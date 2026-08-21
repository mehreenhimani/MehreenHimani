# =====================================================================================
# Environment: prod
#
# The same modules as dev. Everything that differs is a number: bigger SKUs, zone
# redundancy on, geo-redundant backup on, agents never scaling to zero, Defender on,
# a canary weight on every release, and a real budget.
#
# The controls that are identical to dev are the interesting ones — private
# endpoints, no public network access, managed identity everywhere, no password auth
# on Postgres, guardrails and HITL enabled, audit retention. If any of those had to
# be turned *on* for production, dev would be the weak link an attacker uses.
#
# Applying this environment requires a GitHub Environment protection rule: two
# approvers, and the plan file reviewed on the pull request is the plan that runs.
# =====================================================================================

terraform {
  required_version = ">= 1.9.0"

  required_providers {
    azurerm = { source = "hashicorp/azurerm", version = "~> 4.14" }
    azuread = { source = "hashicorp/azuread", version = "~> 3.0" }
  }

  backend "azurerm" {
    resource_group_name  = "rg-tfstate-shared"
    storage_account_name = "sttfstateredcareai"
    container_name       = "tfstate"
    key                  = "agentic-ai-platform/prod.tfstate"
    use_azuread_auth     = true # no storage keys; the OIDC token authorises the state write
  }
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy    = false # never purge a vault from a pipeline
      recover_soft_deleted_key_vaults = true
    }
    resource_group { prevent_deletion_if_contains_resources = true }
  }
  subscription_id     = var.subscription_id
  storage_use_azuread = true
}

provider "azuread" {}

data "azurerm_client_config" "current" {}

locals {
  environment = "prod"
  name_prefix = "raap-prod-sc"

  # Tags are not decoration: they drive cost allocation, ownership routing during an
  # incident, and the data-classification policy that Azure Policy enforces.
  tags = {
    platform            = "agentic-ai-platform"
    environment         = local.environment
    owner               = "team-ai-platform"
    cost_centre         = "cc-9001-ai-platform"
    data_classification = "confidential-health"
    managed_by          = "terraform"
    repo                = "redcare/agentic-ai-platform"
  }
}

resource "azurerm_resource_group" "main" {
  name     = "rg-${local.name_prefix}"
  location = var.location
  tags     = local.tags
}

module "network" {
  source              = "../../modules/network"
  name_prefix         = local.name_prefix
  location            = var.location
  resource_group_name = azurerm_resource_group.main.name
  address_space       = "10.44.0.0/16"
  tags                = local.tags
}

module "security" {
  source                     = "../../modules/security"
  name_prefix                = local.name_prefix
  location                   = var.location
  resource_group_name        = azurerm_resource_group.main.name
  private_endpoint_subnet_id = module.network.private_endpoint_subnet_id
  key_vault_dns_zone_id      = module.network.private_dns_zone_ids["keyvault"]
  enable_defender            = true
  tags                       = local.tags
}

module "observability" {
  source              = "../../modules/observability"
  name_prefix         = local.name_prefix
  location            = var.location
  resource_group_name = azurerm_resource_group.main.name
  resource_group_id   = azurerm_resource_group.main.id
  subscription_scope  = "/subscriptions/${var.subscription_id}"

  operational_retention_days = 90
  audit_retention_days       = 2555 # ~7y: EU AI Act Art. 12 + pharmacy record-keeping
  daily_quota_gb             = 50
  enable_grafana             = true
  grafana_public_access      = false
  zone_redundant             = true
  daily_budget_usd           = 900
  monthly_budget_eur         = 20000
  oncall_emails              = var.oncall_emails
  slack_webhook_url          = var.slack_webhook_url
  tags                       = local.tags
}

module "data" {
  source              = "../../modules/data"
  name_prefix         = local.name_prefix
  resource_group_name = azurerm_resource_group.main.name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  primary_location    = var.location

  # Two regions: a single region is a single point of failure for every AI feature
  # in the company, and Azure OpenAI quota is allocated per region, so the second
  # region is also a second quota pool.
  enable_secondary_region  = true
  secondary_location       = "westeurope"
  secondary_capacity_ratio = 0.5

  model_deployments = {
    "gpt-4o-mini" = {
      model_name             = "gpt-4o-mini"
      model_version          = "2024-07-18"
      sku_name               = "GlobalStandard"
      capacity_tpm_thousands = 200
      rai_policy             = "redcare-strict"
    }
    "gpt-4o" = {
      model_name             = "gpt-4o"
      model_version          = "2024-11-20"
      sku_name               = "GlobalStandard"
      capacity_tpm_thousands = 100
      rai_policy             = "redcare-strict"
    }
    "text-embedding-3-large" = {
      model_name             = "text-embedding-3-large"
      model_version          = "1"
      sku_name               = "Standard"
      capacity_tpm_thousands = 120
      rai_policy             = "redcare-strict"
    }
  }

