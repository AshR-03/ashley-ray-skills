# Ashley Ray Skills

[![CI](https://github.com/AshR-03/ashley-ray-skills/actions/workflows/ci.yml/badge.svg)](https://github.com/AshR-03/ashley-ray-skills/actions/workflows/ci.yml)

A library of [Agent Skills](https://agentskills.io) for building software with AI agents, following an agile software development lifecycle.

Each skill is a self-contained folder with a `SKILL.md` file: instructions, scripts and references that an agent loads only when the task calls for it. Skills work with Claude Code, Claude.ai and other agents that support the Agent Skills format.

## Skills

### Setup

| Skill | What it does | Status |
| --- | --- | --- |
| [brainstorm](skills/brainstorm) | Interviews the product owner with focused questions and builds a connected knowledge graph of the project: purpose, users, vision, goals, features, risks and roadmap. Done when every idea is explored and linked. | Tested |

**Status** shows how far a skill has been checked (see [How skills are checked](#how-skills-are-checked)):

- **Draft:** written, not yet checked.
- **Tested:** has a spec, passes the linter, and its bundled scripts have unit tests.
- **Measured:** also passes its evals and beats running the same prompts without the skill, with results published below.

### Planned

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
├── spec.md         # required: what the skill must do; written first, tested against
├── scripts/        # optional: code the agent runs (Python standard library only)
├── references/     # optional: docs the agent reads when needed
└── assets/         # optional: templates and files used in output
template/           # starting point for a new skill: SKILL.md and spec.md
tools/lint_skills.py              # checks every skill against the rules below
tools/run_evals.sh                # runs the evals on your Claude plan's usage limits
tests/                            # unit tests for bundled scripts and the linter
evals/<skill-name>/               # eval cases: a prompt, graders and optional fixtures
.claude-plugin/marketplace.json   # groups skills into installable sets
```

## Using a skill

- **Claude Code (plugin):** run `/plugin marketplace add AshR-03/ashley-ray-skills`, then `/plugin install setup-skills@ashley-ray-skills`.
- **Claude Code (single skill):** copy a skill folder into `~/.claude/skills/` (personal) or `.claude/skills/` (per project).
- **Claude.ai:** zip the skill folder and upload it under Settings → Capabilities → Skills.

## Creating a skill

1. Copy `template/` to `skills/<skill-name>/`.
2. Write `spec.md` first: the goal, the outputs, what the agent must and must not do, and the prompts that should and shouldn't trigger the skill.
3. Write `SKILL.md` to meet the spec. Keep it under 500 lines, with detail moved into `references/`.
4. Add the skill to its set in `.claude-plugin/marketplace.json` and to the table above.
5. Add unit tests for any bundled scripts under `tests/`, then run the checks below.

## How skills are checked

Skills are treated like software: each has a spec, automated checks, and (as a goal for every skill) measured results. The process is adapted from [how Uber evaluates its agent skills](https://www.uber.com/in/en/blog/optimizing-ubers-agent-skills/).

Every push and pull request runs, on Python 3.10 and 3.13:

```bash
python tools/lint_skills.py --strict      # the authoring rules
python -m unittest discover -s tests      # golden tests for bundled scripts
```

The linter checks that:

- `SKILL.md` has a `name` that matches its folder and a `description` under 1024 characters.
- The body is under 500 lines, gives its workflow as numbered steps, and has a **When things go wrong** table of errors and fixes ("try again" is not a fix).
- Every file the skill mentions exists, and every bundled file is mentioned, so the agent knows when to use it.
- `spec.md` has its required sections.
- Bundled Python scripts parse and import only the standard library, so skills install with no dependencies.
- Every skill is in a set in `marketplace.json` and linked from this README.

### Evals

Unit tests check the scripts; evals check how an agent behaves with the skill. Each case in `evals/<skill-name>/` is a prompt plus graders, run with `claude plugin eval` (built into Claude Code). Cases come from the spec:

- **Should trigger:** the skill fires and does its first step (for `brainstorm`, asks about purpose or horizon before anything else).
- **Should not trigger:** a nearby request, such as writing user stories, leaves the skill alone and still gets done.
- **Resumed:** a fixture graph is copied into the workspace first, to check the skill picks up where it left off and never calls an unfinished brainstorm done.

Every case runs with and without the skill, and the score difference shows what the skill adds. Graders mix tool-call checks, regexes and an LLM judge that votes three times.

Cases use read-only tools only, so they need no OS sandbox; a test enforces this. Evals use model calls, so they run by hand rather than in CI:

```bash
tools/run_evals.sh --model sonnet              # MAX_COST_USD caps the spend (default 5)
```

## License

[MIT](LICENSE)
