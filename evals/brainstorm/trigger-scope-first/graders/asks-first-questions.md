---
type: llm
weight: 2
---

The user shared a rough project idea and wants help shaping it before building.

PASS if the response ends by asking the user questions to shape the idea, with at most 4 questions, and at least one asks what the project is for (for example business, research or personal) or its time horizon (a short project or a long-term one). The questions may be numbered plain text with suggested options.

FAIL if it asks more than 4 questions, if none of its questions is about what the project is for or its time horizon, or if instead of asking it mainly hands over a feature list, requirements, user stories, an architecture or code.
