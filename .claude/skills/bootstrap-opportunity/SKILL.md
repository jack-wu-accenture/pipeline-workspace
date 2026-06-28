---
name: bootstrap-opportunity
description: Initialize a new opportunity workspace under opportunities/{opportunity_id}/ with the full input/okf/output folder structure. Use when starting work on a new Salesforce opportunity in Opportunity OS.
---

# bootstrap-opportunity

Args: `<opportunity_id> <opportunity_name>`

1. Run `scripts/create_opportunity.sh <opportunity_id> "<opportunity_name>"` from the repo root.
2. The script creates:
   ```
   opportunities/{opportunity_id}/
     input/{meetings,rfp,notes,references}/
     okf/{context,requirements,decisions,actions,solution,_graph}/
     output/{proposal,reasoning,salesforce}/
   ```
   plus a `meta.yaml` with `id`, `name`, `created_at`.
3. If the opportunity folder already exists, do NOT overwrite — report the existing path and stop.
4. After creation, tell the user the path and the next step (`/ingest-input`).

Do not create any OKF nodes here — this skill only scaffolds folders.
