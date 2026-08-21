# =====================================================================================
# Environment: dev
#
# Same modules as production, different variables. That sentence is the entire point
# of the layout: if dev and prod were different code, "it worked in dev" would mean
# nothing. What differs here is size and cost — smaller SKUs, no zone redundancy, no
# geo-backup, scale-to-zero on the agents, Defender off.
#
# What does NOT differ, ever: private networking, managed identity, no public access
# on data stores, guardrails on, audit logging on. Security posture is not an
# environment variable, because dev is where a real customer record eventually gets
# pasted into a test.
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
    key                  = "agentic-ai-platform/dev.tfstate"
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
  environment = "dev"
  name_prefix = "raap-dev-sc"

  # Tags are not decoration: they drive cost allocation, ownership routing during an
  # incident, and the data-classification policy that Azure Policy enforces.
  tags = {
    platform            = "agentic-ai-platform"
    environment         = local.environment
    owner               = "team-ai-platform"
    cost_centre         = "cc-9001-ai-platform"
    data_classification = "internal"
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
  address_space       = "10.42.0.0/16"
  tags                = local.tags
}

module "security" {
  source                     = "../../modules/security"
  name_prefix                = local.name_prefix
  location                   = var.location
  resource_group_name        = azurerm_resource_group.main.name
  private_endpoint_subnet_id = module.network.private_endpoint_subnet_id
  key_vault_dns_zone_id      = module.network.private_dns_zone_ids["keyvault"]
  enable_defender            = false # dev pays for itself in learning, not in Defender plans
  tags                       = local.tags
}

module "observability" {
  source              = "../../modules/observability"
  name_prefix         = local.name_prefix
  location            = var.location
  resource_group_name = azurerm_resource_group.main.name
  resource_group_id   = azurerm_resource_group.main.id
  subscription_scope  = "/subscriptions/${var.subscription_id}"

  operational_retention_days = 30
  audit_retention_days       = 365
  daily_quota_gb             = 2
  enable_grafana             = true
  grafana_public_access      = true # dev only; prod is private
  zone_redundant             = false
  daily_budget_usd           = 25
  monthly_budget_eur         = 750
  oncall_emails              = var.oncall_emails
  tags                       = local.tags
}

module "data" {
  source              = "../../modules/data"
  name_prefix         = local.name_prefix
  resource_group_name = azurerm_resource_group.main.name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  primary_location    = var.location

  enable_secondary_region = false # one region is enough to develop against

  model_deployments = {
    "gpt-4o-mini" = {
      model_name             = "gpt-4o-mini"
      model_version          = "2024-07-18"
      sku_name               = "GlobalStandard"
      capacity_tpm_thousands = 30
      rai_policy             = "redcare-strict"
    }
    "gpt-4o" = {
      model_name             = "gpt-4o"
      model_version          = "2024-11-20"
      sku_name               = "GlobalStandard"
      capacity_tpm_thousands = 20
      rai_policy             = "redcare-strict"
    }
    "text-embedding-3-large" = {
      model_name             = "text-embedding-3-large"
      model_version          = "1"
      sku_name               = "Standard"
      capacity_tpm_thousands = 30
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
      min_replicas                    = 0 # dev scales to zero — nights and weekends are free
      max_replicas                    = 3
      cpu                             = 0.5
      memory                          = "1Gi"
      concurrent_requests_per_replica = 20
      daily_budget_usd                = 25
      hitl_enabled                    = true
      eu_ai_act_risk_tier             = "limited-risk"
      canary_percentage               = 100 # no canary in dev; latest is the point
      stable_revision_suffix          = ""
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

  internal_only  = false # dev exposes the gateway UI to the corporate VPN range
  zone_redundant = false

  acr_sku           = "Standard"
  acr_public_access = true # dev pulls from a laptop sometimes; prod never does

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

  min_replicas = 1
  max_replicas = 3
  cpu          = 0.5
  memory       = "1Gi"

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
    env_dev      = "repo:${var.github_repo}:environment:dev"
  }

  key_vault_id          = module.security.key_vault_id
  container_registry_id = module.runtime.container_registry_id
  azure_openai_id       = module.data.openai_primary_id
  search_service_id     = module.data.search_service_id
  app_insights_id       = module.observability.app_insights_id

  tags = local.tags
}
