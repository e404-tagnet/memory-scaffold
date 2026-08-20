"""
outcome_feedback.py
───────────────────
Infers real outcome quality from user behaviour — not response length.

Signal hierarchy (strongest → weakest):
    1. Explicit rating        – user says "perfect" / "wrong" / "not what I meant"
    2. Rephrasing signal      – user repeats same ask = previous response failed
    3. Follow-up type         – clarifying question vs. building on the answer
    4. Sentiment shift        – frustration markers vs. acknowledgement markers
    5. Silence / topic change – ambiguous; treated as neutral

Produces:
    FeedbackSignal(
        outcome     – right_exact | right_partial | clarify_needed | wrong_close | wrong_badly
        confidence  – how sure we are about the inferred outcome
        reason      – human-readable explanation
        raw_signals – dict of all detected signals
    )

Usage:
    from outcome_feedback import OutcomeFeedback

    fb = OutcomeFeedback()

    # After AI responds, call with the NEXT user message:
    signal = fb.infer(
        previous_user_msg = "How do I configure Podman networking?",
        ai_response       = "Here's how...",
        next_user_msg     = "That's not what I meant, I need rootless mode.",
    )
    # signal.outcome    → "wrong_close"
    # signal.confidence → 0.82
    # signal.reason     → "User corrected scope: 'not what I meant'"

    # Or provide explicit feedback directly:
    signal = fb.explicit("perfect, exactly what I needed")
    # signal.outcome → "right_exact"
"""

from __future__ import annotations
import re
import time
from dataclasses import dataclass, field
from typing import Optional
from difflib import SequenceMatcher

# ── Signal dataclass ──────────────────────────────────────────────────────────

@dataclass
class FeedbackSignal:
    outcome:     str          # right_exact | right_partial | clarify_needed | wrong_close | wrong_badly
    confidence:  float        # 0-1
    reason:      str          # human-readable
    raw_signals: dict         = field(default_factory=dict)
    timestamp:   float        = field(default_factory=time.time)

    def to_outcome_key(self) -> str:
        """Maps to the outcome keys used by memory_store / bayesian_middleware."""
        mapping = {
            "right_exact":    "right_exact",
            "right_partial":  "right_partial",
            "clarify_needed": "clarify",
            "wrong_close":    "wrong_close",
            "wrong_badly":    "wrong_badly",
        }
        return mapping.get(self.outcome, "right_partial")


# ── Signal pattern banks ──────────────────────────────────────────────────────

_EXPLICIT_POSITIVE = [
    r"\b(perfect|exactly|brilliant|spot on|that'?s it|nailed it|thanks?\b.*\bperfect)\b",
    r"\b(great|excellent|works?|sorted|did it|that worked)\b",
    r"\byep,? that'?s (right|it|what i (wanted|needed|meant))\b",
]

_EXPLICIT_NEGATIVE = [
    r"\b(wrong|incorrect|not right|that'?s not|not what i (wanted|meant|asked|needed))\b",
    r"\b(no,?\s+that'?s|nope|wrong answer|completely (off|wrong|missed))\b",
    r"\b(useless|doesn'?t work|broken|failed|nothing like)\b",
]

_EXPLICIT_PARTIAL = [
    r"\b(close but|almost|nearly|partially|sort of|kind of right|on the right track)\b",
    r"\b(mostly|good start|not quite|nearly there)\b",
]

_EXPLICIT_CLARIFY = [
    r"\b(what do you mean|could you (clarify|explain)|i don'?t (understand|follow))\b",
    r"\b(more detail|elaborate|be more specific|expand on)\b",
]

_FRUSTRATION = [
    r"\b(again|still|as i said|i already|how many times|you'?re not (listening|understanding))\b",
    r"[!]{2,}",
    r"\b(ugh|seriously|come on|ffs|for (god|crying|heaven)'?s sake)\b",
]

_ACKNOWLEDGEMENT = [
    r"^(ok|okay|got it|understood|makes sense|right|sure|cool|nice)\b",
    r"\b(that makes sense|i see|ah,? (right|ok|i see)|good point)\b",
]

_BUILD_ON = [
    r"\b(now (can you|add|also|let'?s)|next,? (can you|let'?s)|building on)\b",
    r"\b(additionally|furthermore|as well as|in addition to (that|this))\b",
    r"^(and |also |now )",
]


def _match_any(text: str, patterns: list[str]) -> Optional[str]:
    t = text.lower()
    for p in patterns:
        m = re.search(p, t)
        if m:
            return m.group(0)
    return None


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().split(), b.lower().split()).ratio()


# ── Main class ────────────────────────────────────────────────────────────────

