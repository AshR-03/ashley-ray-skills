# Ashley Ray Skills

A library of [Agent Skills](https://agentskills.io) for building software with AI agents, following an agile software development lifecycle.

Each skill is a self-contained folder with a `SKILL.md` file: instructions, scripts and references that an agent loads only when the task calls for it. Skills work with Claude Code, Claude.ai and other agents that support the Agent Skills format.

## Planned skills

| Area | Skills |
| --- | --- |
| **Software development lifecycle** | Business analyst, solution architect, developer, QA engineer, sprint planning, release and retrospective |
| **Engineering standards** | Project setup, code review, policies and definition of done, delivery metrics |
| **Frontier practices** | Chief of staff (coordinates the roles across a sprint), Lean proof verification (proves code correct) |

The lifecycle skills are designed to hand work to each other: the analyst writes user stories with acceptance criteria, the architect records design decisions, the developer builds against the acceptance criteria, and QA verifies against the same criteria.

## Repository layout

```
skills/<skill-name>/
├── SKILL.md        # required: frontmatter (name, description) + instructions
├── scripts/        # optional: code the agent runs
├── references/     # optional: docs the agent reads when needed
└── assets/         # optional: templates and files used in output
template/SKILL.md   # starting point for a new skill
```

## Using a skill

- **Claude Code:** copy a skill folder into `~/.claude/skills/` (personal) or `.claude/skills/` (per project).
- **Claude.ai:** zip the skill folder and upload it under Settings → Capabilities → Skills.

## Creating a skill

Copy `template/` to `skills/<skill-name>/`, fill in the frontmatter and instructions, and keep `SKILL.md` focused, with detail moved into `references/`.

## License

[MIT](LICENSE)
