---
template: true
description: Starting point for Power BI or Fabric projects. Copy as CLAUDE.md or append to existing CLAUDE.md / agents.md.
---

# Power BI / Fabric Project

## Automatic Skills

Always invoke `fabric-cli` skill when:

- Working with Power BI reports, semantic models, or datasets
- Managing Fabric workspaces, lakehouses, notebooks, pipelines
- Running `fab` CLI commands or discussing Fabric APIs
- Answering questions about Power BI or Microsoft Fabric

## Fabric CLI Usage

```bash
fab auth status        # Check authentication
fab ls                 # List workspaces
fab ls "ws.Workspace"  # List items in workspace
fab --help             # Command reference
```

## Common Patterns

- Always use `-f` flag for non-interactive execution
- Quote paths with spaces: `"My Workspace.Workspace"`
- Extract IDs for API calls: `fab get "ws.Workspace" -q "id"`
- Use `-q` for JMESPath queries on output

## Safety

- Never remove/move items without explicit permission
- Verify workspace/item names with `fab ls` or `fab exists` before operations
- Check `fab auth status` before first use each session

## Cross-Workspace Search

Use `scripts/datahub_search.py` for finding items across workspaces:

```bash
python3 scripts/datahub_search.py --type Model --filter "Sales"
python3 scripts/datahub_search.py --list-types
```

## References

Skill includes detailed references for:

- Semantic models, reports, notebooks, lakehouses
- DAX queries, Power BI API, admin operations
- Full command reference at `fab <command> --help`