class OutcomeFeedback:
    """
    Infers outcome quality from conversational signals.
    Call infer() with a sliding window of three turns.
    """

    def __init__(self):
        self._history: list[FeedbackSignal] = []

    def infer(
        self,
        previous_user_msg: str,
        ai_response:       str,
        next_user_msg:     str,
    ) -> FeedbackSignal:
        signals: dict[str, any] = {}

        # ── 1. Explicit signals (highest priority) ────────────────────────────
        if m := _match_any(next_user_msg, _EXPLICIT_NEGATIVE):
            signals["explicit_negative"] = m
        if m := _match_any(next_user_msg, _EXPLICIT_POSITIVE):
            signals["explicit_positive"] = m
        if m := _match_any(next_user_msg, _EXPLICIT_PARTIAL):
            signals["explicit_partial"] = m
        if m := _match_any(next_user_msg, _EXPLICIT_CLARIFY):
            signals["explicit_clarify"] = m

        # ── 2. Rephrasing detection ───────────────────────────────────────────
        sim = _similarity(previous_user_msg, next_user_msg)
        if sim >= 0.70:
            signals["rephrasing"] = round(sim, 2)

        # ── 3. Follow-up type ─────────────────────────────────────────────────
        if m := _match_any(next_user_msg, _BUILD_ON):
            signals["builds_on"] = m
        if m := _match_any(next_user_msg, _ACKNOWLEDGEMENT):
            signals["acknowledgement"] = m

        # ── 4. Frustration / sentiment ────────────────────────────────────────
        if m := _match_any(next_user_msg, _FRUSTRATION):
            signals["frustration"] = m

        # ── 5. Response length heuristic (weakest signal) ────────────────────
        signals["response_length"] = len(ai_response.split())

        # ── Decision tree ─────────────────────────────────────────────────────
        signal = self._decide(signals)
        self._history.append(signal)
        if len(self._history) > 50:
            self._history = self._history[-50:]
        return signal

    def _decide(self, s: dict) -> FeedbackSignal:
        # Explicit negative → wrong
        if "explicit_negative" in s:
            sev = "wrong_badly" if "frustration" in s else "wrong_close"
            return FeedbackSignal(
                outcome=sev, confidence=0.90,
                reason=f"Explicit rejection: '{s['explicit_negative']}'",
                raw_signals=s,
            )

        # Rephrasing without positive signal → wrong
        if "rephrasing" in s and "explicit_positive" not in s:
            conf = min(0.85, s["rephrasing"])
            return FeedbackSignal(
                outcome="wrong_close", confidence=conf,
                reason=f"User rephrased same request (similarity={s['rephrasing']}). Previous response inadequate.",
                raw_signals=s,
            )

        # Explicit clarification request → clarify_needed
        if "explicit_clarify" in s:
            return FeedbackSignal(
                outcome="clarify_needed", confidence=0.85,
                reason=f"User asked for clarification: '{s['explicit_clarify']}'",
                raw_signals=s,
            )

        # Explicit positive
        if "explicit_positive" in s:
            return FeedbackSignal(
                outcome="right_exact", confidence=0.88,
                reason=f"Explicit positive: '{s['explicit_positive']}'",
                raw_signals=s,
            )

        # Partial
        if "explicit_partial" in s:
            return FeedbackSignal(
                outcome="right_partial", confidence=0.80,
                reason=f"Partial success: '{s['explicit_partial']}'",
                raw_signals=s,
            )

        # Builds on answer → probably right
        if "builds_on" in s:
            return FeedbackSignal(
                outcome="right_partial", confidence=0.65,
                reason="User building on previous answer — likely satisfied.",
                raw_signals=s,
            )

        # Acknowledgement → weakly right
        if "acknowledgement" in s:
            return FeedbackSignal(
                outcome="right_partial", confidence=0.55,
                reason=f"Acknowledgement token: '{s['acknowledgement']}'",
                raw_signals=s,
            )

        # Frustration alone
        if "frustration" in s:
            return FeedbackSignal(
                outcome="wrong_close", confidence=0.60,
                reason=f"Frustration marker without explicit correction: '{s['frustration']}'",
                raw_signals=s,
            )

        # Neutral / unknown
        return FeedbackSignal(
            outcome="right_partial", confidence=0.35,
            reason="No strong signal detected. Defaulting to partial.",
            raw_signals=s,
        )

    def explicit(self, user_text: str) -> FeedbackSignal:
        """
        Shortcut: call when you have a direct rating message with no context.
        e.g. fb.explicit("that was perfect")
        """
        return self.infer("", "", user_text)

    @property
    def recent_accuracy(self) -> float:
        """Rolling accuracy over last 10 signals."""
        window = self._history[-10:]
        if not window:
            return 0.0
        hits = sum(1 for s in window if s.outcome in ("right_exact", "right_partial"))
        return hits / len(window)

    def reset(self):
        self._history.clear()
