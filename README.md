# Latch Skills

Skills for building on the [Latch](https://latch.bio) platform using any agent environment that supports the [Claude Agent SDK skill format](https://docs.anthropic.com/en/docs/claude-code/skills) — including Claude Code, Latch Plots, and custom agent setups.

Each skill is a directory containing a `SKILL.md` file with YAML frontmatter (`name`, `description`) and complete API reference documentation that the agent loads on demand.

## Skills

| Skill | Description |
|-------|-------------|
| **latch-data-access** | Browse and select files from Latch Data, Registry tables, and DataFrames. Includes LPath utilities for working with `latch://` paths. |
| **latch-plots-ui** | Render plots, tables, AnnData viewers, IGV browsers, and interactive input widgets in Latch Plots notebooks. |
| **latch-workflows** | Launch and monitor bioinformatics workflows on Latch from agent code — including parameter construction, validation, and output retrieval. |

## Getting started

Clone this repo into your `.claude/skills/` directory (or let your agent environment handle it automatically):

```bash
git clone https://github.com/latchbio/latch-skills.git .claude/skills/latch-skills
```

For monorepos like this one, each subdirectory with a `SKILL.md` is treated as an independent skill. Symlink them individually if your agent expects flat skill directories:

```bash
for dir in .claude/skills/latch-skills/*/; do
  ln -s "$dir" ".claude/skills/$(basename "$dir")"
done
```

## Adding a new skill

Create a directory with a `SKILL.md`:

```markdown
---
name: my-skill
description: >
  When to load this skill.
---

# My Skill

Reference documentation here.
```

## Structure

```
latch-skills/
├── latch-data-access/
│   └── SKILL.md
├── latch-plots-ui/
│   └── SKILL.md
└── latch-workflows/
    └── SKILL.md
```
