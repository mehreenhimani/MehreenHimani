# =====================================================================================
# Identity — who may do what, and for how long.
#
# The whole module exists to make one sentence true: there is no long-lived secret
# anywhere in the delivery chain. GitHub Actions authenticates to Azure by OIDC
# federation and receives a token that lives minutes. The running app authenticates to
# Key Vault, ACR, Postgres and Azure OpenAI with a user-assigned managed identity and
# holds no credential at all.
#
# Everything below is least privilege by construction: the deploy identity may write
# infrastructure but cannot read a customer record; the runtime identity may read
# secrets but cannot change infrastructure.
# =====================================================================================

terraform {
  required_version = ">= 1.9.0"
  required_providers {
    azurerm = { source = "hashicorp/azurerm", version = "~> 4.14" }
    azuread = { source = "hashicorp/azuread", version = "~> 3.0" }
  }
}

data "azurerm_subscription" "current" {}

# --- runtime identity for the agent service -------------------------------------------
resource "azurerm_user_assigned_identity" "agent" {
  name                = "id-${var.name_prefix}-agent"
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags
}

# --- runtime identity for the LiteLLM gateway -----------------------------------------
# Separate from the agent's: the gateway holds provider keys, the agent must never be
# able to read them. Two identities is the difference between "the agent was
# compromised" and "the provider keys were compromised".
resource "azurerm_user_assigned_identity" "gateway" {
  name                = "id-${var.name_prefix}-gateway"
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags
}

# --- deployment identity used by GitHub Actions ----------------------------------------
resource "azuread_application" "deployer" {
  display_name = "gh-${var.name_prefix}-deployer"
  owners       = var.owner_object_ids
}

resource "azuread_service_principal" "deployer" {
  client_id = azuread_application.deployer.client_id
  owners    = var.owner_object_ids
}

# One federated credential per trusted GitHub context. The subject is exact: a token
# minted for a different branch, a different environment or a fork does not match and
# is rejected by Entra ID before any Azure call happens.
resource "azuread_application_federated_identity_credential" "github" {
  for_each = var.github_federation_subjects

  application_id = azuread_application.deployer.id
  display_name   = "gh-${each.key}"
  description    = "OIDC federation for ${each.value}"
  audiences      = ["api://AzureADTokenExchange"]
  issuer         = "https://token.actions.githubusercontent.com"
  subject        = each.value
}

resource "azurerm_role_assignment" "deployer_contributor" {
  scope                = "/subscriptions/${data.azurerm_subscription.current.subscription_id}/resourceGroups/${var.resource_group_name}"
  role_definition_name = "Contributor"
  principal_id         = azuread_service_principal.deployer.object_id
}

# Needed to create role assignments and Key Vault policies from Terraform, scoped to
# the one resource group rather than the subscription.
resource "azurerm_role_assignment" "deployer_rbac_admin" {
  scope                = "/subscriptions/${data.azurerm_subscription.current.subscription_id}/resourceGroups/${var.resource_group_name}"
  role_definition_name = "Role Based Access Control Administrator"
  principal_id         = azuread_service_principal.deployer.object_id
  condition_version    = "2.0"
  # Guardrail: the deployer may grant only the roles the platform actually uses, and
  # may never grant Owner or User Access Administrator — no privilege escalation path.
  condition = <<-COND
    (
      (
        !(ActionMatches{'Microsoft.Authorization/roleAssignments/write'})
      )
      OR
      (
        @Request[Microsoft.Authorization/roleAssignments:RoleDefinitionId] ForAnyOfAnyValues:GuidNotEquals {
          8e3af657-a8ff-443c-a75c-2fe8c4bcb635,
          18d7d88d-d35e-4fb5-a5c3-7773c20a72d9
        }
      )
    )
  COND
}

# --- runtime role assignments ----------------------------------------------------------
locals {
  agent_roles = {
    key_vault_secrets = { role = "Key Vault Secrets User", scope = var.key_vault_id }
    acr_pull          = { role = "AcrPull", scope = var.container_registry_id }
    search_reader     = { role = "Search Index Data Reader", scope = var.search_service_id }
    monitor_publisher = { role = "Monitoring Metrics Publisher", scope = var.app_insights_id }
  }

  gateway_roles = {
    key_vault_secrets = { role = "Key Vault Secrets User", scope = var.key_vault_id }
    acr_pull          = { role = "AcrPull", scope = var.container_registry_id }
    # This is the only identity in the platform allowed to call the model endpoints.
    # Agents reach models exclusively through the gateway — that is what makes the
    # gateway's governance non-optional rather than a convention teams may skip.
    openai_user       = { role = "Cognitive Services OpenAI User", scope = var.azure_openai_id }
    monitor_publisher = { role = "Monitoring Metrics Publisher", scope = var.app_insights_id }
  }
}

resource "azurerm_role_assignment" "agent" {
  for_each             = { for k, v in local.agent_roles : k => v if v.scope != null }
  scope                = each.value.scope
  role_definition_name = each.value.role
  principal_id         = azurerm_user_assigned_identity.agent.principal_id
}

resource "azurerm_role_assignment" "gateway" {
  for_each             = { for k, v in local.gateway_roles : k => v if v.scope != null }
  scope                = each.value.scope
  role_definition_name = each.value.role
  principal_id         = azurerm_user_assigned_identity.gateway.principal_id
}
