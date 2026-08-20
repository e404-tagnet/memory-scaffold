# ARGUS — Setup & Usage Instructions

Everything you need to get this running in one session.

---

## What this is

ARGUS is a structured prompt framework. It is not software. There is nothing to install.

It works by loading carefully designed context files into Claude at the start of each session. Those files tell Claude who you are, how to route your requests, which specialist persona to adopt, and which internal checks to run before responding.

The result: Claude behaves like a team of specialists who already know your business — not a generic chatbot starting from zero every time.

---

## What's in the box

| File / Folder | What it does |
|---|---|
| `ARGUS_MEMORY.md` | Your persistent context. Claude reads this first, every session. |
| `DISPATCH_ENGINE.md` | The routing layer. Routes your task to the right mode. |
| `modes/` | 6 specialist personas (CODER, STRATEGY, FINANCE, MARKETER, OPS, SALES) |
| `skills/` | 12 skill files — internal checklists that activate per mode |
| `README.md` | Quick reference |
| `INSTRUCTIONS.md` | You are here |

---

## Step 1 — Fill in ARGUS_MEMORY.md (10 minutes)

Open `ARGUS_MEMORY.md` in any text editor. Fill in every section marked with `[brackets]`.

**The sections are:**
- **Who I am** — your name, role, location, businesses
- **Business context** — one block per business: what it does, its stage, revenue range, biggest constraint
- **Current priorities** — your top 3 priorities this week
- **Active blockers** — things that are stuck or unresolved
- **Operating rules** — these are pre-filled with sensible defaults; edit to match your preferences
- **My preferences** — tone, format, what you don't want

**Tips:**
- Be specific. "E-commerce business" is less useful than "D2C skincare brand, 3 years old, £40k/month revenue, struggling with retention."
- Keep it under 150 lines. Longer files work but adherence drops.
- You don't need to fill in the "Session handoff" section yet — that comes later.

---

## Step 2 — Your first session

**Open a new Claude conversation at claude.ai**

Then do this, in order:

### 2a — Load your memory

Copy the entire contents of `ARGUS_MEMORY.md` and paste it into Claude with this instruction at the top:

```
Read the following file fully before responding to anything in this session:

[paste ARGUS_MEMORY.md contents here]
```

### 2b — Load the dispatch engine

Copy the entire contents of `DISPATCH_ENGINE.md` and paste it in as a follow-up message:

```
Also load this routing layer for this session:

[paste DISPATCH_ENGINE.md contents here]
```

Claude will confirm it's ready.

### 2c — Trigger your first mode

Type your task using this format:

```
ARGUS [your task]
```

**Examples:**
- `ARGUS build me a booking API in Node.js`
- `ARGUS should I hire a full-time ops manager or use a contractor?`
- `ARGUS write a cold email sequence for our new product launch`
- `ARGUS create an SOP for onboarding new drivers`
- `ARGUS review our pricing — we're charging £99/month, costs are £30/customer`

The dispatch engine reads your task, picks the right mode, and Claude switches into that specialist persona automatically.

---

## Step 3 — During a session

**Switching modes**

If your task changes, just use a new trigger:

```
ARGUS switch to FINANCE
```

or just use a new task trigger and the engine will re-route:

```
ARGUS now I need to think about pricing for this feature
```

**Asking a general question (no mode)**

You can still ask Claude anything without a trigger. The memory and operating rules are still active — just no specialist mode.

**Using a skill directly**

Skills normally activate automatically, but you can invoke them explicitly:

```
ARGUS run a pre-mortem on the plan we just discussed
```

```
ARGUS run an objection handler on: "Your price is too high compared to competitors"
```

---

## Step 4 — End every session with a handoff

This is the most important habit. At the end of every session, type:

```
ARGUS generate handoff
```

Claude will produce a compact summary (under 200 words) covering:
- What was decided
- What's in progress
- What to pick up next session
- Any blockers that emerged

**Copy that output and paste it into the "Session handoff" section at the bottom of `ARGUS_MEMORY.md`.** Replace the previous handoff each time.

Next session, paste ARGUS_MEMORY.md first as usual — the handoff is already in it, so Claude picks up exactly where you left off.

---

## Step 5 — Maintain your memory file

**Weekly (2 minutes):**
- Update "Current priorities" to reflect this week's focus
- Update "Active blockers" — remove resolved ones, add new ones

**Monthly (5 minutes):**
- Review "Business context" — has anything changed?
- Review "Operating rules" — is Claude behaving how you want? Adjust if not.

---

## The 6 modes — what each one does

### CODER
Full-stack engineering mindset. Confirms requirements before writing code. Flags security risks before deployment. Includes error handling as standard. Calls out tech debt explicitly.

