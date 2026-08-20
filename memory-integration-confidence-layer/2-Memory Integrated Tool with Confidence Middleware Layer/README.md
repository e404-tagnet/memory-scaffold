<!-- TAGNET README HEADER — Catppuccin Mocha — do not edit by hand -->
<div align="center">

[![License](https://img.shields.io/github/license/e404-tagnet/memory-scaffold?color=313244&labelColor=11111b&label=License&style=flat-square)](https://github.com/e404-tagnet/memory-scaffold/blob/main/LICENSE)
[![Status](https://img.shields.io/badge/Status-experimental-fab387?labelColor=11111b&style=flat-square)](https://github.com/e404-tagnet/memory-scaffold/pulse)
[![Version](https://img.shields.io/github/v/release/e404-tagnet/memory-scaffold?color=313244&labelColor=11111b&label=Version&style=flat-square)](https://github.com/e404-tagnet/memory-scaffold/releases)
[![Repo](https://img.shields.io/badge/Repo-memory-scaffold-94e2d5?labelColor=11111b&style=flat-square&logo=github&logoColor=94e2d5)](https://github.com/e404-tagnet/memory-scaffold)
[![Tagnet](https://img.shields.io/badge/By-Tagnet-89dceb?labelColor=11111b&style=flat-square&logo=tag&logoColor=89dceb)](https://tagnet.dev)

</div>
<!-- TAGNET README HEADER — end -->

# Bayesian Scaffold — Drop-in Middleware for Ollama Agents

Three files. One decision layer. Your agent stops being a yes-machine.


## Files

|File                    |Role                                                                    |
|------------------------|------------------------------------------------------------------------|
|`memory_store.py`       |Persistent JSON belief store — priors, bias fingerprint, outcome history|
|`bayesian_middleware.py`|Decision engine — classifies input, routes, builds system prompt        |
|`scaffold_example.py`   |Minimal working loop with Ollama                                        |
|`monitor.html`          |Live visualiser — drop in `scaffold_memory.json` to inspect             |


## Drop-in Usage

```python
from bayesian_middleware import BayesianMiddleware

mw = BayesianMiddleware(user_id="e404")

# Before Ollama call
decision = mw.pre_process(user_message)

# decision.route        → comply | reframe | clarify | challenge
# decision.bias_detected → anchoring | vague_intent | etc.
# decision.system_injection → enriched system prompt string

response = call_ollama(decision.system_injection, user_message, history)

# After Ollama responds
mw.post_process(response, decision)
# → updates priors, writes to scaffold_memory.json
```


## Routes

|Route      |When                                    |What the agent does                          |
|-----------|----------------------------------------|---------------------------------------------|
|`comply`   |Clear intent, high AI confidence        |Produces exactly what was asked              |
|`reframe`  |Detectable intent beneath stated request|Produces the better answer, notes what it did|
|`clarify`  |Insufficient signal                     |Asks one focused question                    |
|`challenge`|Flawed premise / cognitive bias detected|Surfaces the flaw, offers reframe            |

Assertiveness drift shifts the balance: the more often the AI gets wrong outcomes, the bolder it becomes — leaning toward `reframe` and `challenge` over `comply`.


## Memory Store

`scaffold_memory.json` persists across sessions:

- `human_prior` — P(human knows what they want)
- `ai_prior` — P(AI can satisfy without clarification)
- `agent_assertiveness` — drifts 0→0.90 as wrong-outcome rate rises
- `bias_counts` — fingerprint of user’s cognitive patterns
- `outcome_counts` — hit/clarify/wrong history
- `recent` — rolling 10-entry window for trend detection


## Monitor

Open `monitor.html` in any browser.

- Manual simulator works standalone (no Python needed)
- Drop `scaffold_memory.json` onto the upload zone to visualise a live session
- Shows: belief posteriors, bias radar, outcome distribution, assertiveness dial, route decisions


## Swap backends

`MemoryStore` uses JSON by default. To use SQLite:

```python
import sqlite3
from memory_store import MemoryStore

class SQLiteStore(MemoryStore):
    def _load(self): ...   # read from SQLite
    def _save(self): ...   # write to SQLite
```

API is identical. Everything else just works.

<!-- TAGNET README FOOTER — start -->

<div align="center">

**Like this work? Fuel the next widget / experiment / scaffold.**

[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-%23FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/e404.tagnet)
[![Patreon](https://img.shields.io/badge/Support-Patreon-ff424d?logo=patreon&logoColor=white&style=for-the-badge)](https://www.patreon.com/VeritasExMachina?utm_campaign=creatorshare_creator)

<small>Crafted with caffeine, curiosity, and a Catppuccin palette · © e404-tagnet</small>

</div>
<!-- TAGNET README FOOTER — end -->
