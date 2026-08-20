# SKILL: Code Review
> Run this when the user shares existing code for review or asks "what's wrong with this."

---

## When to activate
- User pastes existing code and asks for feedback
- User asks "can you review this" or "what would you improve"
- User shares a PR or diff

---

## Review framework (run in this order)

**1. Does it work?**
- Does the logic achieve the stated goal?
- Are there any obvious bugs or edge cases not handled?

**2. Is it safe?**
- Run the security-audit checklist mentally
- Flag anything that could be exploited

**3. Is it maintainable?**
- Would another developer understand this in 6 months?
- Are functions doing one thing?
- Is naming clear and consistent?

**4. Is it necessary?**
- Is there duplication that could be extracted?
- Is there complexity that could be removed?

---

## Output format

Structure the review as:

**What works well**
- [1-3 things genuinely worth keeping]

**Issues to fix** (prioritised)
1. [Critical] [Issue + why + fix]
2. [Important] [Issue + why + fix]
3. [Minor] [Issue + why + fix]

**Suggested refactor** (only if substantial improvement is possible)
- [What and why — not the full rewrite, just the direction]
