---
name: check_public_status
track: bonus
kind: live_api
provider: Official Statuspage APIs
requires_env: []
inputs: [provider]
outputs: [indicator, description, checked_at, source_url]
side_effect: false
---
# check_public_status

Reads the live public status of GitHub, Cloudflare, or Atlassian from a fixed
official endpoint. The caller cannot supply a URL, which prevents arbitrary
outbound requests. No employee, asset, diagnostic, ticket, or credential data
is sent outside the lab.
