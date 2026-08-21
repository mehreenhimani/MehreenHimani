# =====================================================================================
# Compute — where agents run.
#
# Azure Container Apps rather than AKS. The tradeoff is deliberate: a platform team of
# a handful of people should be maintaining golden paths, not a Kubernetes control
# plane. Container Apps gives revisions, traffic splitting, KEDA autoscaling, managed
# identity and scale-to-zero out of the box, and the exit to AKS stays open because
# the unit of deployment is a plain OCI image.
#
# The module is generic on purpose: `var.agents` is a map, so onboarding the second
# and tenth agent team is a few lines of configuration rather than a new pipeline.
# That is the difference between a platform and a bespoke deployment.
# =====================================================================================

terraform {
  required_version = ">= 1.9.0"
  required_providers {
    azurerm = { source = "hashicorp/azurerm", version = "~> 4.14" }
  }
}

resource "azurerm_container_app" "agents" {
  for_each = var.agents

  name                         = "ca-${each.key}"
  container_app_environment_id = var.container_app_environment_id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Multiple" # both revisions live during a canary
  tags                         = merge(var.tags, { agent = each.key, tenant = each.value.tenant })

  identity {
    type         = "UserAssigned"
    identity_ids = [var.agent_identity_id]
  }

  registry {
    server   = var.container_registry_login_server
    identity = var.agent_identity_id
  }

  dynamic "secret" {
    for_each = each.value.key_vault_secret_uris
    content {
      name                = secret.key
      key_vault_secret_id = secret.value
      identity            = var.agent_identity_id
    }
  }

  ingress {
    external_enabled = each.value.external
    target_port      = 8080
    transport        = "auto"

    # Traffic split is how a release becomes gradual. CD sets 10/90, watches the
    # SLOs and the eval score on the canary, then promotes or rolls back. A rollback
    # is a weight change — seconds, not a rebuild.
    traffic_weight {
      latest_revision = true
      percentage      = each.value.canary_percentage
    }

    dynamic "traffic_weight" {
      for_each = each.value.canary_percentage < 100 ? [1] : []
      content {
        revision_suffix = each.value.stable_revision_suffix
        percentage      = 100 - each.value.canary_percentage
      }
    }
  }

  template {
    min_replicas = each.value.min_replicas
    max_replicas = each.value.max_replicas

    container {
      name   = each.key
      image  = "${var.container_registry_login_server}/${each.key}:${each.value.image_tag}"
      cpu    = each.value.cpu
      memory = each.value.memory

      env {
        name  = "SERVICE_NAME"
        value = each.key
      }
      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }
      env {
        name  = "TENANT_ID"
        value = each.value.tenant
      }
      env {
        name  = "COST_CENTRE"
        value = each.value.cost_centre
      }
      env {
        name  = "LLM_MODE"
        value = "litellm"
      }
      # The agent knows one URL. It cannot reach a provider directly even if it tried:
      # egress to the internet is denied by the NSG and it holds no provider key.
      env {
        name  = "LITELLM_BASE_URL"
        value = var.gateway_base_url
      }
      env {
        name  = "OTEL_EXPORTER_OTLP_ENDPOINT"
        value = var.otel_endpoint
      }
      env {
        name        = "APPLICATIONINSIGHTS_CONNECTION_STRING"
        secret_name = "app-insights-connection-string"
      }
      env {
        name  = "AZURE_CLIENT_ID"
        value = var.agent_client_id
      }
      env {
        name  = "BUDGET_TENANT_DAILY_USD"
        value = tostring(each.value.daily_budget_usd)
      }
      env {
        name  = "GUARDRAILS_ENABLED"
        value = "true"
      }
      env {
        name  = "HITL_ENABLED"
        value = tostring(each.value.hitl_enabled)
      }
      env {
        name  = "EU_AI_ACT_RISK_TIER"
        value = each.value.eu_ai_act_risk_tier
      }

      dynamic "env" {
        for_each = each.value.key_vault_secret_uris
        content {
          name        = upper(replace(env.key, "-", "_"))
          secret_name = env.key
        }
      }

      liveness_probe {
        transport               = "HTTP"
        port                    = 8080
        path                    = "/healthz"
        initial_delay           = 10
        interval_seconds        = 30
        failure_count_threshold = 3
      }

      readiness_probe {
        transport               = "HTTP"
        port                    = 8080
        path                    = "/readyz"
        interval_seconds        = 10
        failure_count_threshold = 3
      }

      startup_probe {
        transport               = "HTTP"
        port                    = 8080
        path                    = "/healthz"
        interval_seconds        = 5
        failure_count_threshold = 12
      }
    }

    http_scale_rule {
      name                = "http-concurrency"
      concurrent_requests = each.value.concurrent_requests_per_replica
    }

    # Queue-depth scaling for the async/batch path — agent work that arrives in
    # bursts should add replicas, not latency.
    dynamic "custom_scale_rule" {
      for_each = each.value.queue_name == null ? [] : [1]
      content {
        name             = "queue-depth"
        custom_rule_type = "azure-servicebus"
        metadata = {
          queueName    = each.value.queue_name
          messageCount = "20"
          namespace    = var.service_bus_namespace
        }
        identity = var.agent_identity_id
      }
    }
  }

  lifecycle { ignore_changes = [template[0].container[0].image, ingress[0].traffic_weight] }
}
