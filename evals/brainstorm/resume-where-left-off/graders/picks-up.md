---
type: llm
weight: 2
---

The workspace holds a brainstorm in progress for a gym app (docs/brainstorm/graph.json). It already records the purpose (a business selling to gyms), gym members and gym owners, the goal of keeping members coming back, and a weekly progress emails feature. Still open: whether it is a short or long-term project, how the owner pictures the product, an open question about whether the target gyms are independent or chains, and two ideas ("gym owners may not adopt it" and "built by one developer in spare time") that aren't linked to the rest.

PASS if the response shows it knows where the brainstorm stands, by referring to some of the existing ideas, and asks at most 4 questions, at least one of which is about the items still open (the time horizon, how the owner pictures the product, independent gyms or chains, or how the two unlinked ideas relate to the rest).

FAIL if it starts over (asks for the idea again or re-asks what is already recorded, such as who uses it or what it's for), says the brainstorm is complete, or asks more than 4 questions.
