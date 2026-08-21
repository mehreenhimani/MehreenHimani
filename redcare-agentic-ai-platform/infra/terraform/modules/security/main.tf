# =====================================================================================
# Security — where secrets live and how content is filtered.
#
# Key Vault with RBAC (not the legacy access-policy model), purge protection on, and
# no public network access. Secret *values* are never in Terraform: the vault is
# created here, the entries are created empty or by a break-glass operator, and the
# workloads read them at runtime through managed identity. That way a `terraform show`
# or a leaked state file exposes resource ids, not credentials.
# =====================================================================================

terraform {
  required_version = ">= 1.9.0"
  required_providers {
    azurerm = { source = "hashicorp/azurerm", version = "~> 4.14" }
  }
}

data "azurerm_client_config" "current" {}

resource "azurerm_key_vault" "main" {
  name                = "kv-${substr(replace(var.name_prefix, "-", ""), 0, 18)}"
  location            = var.location
  resource_group_name = var.resource_group_name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"

  # RBAC over access policies: one authorisation model across all of Azure, and
  # assignments that show up in the same access reviews as everything else.
  enable_rbac_authorization = true

  # Purge protection makes a deleted vault recoverable for 90 days. It cannot be
  # turned off once on, which is exactly why an auditor asks for it.
  purge_protection_enabled   = true
  soft_delete_retention_days = 90

  public_network_access_enabled = false
  network_acls {
    bypass         = "AzureServices"
    default_action = "Deny"
  }

  tags = var.tags
}

resource "azurerm_private_endpoint" "key_vault" {
  name                = "pe-${var.name_prefix}-kv"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.private_endpoint_subnet_id
  tags                = var.tags

  private_service_connection {
    name                           = "psc-kv"
    private_connection_resource_id = azurerm_key_vault.main.id
    subresource_names              = ["vault"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "kv-dns"
    private_dns_zone_ids = [var.key_vault_dns_zone_id]
  }
}

# Secret *slots*. Terraform declares that the secret must exist and who may read it;
# the value arrives out of band (break-glass operator or a rotation job) and is
# ignored on subsequent plans so a rotation never shows up as drift.
resource "azurerm_key_vault_secret" "slots" {
  for_each = toset(var.secret_names)

  name         = each.value
  value        = "PLACEHOLDER-SET-OUT-OF-BAND"
  key_vault_id = azurerm_key_vault.main.id
  content_type = "text/plain"

  # 90-day rotation. Expiry is not decoration: a secret with no expiry is a secret
  # nobody will ever rotate.
  expiration_date = timeadd(timestamp(), "2160h")

  lifecycle {
    ignore_changes = [value, expiration_date]
  }

  tags = merge(var.tags, { rotation_days = "90" })
}

# --- Azure AI Content Safety ------------------------------------------------------------
# Provider-independent content filtering, called by the gateway on prompt and response.
# Having it as a platform service rather than a provider feature means the filter does
# not change when the model behind the endpoint changes.
resource "azurerm_cognitive_account" "content_safety" {
  name                          = "cs-${var.name_prefix}"
  location                      = var.location
  resource_group_name           = var.resource_group_name
  kind                          = "ContentSafety"
  sku_name                      = "S0"
  custom_subdomain_name         = "cs-${var.name_prefix}"
  public_network_access_enabled = false
  local_auth_enabled            = false # Entra ID only, no shared keys
  tags                          = var.tags

  identity { type = "SystemAssigned" }
}

# --- Defender for Cloud -------------------------------------------------------------------
resource "azurerm_security_center_subscription_pricing" "containers" {
  count         = var.enable_defender ? 1 : 0
  tier          = "Standard"
  resource_type = "Containers"
}

resource "azurerm_security_center_subscription_pricing" "key_vaults" {
  count         = var.enable_defender ? 1 : 0
  tier          = "Standard"
  resource_type = "KeyVaults"
}

resource "azurerm_security_center_subscription_pricing" "ai" {
  count         = var.enable_defender ? 1 : 0
  tier          = "Standard"
  resource_type = "AI"
}