*Best for:* building features, debugging, code review, architecture decisions, API design.

### STRATEGY
Challenges your assumptions before agreeing with you. Runs a pre-mortem before recommending anything major. Gives a recommendation, not just options. Ends every response with the one thing to decide first.

*Best for:* big decisions, pivots, planning, "should I" questions, thinking through direction.

### FINANCE
CFO-level rigour. Shows workings, not just numbers. Models three scenarios (base, optimistic, conservative). Checks your cash position before any financial advice. Flags any assumption that changes the outcome significantly.

*Best for:* pricing decisions, cost analysis, forecasting, investment decisions, cash flow.

### MARKETER
Direct-response copywriter. Matches your voice before writing. Finds non-obvious angles. Avoids AI-sounding language and corporate jargon. Explains what's working and why.

*Best for:* copy, content, cold outreach, ads, emails, social posts, brand messaging.

### OPS
Systems thinker. Builds SOPs with owners and definitions of done. Flags key person risks. Keeps checklists to the minimum viable set. Every process gets a review cadence.

*Best for:* documenting processes, building checklists, onboarding, incident debriefs, workflow design.

### SALES
Buyer-first approach. Opens outreach with their problem, not your product. Handles objections by addressing the real concern underneath. Never recommends discounting without checking the value case first.

*Best for:* cold outreach, proposals, handling objections, pipeline strategy, pitch structure.

---

## The 12 skills — what each one does

| Skill | Mode | What it does |
|---|---|---|
| `security-audit` | CODER | Checks for auth, data handling, and dependency risks before any deploy |
| `code-review` | CODER | Structured review: what works, issues by priority, suggested refactor |
| `pre-mortem` | STRATEGY | Imagines failure, identifies top 5 failure modes, flags the kill shots |
| `assumption-check` | STRATEGY | Surfaces hidden assumptions and rates which ones are load-bearing |
| `cash-flow-check` | FINANCE | Checks your runway and flags cash position risks before any advice |
| `breakeven` | FINANCE | Calculates breakeven with working shown, plus sensitivity analysis |
| `voice-match` | MARKETER | Calibrates tone from examples before writing any copy |
| `angle-finder` | MARKETER | Generates 3 non-obvious angles before choosing what to write from |
| `sop-builder` | OPS | Structures SOPs with trigger, steps, owner, definition of done, failure modes |
| `debrief` | OPS | Post-project review: what worked, what didn't, what changes |
| `objection-handler` | SALES | Classifies objection, identifies real concern, drafts response + follow-up |
| `proposal-builder` | SALES | Structures proposals in buyer-first order: problem → outcome → delivery → price |

Skills run automatically when the mode detects they're relevant. You can also trigger them explicitly.

---

## Adding your own modes and skills

The system is designed to be extended.

**To add a new mode:**
1. Create a new file in `modes/` — e.g. `modes/HR.md`
2. Follow the same structure: Persona, Behaviour rules, Skills loaded, Output format
3. Add a routing rule to `DISPATCH_ENGINE.md` in the keyword table

**To add a new skill:**
1. Create a file in the relevant `skills/` subfolder
2. Structure it as: When to activate → Process (steps) → Output format
3. Reference it in the relevant mode file under "Skills loaded"

**To customise an existing mode:**
Open the mode file and edit the behaviour rules. The persona and output format sections are the easiest places to adjust tone and constraints.

---

## Troubleshooting

**Claude isn't following the mode rules**
- Check your ARGUS_MEMORY.md is under 150 lines — longer files reduce adherence
- Try re-loading both files at the start of the session
- Add the instruction "Stay in CODER mode for this entire session" at the top

**Claude isn't picking up the right mode from my trigger**
- Check the DISPATCH_ENGINE.md routing table — your keywords may not match
- Add your specific keyword to the relevant row in the table
- Or just say explicitly: `ARGUS use STRATEGY mode — should I hire a contractor?`

**Responses feel generic**
- Your ARGUS_MEMORY.md business context may be too vague — make it more specific
- Add a sentence to your preferences: "Always refer to my specific business context when relevant"

**Session handoff isn't capturing what I need**
- Ask for a more specific handoff: "ARGUS generate a handoff focusing on the pricing decision and the three options we discussed"

---

## Quick reference card

```
SESSION START
  1. Paste ARGUS_MEMORY.md → "Read this before responding"
  2. Paste DISPATCH_ENGINE.md → "Load this routing layer"

TRIGGER A MODE
  ARGUS [your task]

SWITCH MODE
  ARGUS switch to [MODE]

INVOKE A SKILL
  ARGUS run a pre-mortem on [X]
  ARGUS run an objection handler on: "[objection]"

END SESSION
  ARGUS generate handoff
  → Paste output into ARGUS_MEMORY.md
```
