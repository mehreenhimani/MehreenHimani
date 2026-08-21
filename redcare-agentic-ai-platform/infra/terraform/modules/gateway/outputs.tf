output "gateway_fqdn" { value = azurerm_container_app.litellm.ingress[0].fqdn }
output "gateway_base_url" { value = "https://${azurerm_container_app.litellm.ingress[0].fqdn}" }
output "gateway_app_id" { value = azurerm_container_app.litellm.id }
