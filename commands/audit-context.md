---
description: Review project context files (CLAUDE.md, agents.md, memory files)
---

Audit the project's context configuration files. Search for and read:

1. `CLAUDE.md` files (root, .claude/, nested directories)
2. `agents.md` or similar agent configuration files
3. `.claude/settings.json` and `.claude/settings.local.json`
4. Any `SKILL.md` files in the project

For each file found, report:

- Location and purpose
- Key instructions or rules defined
- Potential conflicts or redundancies between files
- Missing recommended configurations

Summarize findings in a table showing file path, line count, and primary purpose. Flag any issues or suggestions for improvement.
