output "resource_group" { value = azurerm_resource_group.main.name }
output "gateway_base_url" { value = module.gateway.gateway_base_url }
output "agent_fqdns" { value = module.compute.agent_fqdns }
output "container_registry" { value = module.runtime.container_registry_login_server }
output "grafana_endpoint" { value = module.observability.grafana_endpoint }
output "key_vault_name" { value = module.security.key_vault_name }
output "deployer_client_id" {
  value       = module.identity.deployer_client_id
  description = "Set as the AZURE_CLIENT_ID repository variable in GitHub."
}
output "openai_endpoint" { value = module.data.openai_primary_endpoint }
output "search_endpoint" { value = module.data.search_endpoint }
