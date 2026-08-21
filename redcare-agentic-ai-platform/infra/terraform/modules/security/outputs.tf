output "key_vault_id" { value = azurerm_key_vault.main.id }
output "key_vault_uri" { value = azurerm_key_vault.main.vault_uri }
output "key_vault_name" { value = azurerm_key_vault.main.name }
output "content_safety_id" { value = azurerm_cognitive_account.content_safety.id }
output "content_safety_endpoint" { value = azurerm_cognitive_account.content_safety.endpoint }
output "secret_uris" {
  value = { for k, s in azurerm_key_vault_secret.slots : k => s.versionless_id }
}
