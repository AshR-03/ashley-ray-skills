# brainstorm spec

## Goal

Turn a rough project idea into a connected knowledge graph of the product owner's ideas: purpose, stakeholders, vision, goals, features, constraints, risks and roadmap. The graph is the agreed starting point for requirements, so nothing in it is left open or unconnected.

## Inputs

- The project idea, in the owner's words, from the conversation.
- On a resumed brainstorm, an existing `docs/brainstorm/graph.json`.

## Outputs

- `docs/brainstorm/graph.json`: the graph, written only through `scripts/brainstorm_graph.py`.
- `docs/brainstorm/BRAINSTORM.md`: a Mermaid diagram, every idea grouped by type with its links, and the question log.
- A short summary for the owner: purpose, who it serves, core features, roadmap shape, key assumptions and risks, and the next step (requirements and user stories).

## Must

- Use the owner's own words for the seed idea, and ask for it in plain text if they haven't given it.
- Ask about purpose and horizon before other areas.
- Ask with AskUserQuestion, at most 4 questions per call, all on the same area. Fall back to numbered plain-text questions only when AskUserQuestion is unavailable.
- Record every answer straight away: nodes, edges, closed questions and a `record` log entry.
- Run `check` to pick the next questions and before declaring the brainstorm finished.
- Offer a wrap-up after about 8 rounds, and close remaining questions as `assumption` nodes only with the owner's agreement.
- On a resumed brainstorm, run `show` and `check` and continue from the open items.
- Run `render` when finished, and ask the owner to confirm the result.

## Must not

- Declare the brainstorm finished while `check` exits non-zero.
- Edit `graph.json` by hand instead of through the script.
- Start a new graph over an existing one (`init --force`) without the owner asking.
- Ask questions whose answer wouldn't change what gets built, for whom, or in what order.
- Write requirements, user stories, architecture or code during the brainstorm.

## Should trigger

- "I have an idea for an app that helps small gyms keep members coming back"
- "Help me think through a side project before I start building"
- "Brainstorm with me: I want to build something for my portfolio"
- "I want to start a new project but I'm not sure what it should do yet"
- "Can we scope out this idea before writing any requirements?"

## Should not trigger

- "Write user stories for the login feature in this spec" (requirements are already defined)
- "Fix the failing test in auth.test.ts" (code work)
- "Give me 10 name ideas for my bakery" (a quick list, not a project to shape)
- "Draw an architecture diagram for this service" (design, not discovery)

## Target agents and models

Written for Claude Code and Claude.ai, and any Agent Skills client that can run Python 3. Works best with an AskUserQuestion tool; falls back to plain-text questions without one.

## Success measures

- `check` exits 0 at the end of every completed run, and the agent never claims done before that.
- Questions quote the owner's earlier answers and each one produces a node or an edge.
- Against a run without the skill, a blind judge prefers the result with the skill: a more complete and connected picture of the project in a similar number of questions.
