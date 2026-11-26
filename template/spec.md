# skill-name spec

Write this before `SKILL.md`. It is the contract the skill is built and tested against: `SKILL.md` is how the agent meets it, and the evals check that it does. When a model or agent changes, rewrite `SKILL.md` from this spec rather than patching it.

The linter (`tools/lint_skills.py`) requires every heading below except **Inputs**, **Target agents and models** and **Success measures**, which are recommended.

## Goal

One or two sentences: the outcome this skill produces and why it matters.

## Inputs

What the skill starts from: files, what the user says, output of another skill.

## Outputs

What exists when the skill is done: files and their paths, and what the user is told.

## Must

Actions the agent must take, in order where order matters. Each one becomes a trajectory check in the evals.

- Example: Run `scripts/example.py check` before saying the task is done.

## Must not

Actions the agent must never take. Each one becomes a negative check in the evals.

- Example: Declare the task done on its own judgment.

## Should trigger

Prompts that should load this skill, including ones that don't name it. Each one becomes a trigger eval.

- "Example prompt in the user's own words"

## Should not trigger

Nearby prompts that should *not* load this skill. Each one becomes a negative trigger eval.

- "Example prompt that sounds similar but needs something else"

## Target agents and models

Agents the skill is written for (for example Claude Code, Claude.ai, other Agent Skills clients), and any tools it depends on.

## Success measures

How the evals judge it: what a good result looks like, and the improvement over running without the skill that would make it worth keeping.