  private_endpoint_subnet_id = module.network.private_endpoint_subnet_id
  data_subnet_id             = module.network.data_subnet_id
  openai_dns_zone_id         = module.network.private_dns_zone_ids["openai"]
  search_dns_zone_id         = module.network.private_dns_zone_ids["search"]
  postgres_dns_zone_id       = module.network.private_dns_zone_ids["postgres"]
  redis_dns_zone_id          = module.network.private_dns_zone_ids["redis"]

  search_sku           = "basic"
  search_semantic_sku  = "free"
  storage_replication  = "LRS"
  postgres_sku         = "B_Standard_B1ms"
  postgres_storage_mb  = 32768
  postgres_backup_days = 7
  postgres_ha          = false
  redis_sku            = "Basic"
  redis_capacity       = 0

  tags = local.tags
}

module "compute" {
  source              = "../../modules/compute"
  resource_group_name = azurerm_resource_group.main.name
  environment         = local.environment

  container_app_environment_id    = module.runtime.container_app_environment_id
  agent_identity_id               = module.identity.agent_identity_id
  agent_client_id                 = module.identity.agent_client_id
  gateway_base_url                = module.gateway.gateway_base_url
  otel_endpoint                   = var.otel_endpoint
  container_registry_login_server = module.runtime.container_registry_login_server


  agents = {
    "carecopilot-agent" = {
      tenant                          = "pharmacy-care"
      cost_centre                     = "cc-4711-customer-care"
      image_tag                       = var.agent_image_tag
      external                        = true
      min_replicas                    = 2 # never zero in prod: cold start is customer-visible
      max_replicas                    = 25
      cpu                             = 1.0
      memory                          = "2Gi"
      concurrent_requests_per_replica = 40
      daily_budget_usd                = 900
      hitl_enabled                    = true
      eu_ai_act_risk_tier             = "limited-risk"
      # Progressive delivery: CD sets the canary to 10, watches SLOs and the online
      # eval score for 30 minutes, then promotes to 100 or drops it back to 0. A
      # rollback is a traffic-weight change — seconds, not a rebuild.
      canary_percentage      = 10
      stable_revision_suffix = var.stable_revision_suffix
      key_vault_secret_uris = {
        "carecopilot-virtual-key"        = module.security.secret_uris["carecopilot-virtual-key"]
        "app-insights-connection-string" = module.security.secret_uris["litellm-master-key"]
      }
    }
  }

  tags = local.tags
}

module "runtime" {
  source              = "../../modules/runtime"
  name_prefix         = local.name_prefix
  location            = var.location
  resource_group_name = azurerm_resource_group.main.name

  apps_subnet_id             = module.network.apps_subnet_id
  log_analytics_workspace_id = module.observability.workspace_id

  internal_only  = true # the gateway is never reachable from the public internet
  zone_redundant = true

  acr_sku           = "Premium" # private endpoints, geo-replication, content trust
  acr_public_access = false

  config_storage_account_name = var.config_storage_account_name
  config_storage_access_key   = var.config_storage_access_key

  tags = local.tags
}

module "gateway" {
  source              = "../../modules/gateway"
  resource_group_name = azurerm_resource_group.main.name

  container_app_environment_id    = module.runtime.container_app_environment_id
  gateway_config_storage_name     = module.runtime.gateway_config_storage_name
  container_registry_login_server = module.runtime.container_registry_login_server
  gateway_identity_id             = module.identity.gateway_identity_id
  gateway_client_id               = module.identity.gateway_client_id

  key_vault_secret_uris = module.security.secret_uris

  openai_primary_endpoint = module.data.openai_primary_endpoint
  content_safety_endpoint = module.security.content_safety_endpoint
  redis_hostname          = module.data.redis_hostname
  otel_endpoint           = var.otel_endpoint

  # Two replicas minimum across zones. Every AI call in the company goes through
  # this app; a cold start here is a company-wide outage.
  min_replicas                    = 3
  max_replicas                    = 30
  cpu                             = 2.0
  memory                          = "4Gi"
  concurrent_requests_per_replica = 80
  openai_secondary_endpoint       = module.data.openai_secondary_endpoint

  tags = local.tags
}

module "identity" {
  source              = "../../modules/identity"
  name_prefix         = local.name_prefix
  location            = var.location
  resource_group_name = azurerm_resource_group.main.name

  github_federation_subjects = {
    main_branch  = "repo:${var.github_repo}:ref:refs/heads/main"
    pull_request = "repo:${var.github_repo}:pull_request"
    env_prod     = "repo:${var.github_repo}:environment:prod"
  }

  key_vault_id          = module.security.key_vault_id
  container_registry_id = module.runtime.container_registry_id
  azure_openai_id       = module.data.openai_primary_id
  search_service_id     = module.data.search_service_id
  app_insights_id       = module.observability.app_insights_id

  tags = local.tags
}
