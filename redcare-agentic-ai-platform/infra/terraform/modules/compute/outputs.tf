output "agent_fqdns" {
  value = { for k, a in azurerm_container_app.agents : k => try(a.ingress[0].fqdn, null) }
}
output "agent_names" { value = keys(var.agents) }
output "agent_app_ids" {
  value = { for k, a in azurerm_container_app.agents : k => a.id }
}
