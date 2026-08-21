# =====================================================================================
# Shared runtime — the Container Apps environment and the image registry.
#
# This module exists to break a dependency cycle, and the cycle is worth explaining
# because it is a real design signal: the gateway needs a registry to pull its image
# from, and the agents need the gateway's URL to call. If the registry lives in the
# agent module and the environment lives in the gateway module, the two modules
# depend on each other and Terraform refuses to build a graph.
#
# The fix is not a workaround, it is the correct decomposition: the compute *fabric*
# (where containers run, where images come from) is shared infrastructure that both
# the gateway and every agent sit on top of. Ownership follows the same line — the
# platform team owns this module, tenant teams never touch it.
#
#   runtime  ──►  gateway  ──►  compute (agents)
#      └──────────────────────────┘
# =====================================================================================

terraform {
  required_version = ">= 1.9.0"
  required_providers {
    azurerm = { source = "hashicorp/azurerm", version = "~> 4.14" }
  }
}

resource "azurerm_container_app_environment" "main" {
  name                       = "cae-${var.name_prefix}"
  location                   = var.location
  resource_group_name        = var.resource_group_name
  log_analytics_workspace_id = var.log_analytics_workspace_id

  infrastructure_subnet_id       = var.apps_subnet_id
  internal_load_balancer_enabled = var.internal_only
  zone_redundancy_enabled        = var.zone_redundant

  workload_profile {
    name                  = "Consumption"
    workload_profile_type = "Consumption"
  }

  tags = var.tags
}

resource "azurerm_container_registry" "main" {
  name                = "acr${substr(replace(var.name_prefix, "-", ""), 0, 20)}"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = var.acr_sku

  admin_enabled                 = false # identity-based pulls only, no shared admin password
  public_network_access_enabled = var.acr_public_access
  anonymous_pull_enabled        = false
  data_endpoint_enabled         = var.acr_sku == "Premium"

  dynamic "retention_policy_in_days" {
    for_each = var.acr_sku == "Premium" ? [1] : []
    content {
      days    = 30
      enabled = true
    }
  }

  # Content trust: with cosign signing in CI and this enabled, an unsigned image
  # cannot be promoted. It is the supply-chain control that still holds at 5pm on a
  # Friday, when a convention would not.
  dynamic "trust_policy" {
    for_each = var.acr_sku == "Premium" ? [1] : []
    content { enabled = true }
  }

  identity { type = "SystemAssigned" }
  tags = var.tags
}

# The config share the gateway mounts its config.yaml from. Mounting rather than
# baking means a routing or budget change ships as a PR plus a revision restart,
# with no image rebuild in the path.
resource "azurerm_container_app_environment_storage" "gateway_config" {
  name                         = "gateway-config"
  container_app_environment_id = azurerm_container_app_environment.main.id
  account_name                 = var.config_storage_account_name
  share_name                   = var.config_file_share_name
  access_key                   = var.config_storage_access_key
  access_mode                  = "ReadOnly"
}
