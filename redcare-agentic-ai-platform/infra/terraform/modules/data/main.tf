# =====================================================================================
# Data & AI plane — the model deployments and the knowledge index.
#
# Two Azure OpenAI accounts in two EU regions. That is not gold-plating: a single
# region is a single point of failure for the entire AI surface of the company, and
# quota is allocated per region, so a second region is also a second quota pool.
#
# Deployment capacity is expressed in TPM. Provisioning it in Terraform means a
# capacity increase is a reviewed pull request with a cost consequence attached,
# rather than a slider someone moved on a Friday afternoon.
# =====================================================================================

terraform {
  required_version = ">= 1.9.0"
  required_providers {
    azurerm = { source = "hashicorp/azurerm", version = "~> 4.14" }
  }
}

# --- Azure OpenAI, primary region ---------------------------------------------------------
resource "azurerm_cognitive_account" "openai_primary" {
  name                          = "aoai-${var.name_prefix}-primary"
  location                      = var.primary_location
  resource_group_name           = var.resource_group_name
  kind                          = "OpenAI"
  sku_name                      = "S0"
  custom_subdomain_name         = "aoai-${var.name_prefix}-primary"
  public_network_access_enabled = false
  local_auth_enabled            = false # force Entra ID auth; no key to leak
  tags                          = var.tags

  identity { type = "SystemAssigned" }

  # Every prompt and completion is customer health data. Opting out of abuse-
  # monitoring retention is what keeps that data from being stored for human review;
  # it requires a Microsoft-approved application and is a documented control.
  dynamic "customer_managed_key" {
    for_each = var.cmk_key_vault_key_id == null ? [] : [1]
    content {
      key_vault_key_id   = var.cmk_key_vault_key_id
      identity_client_id = var.cmk_identity_client_id
    }
  }
}

resource "azurerm_cognitive_deployment" "primary" {
  for_each = var.model_deployments

  name                 = each.key
  cognitive_account_id = azurerm_cognitive_account.openai_primary.id

  model {
    format  = "OpenAI"
    name    = each.value.model_name
    version = each.value.model_version
  }

  sku {
    name     = each.value.sku_name
    capacity = each.value.capacity_tpm_thousands
  }

  # Provider-side content filter. The gateway adds its own; defence in depth means a
  # bypass of one layer is not a bypass of the control.
  rai_policy_name = each.value.rai_policy
}

# --- Azure OpenAI, failover region ----------------------------------------------------------
resource "azurerm_cognitive_account" "openai_secondary" {
  count = var.enable_secondary_region ? 1 : 0

  name                          = "aoai-${var.name_prefix}-secondary"
  location                      = var.secondary_location
  resource_group_name           = var.resource_group_name
  kind                          = "OpenAI"
  sku_name                      = "S0"
  custom_subdomain_name         = "aoai-${var.name_prefix}-secondary"
  public_network_access_enabled = false
  local_auth_enabled            = false
  tags                          = var.tags

  identity { type = "SystemAssigned" }
}

resource "azurerm_cognitive_deployment" "secondary" {
  for_each = var.enable_secondary_region ? var.model_deployments : {}

  name                 = each.key
  cognitive_account_id = azurerm_cognitive_account.openai_secondary[0].id

  model {
    format  = "OpenAI"
    name    = each.value.model_name
    version = each.value.model_version
  }

  sku {
    name = each.value.sku_name
    # Failover capacity is deliberately smaller: it absorbs an outage at degraded
    # throughput rather than doubling the standing bill.
    capacity = max(1, floor(each.value.capacity_tpm_thousands * var.secondary_capacity_ratio))
  }

  rai_policy_name = each.value.rai_policy
}

