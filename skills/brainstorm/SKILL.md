---
name: brainstorm
description: Turn a rough project idea into a connected knowledge graph by interviewing the product owner with focused questions. It covers purpose (business, research or personal), who the product serves, how the owner pictures it, goals, features, constraints, risks and a roadmap, and links every answer to the ideas it relates to until nothing is left open or unconnected. Use this whenever someone has a project idea they want to shape, explore, scope or flesh out before building — "I have an idea for an app", "help me think through this project", "brainstorm with me", "what should my side project be about", "I want to start a new project" — and before writing requirements, user stories or architecture for a project that hasn't been clearly defined yet, even if they don't say "brainstorm".
---

# Brainstorm

Shape a raw project idea into a solid foundation by building a **knowledge graph** of the product owner's ideas, one focused question at a time. Each answer becomes nodes (ideas) and edges (how ideas relate). The brainstorm ends when every idea is explored and linked into one connected graph, and the result is the input for requirements and planning.

A graph, not a list, because ideas only become a project when they connect: a feature matters because it serves someone, a goal matters because a purpose motivates it, a milestone matters because it delivers something. Gaps in the graph are gaps in the plan.

## The graph

- **Directed, cycles allowed.** Edges have a direction (`feature -[serves]-> stakeholder`), and loops are normal: a goal motivates a feature, the feature achieves the goal.
- **Nodes** have a type: `idea` (the seed), `purpose`, `stakeholder`, `goal`, `vision`, `feature`, `constraint`, `risk`, `milestone`, `measure`, `assumption`.
- **Edges** have a type such as `motivates`, `serves`, `achieves`, `requires`, `delivers`, `precedes`, `threatens`, `measures`, `conflicts-with`.
- **Open questions** live on nodes. A node with open questions is still to be explored.

Read `references/graph-model.md` for every node and edge type and how to choose between them.

Keep the graph with the bundled script, which validates types, refuses duplicate edges and checks the definition of done. Run it from the project root:

```bash
python <skill-dir>/scripts/brainstorm_graph.py <command> [options]
```

The graph lives in `docs/brainstorm/graph.json` by default (`--graph` changes it). Commands: `init`, `add-node`, `update-node`, `remove-node`, `add-question`, `close-question`, `add-edge`, `remove-edge`, `set`, `record`, `show`, `check`, `render`. Use `--help` on any of them.

If `docs/brainstorm/graph.json` already exists, this is a resumed brainstorm: run `show` and `check`, tell the owner where it stands in a line or two, and carry on from the open items instead of starting over.

## Definition of done

The brainstorm is finished only when `check` exits 0, which means all of:

1. **No open questions** on any node.
2. **No isolated nodes**: every node has at least one edge.
3. **One connected graph**: every node links back, through some path, to the seed idea. A cluster of ideas linked to each other but not to the rest is not done.
4. **Coverage**: at least one `purpose`, `stakeholder`, `goal`, `vision` and `feature`, a known horizon (short- or long-term), and `milestone` nodes for a long-term project.

Never declare the brainstorm finished on your own judgment; let `check` decide.

## Workflow

### 1. Plant the seed

If the owner already described the idea, use their words. If not, ask for it in one short plain message ("What's the project idea? A sentence or two is plenty."), because the seed is free text and a multiple-choice question would put words in their mouth. Then:

```bash
python <skill-dir>/scripts/brainstorm_graph.py init --title "<short name>" --idea "<idea in their words>"
```

### 2. Ask, record, repeat

Each round:

1. **Run `check`** and pick what to ask from what it reports, in this order:
   1. **Missing purpose and horizon first.** Purpose shapes every later question: a business case leads to customers and revenue, research to hypotheses and evaluation, personal to learning goals and enjoyment.
   2. **Detached groups and isolated nodes.** Ask a linking question that would join them to the rest (see "Linking questions" below).
   3. **Other missing coverage**, then **open questions**, starting with nodes closest to the seed and with the most links, since those shape the most.
