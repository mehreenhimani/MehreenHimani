output "agent_identity_id" { value = azurerm_user_assigned_identity.agent.id }
output "agent_client_id" { value = azurerm_user_assigned_identity.agent.client_id }
output "agent_principal_id" { value = azurerm_user_assigned_identity.agent.principal_id }
output "gateway_identity_id" { value = azurerm_user_assigned_identity.gateway.id }
output "gateway_client_id" { value = azurerm_user_assigned_identity.gateway.client_id }
output "gateway_principal_id" { value = azurerm_user_assigned_identity.gateway.principal_id }

output "deployer_client_id" {
  value       = azuread_application.deployer.client_id
  description = "Set as AZURE_CLIENT_ID in GitHub — an id, not a secret."
}