resource "azurerm_private_endpoint" "openai_primary" {
  name                = "pe-${var.name_prefix}-aoai-primary"
  location            = var.primary_location
  resource_group_name = var.resource_group_name
  subnet_id           = var.private_endpoint_subnet_id
  tags                = var.tags

  private_service_connection {
    name                           = "psc-aoai-primary"
    private_connection_resource_id = azurerm_cognitive_account.openai_primary.id
    subresource_names              = ["account"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "aoai-dns"
    private_dns_zone_ids = [var.openai_dns_zone_id]
  }
}

# --- Azure AI Search: the policy / knowledge index --------------------------------------------
resource "azurerm_search_service" "main" {
  name                = "srch-${var.name_prefix}"
  location            = var.primary_location
  resource_group_name = var.resource_group_name
  sku                 = var.search_sku

  replica_count   = var.search_replicas # replicas buy query throughput and availability
  partition_count = var.search_partitions

  public_network_access_enabled = false
  local_authentication_enabled  = false
  authentication_failure_mode   = null

  # Semantic ranker turns keyword retrieval into hybrid retrieval. In RAG the
  # retrieval step, not the model, is usually what is wrong with a bad answer.
  semantic_search_sku = var.search_semantic_sku

  identity { type = "SystemAssigned" }
  tags = var.tags
}

resource "azurerm_private_endpoint" "search" {
  name                = "pe-${var.name_prefix}-search"
  location            = var.primary_location
  resource_group_name = var.resource_group_name
  subnet_id           = var.private_endpoint_subnet_id
  tags                = var.tags

  private_service_connection {
    name                           = "psc-search"
    private_connection_resource_id = azurerm_search_service.main.id
    subresource_names              = ["searchService"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "search-dns"
    private_dns_zone_ids = [var.search_dns_zone_id]
  }
}

# --- Storage: source documents, eval datasets, exported traces ------------------------------------
resource "azurerm_storage_account" "data" {
  name                = "st${substr(replace(var.name_prefix, "-", ""), 0, 20)}"
  location            = var.primary_location
  resource_group_name = var.resource_group_name

  account_tier             = "Standard"
  account_replication_type = var.storage_replication
  account_kind             = "StorageV2"

  https_traffic_only_enabled      = true
  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false
  shared_access_key_enabled       = false # Entra ID only
  public_network_access_enabled   = false

  blob_properties {
    versioning_enabled = true
    delete_retention_policy { days = 30 }
    container_delete_retention_policy { days = 30 }
  }

  network_rules {
    default_action = "Deny"
    bypass         = ["AzureServices"]
  }

  tags = var.tags
}

resource "azurerm_storage_container" "containers" {
  for_each = toset(["policy-documents", "eval-datasets", "trace-archive", "prompt-versions"])

  name                  = each.value
  storage_account_id    = azurerm_storage_account.data.id
  container_access_type = "private"
}

# --- PostgreSQL: gateway spend logs, session transcripts, approvals, eval history ------------------
resource "azurerm_postgresql_flexible_server" "main" {
  name                = "psql-${var.name_prefix}"
  location            = var.primary_location
  resource_group_name = var.resource_group_name

  version    = "16"
  sku_name   = var.postgres_sku
  storage_mb = var.postgres_storage_mb

  # Point-in-time restore. The spend log is the financial record of AI usage and the
  # transcript store is evidence in a complaint — neither is something to lose.
  backup_retention_days        = var.postgres_backup_days
  geo_redundant_backup_enabled = var.postgres_geo_backup

  delegated_subnet_id           = var.data_subnet_id
  private_dns_zone_id           = var.postgres_dns_zone_id
  public_network_access_enabled = false

  authentication {
    active_directory_auth_enabled = true
    password_auth_enabled         = false # managed identity only
    tenant_id                     = var.tenant_id
  }

  dynamic "high_availability" {
    for_each = var.postgres_ha ? [1] : []
    content {
      mode                      = "ZoneRedundant"
      standby_availability_zone = "2"
    }
  }

  tags = var.tags

  lifecycle { ignore_changes = [zone, high_availability[0].standby_availability_zone] }
}

# --- Redis: gateway semantic cache + agent session state ---------------------------------------------
resource "azurerm_redis_cache" "main" {
  name                = "redis-${var.name_prefix}"
  location            = var.primary_location
  resource_group_name = var.resource_group_name

  capacity = var.redis_capacity
  family   = var.redis_family
  sku_name = var.redis_sku

  non_ssl_port_enabled          = false
  minimum_tls_version           = "1.2"
  public_network_access_enabled = false

  redis_configuration {
    maxmemory_policy = "allkeys-lru" # a cache should evict, not fill up and fail
  }

  tags = var.tags
}

resource "azurerm_private_endpoint" "redis" {
  name                = "pe-${var.name_prefix}-redis"
  location            = var.primary_location
  resource_group_name = var.resource_group_name
  subnet_id           = var.private_endpoint_subnet_id
  tags                = var.tags

  private_service_connection {
    name                           = "psc-redis"
    private_connection_resource_id = azurerm_redis_cache.main.id
    subresource_names              = ["redisCache"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "redis-dns"
    private_dns_zone_ids = [var.redis_dns_zone_id]
  }
}