2. **Ask with AskUserQuestion**: up to 4 questions per call, all about the same area, so the owner stays in one train of thought. How to write them is below.
3. **Record every answer straight away:**
   - `add-node` for each new idea (with `--question` for anything the answer raises but doesn't settle).
   - `add-edge` for every relationship the answer states or clearly implies. An answer that adds a node without an edge is only half recorded.
   - `close-question` for the questions it settled.
   - `record` the question and answer with the nodes it touched, so the final document shows where each idea came from.
4. **Reflect back in one line**: what was added and linked, e.g. "Added *weekly progress emails* (feature), serving *gym members* and achieving *keep members engaged*."

Every few rounds, run `render` and mention that `docs/brainstorm/BRAINSTORM.md` shows the graph so far.

### 3. Keep it converging

Answers open new questions, so the graph can grow forever. Keep it heading to done:

- **Only add questions that change the project.** If the answer wouldn't change what gets built, for whom, or in what order, don't ask it.
- **Park what's out of scope.** If the owner says something is "later" or "not now", add it with `--parked` and link it to what it relates to. Parked ideas still count for connectedness but need no more questions.
- **Offer a wrap-up after about 8 rounds**, or sooner if answers get thin. Ask with AskUserQuestion whether to keep going or close the remaining open questions as assumptions. For each one closed this way, add an `assumption` node with your best reasonable guess, link it, and close the question. The owner can revisit assumptions later; they are visible in the final document.

### 4. Finish

When `check` passes:

1. Run `render` to write `docs/brainstorm/BRAINSTORM.md`: the Mermaid diagram, every idea grouped by type with its links, and the question log.
2. Summarise in a few lines: the purpose, who it serves, the core features, the roadmap shape, and the key assumptions and risks.
3. Ask one last AskUserQuestion: does this capture the project, or is something missing or wrong? If something is, go back to step 2 for it.
4. Point to the next step: turning the graph into requirements and user stories. Each `feature` that `serves` a `stakeholder` and `achieves` a `goal` is a ready-made story ("As a <stakeholder>, I want <feature> so that <goal>").

## Asking good questions

The quality of the graph depends on the questions. A good question is **grounded in what the owner already said**, **concrete**, **answerable today**, and **produces a node or an edge**.

**Good:**

- "What purpose does this project serve?" with options *Business*, *Research*, *Personal* (multiSelect, since a project can be both personal and research).
- "You mentioned a customer dashboard. What do you picture your end user seeing there first?" with options built from what's in the graph, such as *Their order history*, *Delivery status*, *Spending over time*.
- "You want this to help you land a data role, and you described a stock-price predictor. Which matters more for that goal?" with options *Model accuracy*, *A polished live demo*, *Clean, well-tested code*.

**Bad:**

- "Where do you see the product in 20 years?" Too far away to answer honestly, and the answer changes nothing about what to build now.
- "How much money do you want to make from this product?" A wish, not a fact about the product. Ask how it would make money instead: "Who would pay: the gyms, or their members?"
- "Where do you see this project helping?" Too vague to answer well and too open to turn into a node. Name the area: "You said it's for small gyms. Is the main help saving staff time, or keeping members coming back?"

Rules of thumb:

- **Quote their words.** Use "You mentioned X…" to show the question comes from their own answers, and to make clear which node it explores.
- **Options come from the graph.** Build the 2–4 options from ideas already in the graph or the most likely answers for this kind of project. The owner can always choose "Other" to type their own.
- **One idea per question.** Don't ask about two things at once ("Who uses it and how do they pay?").
- **No jargon.** Write as the owner would talk, not in the graph's terms: say "Who will use this?", not "Identify stakeholder nodes."
- **Don't re-ask.** Check `show` before asking; if the graph already holds the answer, use it.
- **Make each question stand alone.** The owner may see only the question dialog, so include the context it depends on.
- **Use multiSelect when answers can combine** (purpose, user groups, platforms) and single-select when they can't (which matters most, what comes first).
- **Keep headers short** (12 characters or fewer), such as "Purpose", "Users", "Dashboard", "Roadmap".

### Linking questions

When `check` reports isolated nodes or detached groups, ask a question whose answer is an edge:

- "You mentioned *offline mode* and *gym owners*. Is offline mode mainly for owners at the front desk, for members in the gym, or for both?" (→ `serves` edges)
- "Does *export to CSV* help with *saving staff time*, or is it for something else?" (→ `achieves`, or a new goal)
- "Should *payments* come before or after *class booking* on the roadmap?" (→ `precedes`)

Read `references/questions.md` for a question bank for each node type, follow-up patterns, and more good and bad examples.

## When things go wrong

| Problem | What to do |
| --- | --- |
| `No graph at … Run init first.` | No brainstorm has started here. Run `init`, or pass `--graph` if the graph lives somewhere else. |
| `… already exists` when running `init` | A brainstorm is in progress. Run `show` and `check` and resume it. Use `--force` only if the owner asks to start over. |
| `Unknown node '…'` | The message lists the known ids. Use one of them, or `add-node` first if the idea is new. |
| `That edge already exists.` | Nothing to do: the link is already recorded. |
| `check` still fails after every question is closed | Read its report. Isolated nodes and detached groups need a linking question; missing coverage needs a question for that type. Never add `relates-to` edges just to make it pass. |
| `python: command not found` | Run the script with `python3` instead. |
| The owner wants to stop early | Offer the wrap-up from step 3: close the remaining questions as `assumption` nodes with their agreement, then `render`. |

## If AskUserQuestion isn't available

Some agents don't have an AskUserQuestion tool. Then ask in plain text, numbered with the options listed under each and an "or tell me something else" line, and still at most 4 questions per message.
