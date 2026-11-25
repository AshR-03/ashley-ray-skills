# Question bank

Starting points for each node type. Adapt every question to what the owner has already said: quote their words and build the options from the graph. Never ask these word for word in a vacuum.

## Contents

- Opening questions
- Questions by node type
- Follow-up patterns
- Good and bad questions, side by side

## Opening questions

Ask these right after the seed, in one AskUserQuestion call, because everything else depends on them.

| Header | Question | Options | multiSelect |
| --- | --- | --- | --- |
| Purpose | What purpose does this project serve? | Business (a product or service people would pay for, or one for a company) · Research (answering a question or testing an idea) · Personal (learning, portfolio, or for fun) | yes |
| Horizon | How long do you expect to work on this? | A short build: days to a few weeks · Longer term: months, built in stages · Not sure yet | no |
| Users | Who would use <the idea in their words>? | 2–3 likely groups for this kind of idea, e.g. "Small business owners", "Their customers", "Just me" | yes |

## Questions by node type

**Purpose**
- Business: "Who would pay for <idea>: <user group A> or <user group B>?" · "What do they use today instead?"
- Research: "What question should <idea> answer?" · "How would you know the answer is right: a benchmark, a user study, a comparison?"
- Personal: "What do you want to come away with: a new skill, a portfolio piece, or something you'll use yourself?"

**Stakeholder**
- "You mentioned <group>. What's the main thing they'd come to <idea> to do?"
- "Is <group> the same person who sets it up, or does someone else do that?"

**Goal**
- "For <stakeholder>, what would count as <idea> working: <outcome A>, <outcome B>, or <outcome C>?"
- "You want <goal>. Which of these features matters most for it?"

**Vision**
- "You mentioned <feature>. What do you picture <stakeholder> seeing there first?"
- "Should <idea> feel more like <familiar product type A> or <familiar product type B>?" (types of product, such as "a chat assistant" or "a spreadsheet")

**Feature**
- "What's the one thing <idea> must do on day one?"
- "You mentioned <feature>. Does <stakeholder> need it from the start, or could it come later?"

**Constraint**
- "Is there a deadline: a course hand-in, a job application, a launch date?"
- "Does it have to run anywhere specific: web, phone, an existing system?"

**Risk**
- "What's most likely to stop <goal>: time, getting data, or getting people to use it?"

**Milestone** (long-term projects)
- "What's the smallest version that would already be useful to <stakeholder>?"
- "After <milestone>, what comes next: <feature A> or <feature B>?"

**Measure**
- "How would you tell <goal> is happening: <measure A>, <measure B>, or by asking users?"

## Follow-up patterns

- **Zoom in:** "You mentioned <X>. What does <X> look like for <stakeholder>?"
- **Find the reason:** "Why does <feature> matter to <stakeholder>?" (yields a goal and an `achieves` edge)
- **Find the order:** "Does <A> need to exist before <B>?" (yields `requires` or `precedes`)
- **Find the tension:** "<A> and <B> pull in different directions. Which wins if you have to choose?" (yields `conflicts-with`, then a decision)
- **Test the edge:** "Is <feature> really for <stakeholder>, or for someone else?"

## Good and bad questions, side by side

| Bad | Why it fails | Better |
| --- | --- | --- |
| Where do you see the product in 20 years? | Too far ahead to answer honestly; changes nothing now. | What's the smallest version that would already be useful to gym members? |
| How much money do you want to make? | A wish, not a fact about the product. | Who would pay: the gym owner or the members? |
| Where do you see this project helping? | Too vague; can't become a node. | You said it's for small gyms. Is the main help saving staff time, or keeping members coming back? |
| What features do you want? | Invites a long, unconnected wishlist. | What's the one thing it must do for members on day one? |
| Who are your stakeholders and what are their goals? | Two questions in one, in jargon. | Who would use this day to day? |
| Do you want it to be good and fast? | Leading; everyone says yes. | If you had to choose for the first version: more features, or a faster, simpler app? |
| What's your tech stack? | Too early: a build decision, not a project idea. | Does it need to work on phones, on a website, or both? |
