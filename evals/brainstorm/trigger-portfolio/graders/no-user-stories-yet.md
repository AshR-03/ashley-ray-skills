---
type: regex
target: last_message
pattern: '\bAs an?\b(?:(?!\n\s*\n)[\s\S]){1,160}?\bI want'
flags: i
match: not_contains
---
