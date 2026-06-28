# Opportunity OS

AI-native opportunity operating system. Salesforce holds business state, this Git repo holds the knowledge graph (OKF), Claude Code skills do the reasoning. No automation, no background sync — every action is triggered manually via a Claude Code skill.

## Layout

```
opportunities/{opportunity_id}/
  input/
    meetings/
    rfp/
    notes/
    references/
  okf/
    context/
    requirements/
    decisions/
    actions/
    solution/
    _graph/
  output/
    proposal/
    reasoning/
    salesforce/

portfolio/
  graph_index.yaml
  relations.yaml
  insights.md

templates/
  okf_node.md
```

## Skills

| Skill | Purpose |
|---|---|
| `/bootstrap-opportunity <id> <name>` | Create a new opportunity workspace |
| `/ingest-input <id> <file_path> <input_type>` | Convert a raw input file into OKF nodes |
| `/rebuild-okf-graph <id>` | Regenerate `okf/_graph/` from node links (cache only) |
| `/reason-opportunity <id> "<question>"` | Multi-hop reasoning over the OKF graph, writes `output/reasoning.md` |
| `/generate-salesforce-update <id>` | Produce a copy-paste-ready Salesforce update block |

Skills live in `.claude/skills/`. They are manually triggered — there is no event system, no auto-ingestion, no auto-sync to Salesforce.

## OKF Node Format

See `templates/okf_node.md`. Every node has an `id`, `type`, `title`, `status`, `source`, and `links` (derives_from / impacts / supports / blocks).

## Workflow

```
/bootstrap-opportunity SF-001 "AI CRM Transformation"
# drop a file into opportunities/SF-001/input/meetings/meeting_01.md
/ingest-input SF-001 meeting_01.md meeting
/reason-opportunity SF-001 "What are the key risks?"
/generate-salesforce-update SF-001
# copy result into Salesforce manually
```
