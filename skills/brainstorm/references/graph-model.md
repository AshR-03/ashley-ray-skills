# Graph model

How to turn answers into nodes and edges. The script enforces the type names below.

## Contents

- Node types
- Edge types
- Turning an answer into the graph
- Worked example
- File format

## Node types

| Type | What it holds | Example |
| --- | --- | --- |
| `idea` | The seed, in the owner's words. Exactly one, id `idea`. | "An app that helps small gyms keep members" |
| `purpose` | Why the project exists: business, research or personal. A project can have more than one. | "Personal: portfolio piece for a data job" |
| `stakeholder` | Anyone who uses, pays for or is affected by the product. Includes the owner when the project is personal. | "Gym members", "Gym owner", "Recruiters reading my GitHub" |
| `goal` | An outcome someone wants. Write it as an outcome, not a feature. | "Members come back at least twice a week" |
| `vision` | How the owner pictures the product, a screen, or an experience. | "Feels like a fitness tracker, not a booking system" |
| `feature` | A capability the product has. | "Class booking", "Weekly progress email" |
| `constraint` | A fixed limit: deadline, budget, skills, platform, rules. | "Must run on the gym's existing tablets" |
| `risk` | Something that could stop the project or a goal. | "Gyms already pay for booking software" |
| `milestone` | A roadmap step. Order them with `precedes`. | "MVP: booking only, one gym" |
| `measure` | How the success of a goal will be judged. | "Weekly visits per member" |
| `assumption` | Something taken as true without the owner confirming it. Used when closing questions at wrap-up. | "Members have smartphones" |

Choosing between similar types:

- **goal vs feature:** "keep members coming back" is a goal; "streak badges" is a feature that achieves it.
- **vision vs feature:** a vision is how something should look or feel; a feature is what it does. A vision usually `refines` a feature or the seed idea.
- **constraint vs risk:** a constraint is certain ("we have three months"); a risk might happen ("the API may get rate-limited").

## Edge types

Edges point from the node that acts to the node it acts on. Read each edge as a sentence: `class-booking -[serves]-> gym-members` reads "class booking serves gym members".

| Type | Typical direction | Meaning |
| --- | --- | --- |
| `motivates` | purpose or goal → goal or feature | gives the reason for |
| `serves` | feature or vision → stakeholder | is used by, or helps |
| `achieves` | feature or milestone → goal | moves the goal forward |
| `requires` | any → any | needs the other to exist or work |
| `part-of` | feature → feature, milestone → milestone | is a piece of |
| `refines` | vision or feature → feature or idea | describes in more detail |
| `precedes` | milestone → milestone | comes before on the roadmap |
| `delivers` | milestone → feature | ships |
| `constrains` | constraint → any | limits |
| `threatens` | risk → any | could stop or harm |
| `mitigates` | feature → risk | reduces |
| `measures` | measure → goal | judges success of |
| `conflicts-with` | any → any | pulls against; needs a trade-off |
| `relates-to` | any → any | fallback; prefer a specific type |

Cycles are expected. Example: `keep-members -[motivates]-> streak-badges`, `streak-badges -[achieves]-> keep-members`.

Every new node should link to at least one existing node in the same round it is added. If the answer doesn't say how it links, add an open question on the new node asking that, so `check` keeps it on the list.

## Turning an answer into the graph

1. **Find the ideas.** Each distinct thing the owner named that isn't already in the graph becomes a node. Reuse existing nodes rather than adding near-duplicates; `show` lists them.
2. **Find the links.** For each new node, ask yourself: who does it serve, what goal does it achieve, what does it need, what comes before it? Add every edge the answer states or clearly implies. Don't invent links the owner didn't suggest; ask about them instead.
3. **Find the new unknowns.** Anything the answer raises but doesn't settle becomes an open question on the relevant node, but only if it would change the project.
4. **Close what's settled.** Close the questions this answer settled.
5. **Log it.** `record` the question and answer with the node ids touched.

## Worked example

The owner answered: "It's for small independent gyms. The owner would pay a monthly fee, but it's the members who use it day to day."

```bash
G="python <skill-dir>/scripts/brainstorm_graph.py"
$G add-node --id gym-owner --type stakeholder --label "Independent gym owner" \
  --detail "Pays a monthly fee" --question "What would make the owner keep paying each month?"
$G add-node --id gym-members --type stakeholder --label "Gym members" \
  --detail "Use the app day to day"
$G add-node --id monthly-fee --type purpose --label "Business: monthly subscription paid by gyms"
$G add-edge --from idea --to gym-members --type serves
$G add-edge --from idea --to gym-owner --type serves
$G add-edge --from monthly-fee --to idea --type motivates --note "the gym owner is the paying customer"
$G record --question "Who is this for, and who pays?" \
  --answer "Small independent gyms; owner pays monthly, members use it daily" \
  --node gym-owner --node gym-members --node monthly-fee
```

The open question on `gym-owner` keeps it on `check`'s list and leads to a goal node in a later round.

## File format

`docs/brainstorm/graph.json`:

```json
{
  "title": "Gym retention app",
  "horizon": "long",
  "created": "2026-11-25T10:00:00Z",
  "updated": "2026-11-25T10:20:00Z",
  "nodes": {
    "idea": {"type": "idea", "label": "...", "detail": "", "status": "explored", "open_questions": []},
    "gym-owner": {"type": "stakeholder", "label": "...", "detail": "...", "status": "explored", "open_questions": ["..."]}
  },
  "edges": [{"from": "idea", "to": "gym-owner", "type": "serves", "note": ""}],
  "log": [{"at": "...", "question": "...", "answer": "...", "nodes": ["gym-owner"]}]
}
```

`status` is `explored` or `parked`. A node is open while `open_questions` is not empty.
