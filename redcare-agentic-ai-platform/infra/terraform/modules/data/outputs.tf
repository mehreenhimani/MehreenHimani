output "openai_primary_id" { value = azurerm_cognitive_account.openai_primary.id }
output "openai_primary_endpoint" { value = azurerm_cognitive_account.openai_primary.endpoint }
output "openai_secondary_endpoint" {
  value = var.enable_secondary_region ? azurerm_cognitive_account.openai_secondary[0].endpoint : null
}
output "search_service_id" { value = azurerm_search_service.main.id }
output "search_endpoint" { value = "https://${azurerm_search_service.main.name}.search.windows.net" }
output "storage_account_id" { value = azurerm_storage_account.data.id }
output "postgres_fqdn" { value = azurerm_postgresql_flexible_server.main.fqdn }
output "postgres_id" { value = azurerm_postgresql_flexible_server.main.id }
output "redis_hostname" { value = azurerm_redis_cache.main.hostname }
output "redis_id" { value = azurerm_redis_cache.main.id }
output "deployment_names" { value = keys(var.model_deployments) }
