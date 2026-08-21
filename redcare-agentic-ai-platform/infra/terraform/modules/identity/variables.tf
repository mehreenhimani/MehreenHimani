variable "name_prefix" { type = string }
variable "location" { type = string }
variable "resource_group_name" { type = string }

variable "github_federation_subjects" {
  type        = map(string)
  description = <<-DESC
    Exact OIDC subjects allowed to assume the deploy identity. Use the environment
    form for anything that can apply, so a protection rule stands between a merge and
    a production change:
      main-branch = "repo:redcare/agentic-ai-platform:ref:refs/heads/main"
      env-prod    = "repo:redcare/agentic-ai-platform:environment:prod"
      pull-plan   = "repo:redcare/agentic-ai-platform:pull_request"
  DESC
}

variable "owner_object_ids" {
  type    = list(string)
  default = []
}

variable "key_vault_id" { type = string }
variable "container_registry_id" { type = string }
variable "azure_openai_id" { type = string }
variable "search_service_id" {
  type    = string
  default = null
}
variable "app_insights_id" {
  type    = string
  default = null
}
variable "tags" { type = map(string) }
