---
name: generate-salesforce-update
description: Generate a copy-paste-ready Salesforce update block (AI summary, risk level, next action, tasks, risks) from an opportunity's current OKF state. Use when the user needs to push the latest knowledge graph state into Salesforce custom fields.
---

# generate-salesforce-update

Args: `<opportunity_id>`

This skill never writes to Salesforce directly — Salesforce sync is manual by design. It only produces text for the user to copy.

## Process

1. Rebuild the graph cache: `python3 scripts/build_graph.py <opportunity_id>` (repo root).
2. Read all nodes under `okf/` for this opportunity, prioritizing nodes with `status: confirmed` and anything updated since the last `output/salesforce/` update (check the most recent file there, if any).
3. Synthesize:
   - **AI Summary** — 2-4 sentences: where the opportunity stands, what's been decided, what's open
   - **AI Risk Level** — `Low | Medium | High`, based on count/severity of open requirements with no solution, blocking decisions, overdue-sounding actions
   - **Next Action** — the single most important open action
   - **Tasks** — bullet list from `okf/actions/` nodes not yet superseded, each with owner if known
   - **Risks** — bullet list of concrete risks found in the graph (unresolved blocks, unanswered requirements, contradictions), not generic boilerplate
4. Write the result to `opportunities/{opportunity_id}/output/salesforce/update-{YYYY-MM-DD}.md` using exactly this shape:
   ```
   AI Summary:
   <text>

   AI Risk Level:
   <Low|Medium|High>

   Next Action:
   <text>

   Tasks:
   - ...

   Risks:
   - ...
   ```
5. Print the full content in the response as well, so the user can copy it immediately without opening the file.
