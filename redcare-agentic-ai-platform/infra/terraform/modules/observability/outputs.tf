output "workspace_id" { value = azurerm_log_analytics_workspace.main.id }
output "workspace_customer_id" { value = azurerm_log_analytics_workspace.main.workspace_id }
output "app_insights_id" { value = azurerm_application_insights.main.id }
output "app_insights_connection_string" {
  value     = azurerm_application_insights.main.connection_string
  sensitive = true
}
output "grafana_endpoint" {
  value = var.enable_grafana ? azurerm_dashboard_grafana.main[0].endpoint : null
}
output "action_group_id" { value = azurerm_monitor_action_group.oncall.id }
output "alert_names" { value = keys(local.scheduled_alerts) }
