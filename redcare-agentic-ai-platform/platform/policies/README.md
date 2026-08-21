# Policy as code

Rego policies evaluated by Conftest against the **Terraform plan JSON**, not against
the source. That distinction matters: HCL can look compliant while a `for_each`, a
variable default or a module input turns it into a public storage account. The plan
is what will actually exist.

Two namespaces:

* `terraform.plan` — runs in `terraform-plan.yml` on every infrastructure PR
* `main` — runs in `ci.yml` over the source tree as a fast pre-check

## Why these rules and not a stock pack

Checkov and tfsec already cover the generic CIS-style findings, and they run too.
These policies encode the things no off-the-shelf pack knows about Redcare:

| Rule | Why it exists |
|---|---|
| EU-only regions | Health data under GDPR Art. 9 must not leave the EU. A region typo is a reportable breach, not a lint warning. |
| No public network access on data services | The blast radius of a leaked key should be "nothing, it is not reachable". |
| Gateway never scales to zero | A cold gateway is a company-wide AI outage, and the failure mode is a timeout, which looks like a bug for twenty minutes. |
| Managed identity only | The moment one password exists, it gets copied into a runbook. |
| Purge protection on Key Vault | Recoverability after a mistake or an attack. |
| Cost-centre and data-classification tags | Untagged spend is unattributable spend, and unclassified data cannot be governed. |
| RAI policy on every model deployment | A deployment without a content filter is a deployment nobody reviewed. |

## Running them locally

```bash
terraform -chdir=infra/terraform/envs/dev plan -out=tfplan
terraform -chdir=infra/terraform/envs/dev show -json tfplan > plan.json
conftest test plan.json --policy platform/policies --namespace terraform.plan
```

A failure prints the resource address and the rule, so the fix is obvious without
reading the Rego.
