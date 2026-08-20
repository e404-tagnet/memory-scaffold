"""
confidence_floor.py
───────────────────
Prevents the agent from producing output when its confidence is too low
to be useful. Forces a graceful refusal or targeted clarification instead
of hallucinating intent.

Three operating modes:
    PRODUCE   – confidence sufficient; proceed normally
    CLARIFY   – confidence borderline; ask one targeted question first
    REFUSE    – confidence below floor; cannot responsibly produce output

Confidence is computed from a weighted combination of:
    - AI prior (from Bayesian middleware)
    - Intent completeness (from IntentExtractor)
    - Bias severity (how hard is this bias to route around?)
    - Session health (from SessionTracker flags)
    - Outcome trend (recent hit rate from memory store)

Usage:
    from confidence_floor import ConfidenceFloor, FloorDecision

    floor = ConfidenceFloor()

    decision = floor.evaluate(
        ai_prior          = 0.42,
        intent_confidence = 0.30,
        bias              = "vague_intent",
        session_flags     = ["REPEAT_ASK"],
        recent_hit_rate   = 0.40,
    )

    if decision.mode == "REFUSE":
        # Return floor.refusal_message(decision) to user
        # Do NOT call Ollama
        ...
    elif decision.mode == "CLARIFY":
        # Inject decision.clarify_prompt into system prompt
        # Ollama will ask one question
        ...
    else:
        # Proceed normally
        ...
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

# ── Thresholds — tune these ───────────────────────────────────────────────────

PRODUCE_THRESHOLD  = 0.45   # above this → produce
CLARIFY_THRESHOLD  = 0.28   # between this and PRODUCE → clarify first
# below CLARIFY_THRESHOLD → refuse

# Per-bias severity penalty (how much each bias reduces effective confidence)
_BIAS_PENALTY: dict[str, float] = {
    "anchoring":         0.08,
    "vague_intent":      0.20,   # highest — we genuinely don't know what they want
    "confirmation_bias": 0.12,
    "dunning_kruger":    0.10,
    "framing_effect":    0.07,
    "clear_intent":      0.00,   # no penalty — clarity is rare and precious
    "unknown":           0.10,
}

# Per-flag severity penalty
_FLAG_PENALTY: dict[str, float] = {
    "REPEAT_ASK":           0.10,
    "TOPIC_DRIFT":          0.05,
    "FRUSTRATION":          0.08,
    "CRITICAL_FRUSTRATION": 0.18,
    "STUCK_LOOP":           0.20,
}

# Weight of each component in final confidence score
_WEIGHTS = {
    "ai_prior":          0.35,
    "intent_confidence": 0.30,
    "outcome_trend":     0.20,
    "session_health":    0.15,
}

# ── Decision dataclass ────────────────────────────────────────────────────────

@dataclass
class FloorDecision:
    mode:              str          # PRODUCE | CLARIFY | REFUSE
    effective_conf:    float        # final weighted confidence score
    components:        dict         # breakdown of each input component
    penalties_applied: list[str]    # which penalties fired
    clarify_prompt:    str = ""     # if mode == CLARIFY, inject this
    refusal_reason:    str = ""     # if mode == REFUSE, explain why

    @property
    def should_produce(self) -> bool:
        return self.mode == "PRODUCE"

    @property
    def should_clarify(self) -> bool:
        return self.mode == "CLARIFY"

    @property
    def should_refuse(self) -> bool:
        return self.mode == "REFUSE"


# ── Clarify prompt templates ──────────────────────────────────────────────────

_CLARIFY_BY_BIAS = {
    "vague_intent": (
        "Before I produce anything, I need one clarification: "
        "what does a successful outcome look like to you? "
        "Specifically — what would it do, output, or solve?"
    ),
    "anchoring": (
        "I want to make sure I'm working from the right starting point. "
        "What's the evidence or reasoning behind your assumption? "
        "That'll help me either confirm it or offer a better baseline."
    ),
    "confirmation_bias": (
        "I want to be genuinely useful here, not just agreeable. "
        "Are you looking for an honest assessment — including where you might be wrong — "
        "or are you looking for help executing a decision you've already made?"
    ),
    "dunning_kruger": (
        "To make sure I pitch this at the right level: "
        "what's your current experience with this? "
        "I want to be useful, not patronising."
    ),
    "framing_effect": (
        "I noticed the question contains an assumption I'd like to check. "
        "Can you tell me what you're ultimately trying to achieve, "
        "rather than how you think it should be done?"
    ),
    "unknown": (
        "I want to make sure I understand what you need. "
        "Can you tell me: what are you trying to achieve, and "
        "what would a good answer look like?"
    ),
}

_REFUSE_TEMPLATES = [
    (
        "I don't have enough signal to produce something useful here. "
        "If I proceed, I'll either guess wrong or produce something generic. "
        "{reason} "
        "Can you give me a bit more to work with?"
    ),
    (
        "My confidence that I understand what you need is too low to act on. "
        "{reason} "
        "Rather than produce something plausible-but-wrong, I'd rather ask: "
        "what's the actual goal?"
    ),
]

import random

def _refusal_message(reason: str) -> str:
    template = random.choice(_REFUSE_TEMPLATES)
    return template.format(reason=reason).strip()


# ── Main class ────────────────────────────────────────────────────────────────

class ConfidenceFloor:
    """
    Evaluates whether the agent has sufficient confidence to produce output.
    """

    def __init__(
        self,
        produce_threshold:  float = PRODUCE_THRESHOLD,
        clarify_threshold:  float = CLARIFY_THRESHOLD,
    ):
        self.produce_t  = produce_threshold
        self.clarify_t  = clarify_threshold

    def evaluate(
        self,
        ai_prior:          float,
        intent_confidence: float,
        bias:              str   = "unknown",
        session_flags:     list  = None,
        recent_hit_rate:   float = 0.50,
    ) -> FloorDecision:

        session_flags = session_flags or []

        # ── Component scores ──────────────────────────────────────────────────
        # Session health: 1.0 if no flags, degrades with each flag
        flag_penalty_total = sum(
            _FLAG_PENALTY.get(f, 0.05) for f in session_flags
        )
        session_health = max(0.0, 1.0 - flag_penalty_total)

        components = {
            "ai_prior":          round(ai_prior, 3),
            "intent_confidence": round(intent_confidence, 3),
            "outcome_trend":     round(recent_hit_rate, 3),
            "session_health":    round(session_health, 3),
        }

        # ── Weighted base score ───────────────────────────────────────────────
        base = sum(
            _WEIGHTS[k] * v for k, v in components.items()
        )

        # ── Bias penalty ──────────────────────────────────────────────────────
        bias_pen = _BIAS_PENALTY.get(bias, 0.10)
        effective = max(0.0, base - bias_pen)

        # Track which penalties fired
        penalties = []
        if bias_pen > 0:
            penalties.append(f"bias:{bias}(-{bias_pen:.2f})")
        for f in session_flags:
            p = _FLAG_PENALTY.get(f, 0.05)
            penalties.append(f"flag:{f}(-{p:.2f})")

        # ── Mode decision ─────────────────────────────────────────────────────
        if effective >= self.produce_t:
            mode = "PRODUCE"
            clarify_prompt = ""
            refusal_reason = ""

        elif effective >= self.clarify_t:
            mode           = "CLARIFY"
            clarify_prompt = _CLARIFY_BY_BIAS.get(bias, _CLARIFY_BY_BIAS["unknown"])
            refusal_reason = ""

        else:
            mode           = "REFUSE"
            clarify_prompt = ""
            # Build reason from worst offenders
            worst = sorted(
                [(k, v) for k, v in components.items()],
                key=lambda x: x[1]
            )[:2]
            reason = " ".join(
                f"{k.replace('_',' ')} is low ({v:.0%})." for k, v in worst
            )
            refusal_reason = _refusal_message(reason)

        return FloorDecision(
            mode              = mode,
            effective_conf    = round(effective, 4),
            components        = components,
            penalties_applied = penalties,
            clarify_prompt    = clarify_prompt,
            refusal_reason    = refusal_reason,
        )

    def summary(self, decision: FloorDecision) -> str:
        return (
            f"[ConfidenceFloor] mode={decision.mode} "
            f"conf={decision.effective_conf:.3f} "
            f"penalties={decision.penalties_applied}"
        )
