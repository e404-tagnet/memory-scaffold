<!-- TAGNET README HEADER — Catppuccin Mocha — do not edit by hand -->
<div align="center">

[![License](https://img.shields.io/github/license/e404-tagnet/memory-scaffold?color=313244&labelColor=11111b&label=License&style=flat-square)](https://github.com/e404-tagnet/memory-scaffold/blob/main/LICENSE)
[![Status](https://img.shields.io/badge/Status-experimental-fab387?labelColor=11111b&style=flat-square)](https://github.com/e404-tagnet/memory-scaffold/pulse)
[![Version](https://img.shields.io/github/v/release/e404-tagnet/memory-scaffold?color=313244&labelColor=11111b&label=Version&style=flat-square)](https://github.com/e404-tagnet/memory-scaffold/releases)
[![Repo](https://img.shields.io/badge/Repo-memory-scaffold-94e2d5?labelColor=11111b&style=flat-square&logo=github&logoColor=94e2d5)](https://github.com/e404-tagnet/memory-scaffold)
[![Tagnet](https://img.shields.io/badge/By-Tagnet-89dceb?labelColor=11111b&style=flat-square&logo=tag&logoColor=89dceb)](https://tagnet.dev)

</div>
<!-- TAGNET README HEADER — end -->

# Bayesian Scaffold — Full System

Seven modules. One coherent decision layer between the human and Ollama.


## Architecture

```
User input
    ↓
[IntentExtractor]       what do they actually want?
    ↓
[HybridClassifier]      how are they asking? (semantic + keyword)
    ↓
[CoOccurrenceDetector]  are multiple biases compounding?
    ↓
[SessionTracker]        repeat ask? topic drift? frustration arc?
    ↓
[ConfidenceFloor]       enough signal to produce anything?
    ↓
[BayesianMiddleware]    route + system prompt injection + prior update
    ↓
Ollama LLM
    ↓
[OutcomeFeedback]       infer outcome from next user message
    ↓
MemoryStore write-back → scaffold_memory.json
```


## Files

|File                    |Role                                                 |
|------------------------|-----------------------------------------------------|
|`memory_store.py`       |Persistent JSON belief store                         |
|`bayesian_middleware.py`|Core decision engine + Bayesian updates              |
|`bias_classifier.py`    |SemanticClassifier / HybridClassifier / LLMClassifier|
|`bias_cooccurrence.py`  |Multi-bias interaction detection                     |
|`intent_extractor.py`   |Structured goal/constraint extraction across turns   |
|`outcome_feedback.py`   |Implicit satisfaction inference from next message    |
|`session_tracker.py`    |Cross-turn: drift, repeats, frustration arc          |
|`confidence_floor.py`   |PRODUCE / CLARIFY / REFUSE gating                    |
|`eval_harness.py`       |Ground truth evaluation suite                        |
|`scaffold_example.py`   |Full wired pipeline                                  |
|`monitor.html`          |Live session visualiser                              |


## Quick start

```bash
# Run the full agent
python scaffold_example.py

# Benchmark classifiers
python bias_classifier.py all

# Evaluate routing on baseline cases
python eval_harness.py routing

# Compare classifiers
python eval_harness.py compare
```


## Routes

|Route      |Trigger                                 |Behaviour                                |
|-----------|----------------------------------------|-----------------------------------------|
|`comply`   |Clear intent, high confidence           |Produces exactly what was asked          |
|`reframe`  |Detectable intent beneath stated request|Produces better answer, notes what it did|
|`clarify`  |Insufficient signal                     |Asks one focused question                |
|`challenge`|Flawed premise / cognitive bias         |Surfaces the flaw, offers reframe        |


## Swap classifier

One line in `bayesian_middleware.py`:

```python
from bias_classifier import LLMClassifier as _Classifier   # most interpretable
from bias_classifier import SemanticClassifier as _Classifier  # fastest at inference
from bias_classifier import HybridClassifier as _Classifier    # default, most robust
```


## Add eval cases from real sessions

```python
from eval_harness import EvalSuite, EvalCase

suite = EvalSuite.load("eval_cases.json")
suite.add(EvalCase(
    input          = "just make it work",
    expected_bias  = "vague_intent",
    expected_route = "clarify",
    notes          = "session 3, user stuck for 4 turns",
    source         = "session",
))
suite.save("eval_cases.json")
```


## Monitor

Open `monitor.html`, drop `scaffold_memory.json` on it.
Also works standalone as a manual simulator.

<!-- TAGNET README FOOTER — start -->

<div align="center">

**Like this work? Fuel the next widget / experiment / scaffold.**

[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-%23FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/e404.tagnet)
[![Patreon](https://img.shields.io/badge/Support-Patreon-ff424d?logo=patreon&logoColor=white&style=for-the-badge)](https://www.patreon.com/VeritasExMachina?utm_campaign=creatorshare_creator)

<small>Crafted with caffeine, curiosity, and a Catppuccin palette · © e404-tagnet</small>

</div>
<!-- TAGNET README FOOTER — end -->
