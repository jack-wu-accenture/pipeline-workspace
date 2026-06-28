---
name: ingest-input
description: Convert a raw input file (meeting notes, RFP, email, etc.) for an opportunity into structured OKF nodes (requirements, decisions, actions, context). Use after a file has been dropped into opportunities/{id}/input/.
---

# ingest-input

Args: `<opportunity_id> <file_path> <input_type>`

`file_path` is relative to `opportunities/{opportunity_id}/input/` (e.g. `meetings/meeting_01.md`). `input_type` is one of `meeting | rfp | note | reference`.

## Process

1. Read `opportunities/{opportunity_id}/input/{file_path}`. If it doesn't exist, stop and report.
2. Read existing nodes in `okf/requirements/`, `okf/decisions/`, `okf/actions/`, `okf/context/` for this opportunity so you don't duplicate IDs or re-derive something already captured. Note the highest existing numeric suffix per type to continue numbering (REQ-001, REQ-002, ...; DEC-001; ACT-001; CTX-001).
3. Extract from the source file:
   - **context** — background facts, stakeholders, constraints that aren't requirements/decisions themselves
   - **requirements** — explicit or implied needs the solution must satisfy
   - **decisions** — choices that have been made (by the customer or the team)
   - **actions** — open follow-ups / next steps with an owner if stated
4. For each extracted item, write a new OKF node file using the format in `templates/okf_node.md`:
   - Path: `okf/{type plural}/{TYPE-PREFIX}-{NNN}.md` (e.g. `okf/requirements/REQ-003.md`)
   - `source` lists the input file path (relative to the opportunity root, e.g. `input/meetings/meeting_01.md`)
   - `links.derives_from` points to the relevant `context/` node if one was created from the same source
   - `status: draft` unless the source explicitly confirms it, then `confirmed`
   - Body: a concise, faithful summary — do not invent details not present in the source
5. If an extracted item clearly relates to or supersedes an existing node (same topic, contradicts a prior decision, etc.), set `links.supports` / `links.blocks` accordingly, and if it supersedes, update the old node's `status: superseded`.
6. Do not modify the input file. Do not touch `_graph/` — that is rebuilt separately via `/rebuild-okf-graph`.
7. Report a short summary: how many nodes of each type were created/updated, with their IDs.
