# Terraform

Infrastructure-as-code for Railway, Cloudflare, Supabase project config, and secret wiring.

## Layout

- `railway/` — service + environment stubs (Railway primarily managed via dashboard/API; TF provider is limited)
- `cloudflare/` — DNS + WAF rules for custom domain
- `supabase/` — project notes / remote state pointers
- `secrets/` — mapping of required GitHub Actions secrets

## Usage

```bash
cd terraform/cloudflare
terraform init
terraform plan
terraform apply
```

Railway deploys are driven by GitHub Actions (`serviceInstanceDeployV2`) rather than pure Terraform in this scaffold.
