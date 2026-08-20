# SKILL: Security Audit
> Run this before any task involving deployment, production code, or external-facing systems.

---

## When to activate
- User asks to deploy, ship, or push to production
- Code will handle user data, authentication, or payments
- Code involves an external API or webhook

---

## Checklist to run internally before responding

Work through these silently. Only surface issues found, not the full list.

**Authentication & authorisation**
- [ ] Is every endpoint protected that should be?
- [ ] Are there any hardcoded credentials or API keys in the code?
- [ ] Is user input validated before it touches a database or file system?

**Data handling**
- [ ] Is sensitive data (passwords, tokens, PII) stored or logged anywhere it shouldn't be?
- [ ] Are database queries parameterised? (No raw string concatenation into SQL)
- [ ] Is data encrypted in transit (HTTPS) and at rest where needed?

**Dependencies**
- [ ] Are there any known-vulnerable packages in use?
- [ ] Are dependencies pinned to specific versions?

**Error handling**
- [ ] Do error messages expose internal details to the user?
- [ ] Is there logging in place that would catch a breach?

---

## Output format

If issues are found:
> **Security flags before deploy:**
> - [Issue 1] — [severity: low/medium/high] — [fix]
> - [Issue 2] — ...

If no issues found:
> **Security check passed.** No critical issues found. Proceeding.
