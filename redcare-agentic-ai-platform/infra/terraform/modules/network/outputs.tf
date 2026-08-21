output "vnet_id" { value = azurerm_virtual_network.main.id }
output "apps_subnet_id" { value = azurerm_subnet.apps.id }
output "private_endpoint_subnet_id" { value = azurerm_subnet.private_endpoints.id }
output "data_subnet_id" { value = azurerm_subnet.data.id }
output "private_dns_zone_ids" { value = { for k, z in azurerm_private_dns_zone.zones : k => z.id } }
output "private_dns_zone_names" { value = { for k, z in azurerm_private_dns_zone.zones : k => z.name } }
