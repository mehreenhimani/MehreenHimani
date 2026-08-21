# =====================================================================================
# Observability — how the platform sees itself.
#
# One Log Analytics workspace is the centre of gravity: Container Apps logs, App
# Insights telemetry, Defender alerts and the agent audit table all land in it, which
# is what makes a single KQL query able to answer "show me every turn that escalated
# to a pharmacist last Tuesday, with its cost and its model".
#
# Retention is split deliberately. Operational telemetry is expensive and only useful
# for weeks. The audit table is cheap in the archive tier and legally required for
# years. One retention number for everything would either bankrupt you or breach
# EU AI Act Art. 12.
# =====================================================================================

terraform {
  required_version = ">= 1.9.0"
  required_providers {
    azurerm = { source = "hashicorp/azurerm", version = "~> 4.14" }
  }
}

resource "azurerm_log_analytics_workspace" "main" {
  name                = "log-${var.name_prefix}"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = "PerGB2018"
  retention_in_days   = var.operational_retention_days
  daily_quota_gb      = var.daily_quota_gb # a cap, so a log storm is not a budget event
  tags                = var.tags
}

resource "azurerm_application_insights" "main" {
  name                       = "appi-${var.name_prefix}"
  location                   = var.location
  resource_group_name        = var.resource_group_name
  workspace_id               = azurerm_log_analytics_workspace.main.id
  application_type           = "web"
  sampling_percentage        = var.trace_sampling_percentage
  retention_in_days          = var.operational_retention_days
  internet_ingestion_enabled = false # telemetry arrives over the private endpoint
  tags                       = var.tags
}

# Long-retention audit table. Ingestion goes to the Analytics tier for 30 days so it
# is queryable during an incident, then rolls to the Archive tier for the statutory
# period at roughly a tenth of the cost.
resource "azurerm_log_analytics_workspace_table" "agent_audit" {
  workspace_id            = azurerm_log_analytics_workspace.main.id
  name                    = "AgentAudit_CL"
  retention_in_days       = 30
  total_retention_in_days = var.audit_retention_days
}

# --- Managed Grafana --------------------------------------------------------------------
# Dashboards live in Git as JSON and are provisioned, not hand-drawn. A dashboard
# nobody can recreate is an outage waiting to be worse.
resource "azurerm_dashboard_grafana" "main" {
  count = var.enable_grafana ? 1 : 0

  name                              = "graf-${var.name_prefix}"
  location                          = var.location
  resource_group_name               = var.resource_group_name
  grafana_major_version             = "11"
  api_key_enabled                   = false
  deterministic_outbound_ip_enabled = true
  public_network_access_enabled     = var.grafana_public_access
  zone_redundancy_enabled           = var.zone_redundant

  identity { type = "SystemAssigned" }
  tags = var.tags
}

resource "azurerm_role_assignment" "grafana_monitoring_reader" {
  count                = var.enable_grafana ? 1 : 0
  scope                = var.subscription_scope
  role_definition_name = "Monitoring Reader"
  principal_id         = azurerm_dashboard_grafana.main[0].identity[0].principal_id
}

# --- Alerting ----------------------------------------------------------------------------
resource "azurerm_monitor_action_group" "oncall" {
  name                = "ag-${var.name_prefix}-oncall"
  resource_group_name = var.resource_group_name
  short_name          = "aiplat"
  tags                = var.tags

  dynamic "email_receiver" {
    for_each = var.oncall_emails
    content {
      name                    = "mail-${email_receiver.key}"
      email_address           = email_receiver.value
      use_common_alert_schema = true
    }
  }

  dynamic "webhook_receiver" {
    for_each = var.slack_webhook_url == null ? [] : [1]
    content {
      name                    = "slack"
      service_uri             = var.slack_webhook_url
      use_common_alert_schema = true
    }
  }
}

# Alerts as code. Each one names the SLO it protects, so an alert that fires can be
# traced to a promise that is at risk rather than to a threshold someone once guessed.
locals {
  scheduled_alerts = {
    gateway_error_rate = {
      display     = "AI gateway 5xx rate above 1% (availability SLO)"
      severity    = 1
      frequency   = 5
      window      = 15
      threshold   = 1
      description = "Protects the 99.9% gateway availability SLO. Page-level."
      query       = <<-KQL
        ContainerAppConsoleLogs_CL
        | where ContainerAppName_s == "ca-litellm-gateway"
        | where Log_s has "status_code"
        | extend code = toint(extract("status_code[\"']?[:=]\\s*(\\d{3})", 1, Log_s))
        | summarize errors = countif(code >= 500), total = count()
        | extend pct = 100.0 * errors / max_of(total, 1)
        | project pct
      KQL
    }

    agent_latency_p95 = {
      display     = "Agent turn p95 latency above 4s (latency SLO)"
      severity    = 2
      frequency   = 5
      window      = 30
      threshold   = 4000
      description = "Protects the p95 < 4s turn-latency SLO."
      query       = <<-KQL
        AppRequests
        | where AppRoleName == "carecopilot-agent" and Name == "POST /v1/chat"
        | summarize p95 = percentile(DurationMs, 95)
        | project p95
      KQL
    }

    guardrail_block_spike = {
      display     = "Guardrail blocks spiked — possible prompt-injection campaign"
      severity    = 2
      frequency   = 10
      window      = 60
      threshold   = 25
      description = "A jump in blocked turns is a security signal, not a quality one."
      query       = <<-KQL
        AgentAudit_CL
        | where event_s == "input_blocked"
        | summarize blocks = count()
        | project blocks
      KQL
    }

    ungrounded_answers = {
      display     = "Ungrounded answers above 3% (groundedness SLO)"
      severity    = 2
      frequency   = 15
      window      = 60
      threshold   = 3
      description = "The metric that catches a quality regression before customers do."
      query       = <<-KQL
        AgentAudit_CL
        | where event_s == "turn_completed"
        | summarize ungrounded = countif(grounded_b == false), total = count()
        | extend pct = 100.0 * ungrounded / max_of(total, 1)
        | project pct
      KQL
    }

    spend_burn_rate = {
      display     = "Hourly AI spend on pace to exceed the daily budget"
      severity    = 3
      frequency   = 15
      window      = 60
      threshold   = 1
      description = "Catches a runaway loop or an unplanned rollout within the hour."
      query       = <<-KQL
        AgentAudit_CL
        | where event_s == "turn_completed"
        | summarize hourly = sum(cost_usd_d)
        | extend projected_daily = hourly * 24
        | project ratio = projected_daily / ${var.daily_budget_usd}
      KQL
    }

    eval_gate_regression = {
      display     = "Eval score below threshold on the deployed revision"
      severity    = 2
      frequency   = 60
      window      = 360
      threshold   = 0.95
      description = "Online quality drifting away from what CI approved."
      query       = <<-KQL
        AgentAudit_CL
        | where event_s == "turn_completed"
        | summarize grounded_ratio = todouble(countif(grounded_b == true)) / max_of(count(), 1)
        | project grounded_ratio
      KQL
    }
  }
}

resource "azurerm_monitor_scheduled_query_rules_alert_v2" "alerts" {
  for_each = local.scheduled_alerts

  name                = "alert-${var.name_prefix}-${each.key}"
  location            = var.location
  resource_group_name = var.resource_group_name
  severity            = each.value.severity
  description         = each.value.description
  enabled             = true
  scopes              = [azurerm_log_analytics_workspace.main.id]

  evaluation_frequency = "PT${each.value.frequency}M"
  window_duration      = "PT${each.value.window}M"

  criteria {
    query                   = each.value.query
    time_aggregation_method = "Maximum"
    threshold               = each.value.threshold
    operator                = each.key == "eval_gate_regression" ? "LessThan" : "GreaterThan"

    failing_periods {
      minimum_failing_periods_to_trigger_alert = 1
      number_of_evaluation_periods             = 1
    }
  }

  action { action_groups = [azurerm_monitor_action_group.oncall.id] }
  tags = var.tags
}

# --- Cost management ------------------------------------------------------------------------
# The budget alert is the backstop behind the gateway's own enforcement: the gateway
# stops calls, this tells a human the shape of demand changed.
resource "azurerm_consumption_budget_resource_group" "ai" {
  name              = "budget-${var.name_prefix}"
  resource_group_id = var.resource_group_id

  amount     = var.monthly_budget_eur
  time_grain = "Monthly"

  time_period { start_date = var.budget_start_date }

  dynamic "notification" {
    for_each = { forecast_90 = 90, actual_75 = 75, actual_100 = 100 }
    content {
      enabled        = true
      threshold      = notification.value
      operator       = "GreaterThan"
      threshold_type = startswith(notification.key, "forecast") ? "Forecasted" : "Actual"
      contact_emails = var.oncall_emails
    }
  }
}
