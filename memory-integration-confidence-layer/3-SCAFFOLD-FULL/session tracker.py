"""
session_tracker.py
──────────────────
Tracks state *across* turns within a session — things the per-turn
middleware cannot see.

Detects:
    - Topic drift      – conversation has moved away from original intent
    - Repeat asks      – user asking the same thing multiple times
    - Frustration arc  – escalating negative sentiment across turns
    - Engagement arc   – building, engaged, plateauing, disengaging
    - Turn velocity    – how fast the user is responding (urgency signal)

Produces:
    SessionState(
        turn            – current turn number
        topic_drift     – float 0-1 (0=on topic, 1=completely drifted)
        repeat_score    – float 0-1 (1=user has asked this exact thing before)
        frustration_arc – none | rising | peaked | subsiding
        engagement      – building | engaged | plateauing | disengaging
        dominant_bias   – most frequent bias this session
        flags           – list[str] of active warning flags
        recommendation  – routing hint for middleware
    )

Usage:
    from session_tracker import SessionTracker

    tracker = SessionTracker()

    # Call each turn BEFORE routing:
    state = tracker.update(
        user_message    = user_input,
        bias_detected   = decision.bias_detected,
        outcome         = last_outcome,   # from post_process
    )

    if "REPEAT_ASK" in state.flags:
        # user is stuck — force a clarify or reframe
        ...

    if state.topic_drift > 0.7:
        # conversation has wandered — summarise and refocus
        ...

    # Inject state into middleware decision
    decision.meta["session"] = state
"""

from __future__ import annotations
import time
import math
from dataclasses import dataclass, field
from typing import Optional
from difflib import SequenceMatcher
from collections import Counter

# ── State dataclass ───────────────────────────────────────────────────────────

@dataclass
class SessionState:
    turn:            int
    topic_drift:     float        # 0 = on topic, 1 = fully drifted
    repeat_score:    float        # 0 = novel, 1 = exact repeat
    frustration_arc: str          # none | rising | peaked | subsiding
    engagement:      str          # building | engaged | plateauing | disengaging
    dominant_bias:   str
    flags:           list[str]    = field(default_factory=list)
    recommendation:  str          = ""   # routing hint: comply|reframe|clarify|challenge|summarise
    timestamp:       float        = field(default_factory=time.time)

    def to_prompt_fragment(self) -> str:
        parts = [
            f"Session turn: {self.turn}",
            f"Topic drift: {self.topic_drift:.0%}",
            f"User engagement: {self.engagement}",
            f"Frustration arc: {self.frustration_arc}",
        ]
        if self.flags:
            parts.append(f"Active flags: {', '.join(self.flags)}")
        if self.recommendation:
            parts.append(f"Session recommendation: {self.recommendation}")
        return "\n".join(parts)


# ── Turn record ───────────────────────────────────────────────────────────────

@dataclass
class _TurnRecord:
    message:   str
    bias:      str
    outcome:   str
    timestamp: float = field(default_factory=time.time)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().split(), b.lower().split()).ratio()

def _topic_words(text: str) -> set[str]:
    """Rough topic fingerprint: nouns/content words, stripped of stopwords."""
    _STOP = {
        "a","an","the","is","it","i","you","we","they","he","she",
        "to","of","and","or","but","in","on","at","for","with",
        "this","that","my","your","can","do","be","have","was",
        "just","what","how","why","when","where","would","could",
        "should","please","thanks","ok","yes","no","so","if",
    }
    words = re.sub(r"[^a-z0-9 ]", "", text.lower()).split()
    return {w for w in words if w not in _STOP and len(w) > 2}

import re

_FRUSTRATION_MARKERS = [
    r"\b(again|still|as i said|already told you)\b",
    r"[!]{2,}",
    r"\b(ugh|seriously|ffs|come on|forget it|never mind)\b",
    r"\b(you'?re not (getting|understanding|listening))\b",
    r"\b(this is (useless|pointless|ridiculous))\b",
]

def _frustration_score(text: str) -> float:
    t = text.lower()
    hits = sum(1 for p in _FRUSTRATION_MARKERS if re.search(p, t))
    return min(1.0, hits * 0.35)


# ── Session tracker ───────────────────────────────────────────────────────────

class SessionTracker:
    """
    Maintains full session history and computes cross-turn signals.
    """

    def __init__(self, repeat_threshold: float = 0.72, drift_threshold: float = 0.60):
        self.repeat_threshold = repeat_threshold
        self.drift_threshold  = drift_threshold
        self._turns: list[_TurnRecord] = []
        self._origin_topics: set[str]  = set()
        self._frustration_scores: list[float] = []
        self._bias_counter: Counter = Counter()

    def update(
        self,
        user_message: str,
        bias_detected: str = "unknown",
        outcome: str = "right_partial",
    ) -> SessionState:

        record = _TurnRecord(
            message   = user_message,
            bias      = bias_detected,
            outcome   = outcome,
        )
        self._turns.append(record)
        self._bias_counter[bias_detected] += 1

        # Anchor topic on first turn
        if len(self._turns) == 1:
            self._origin_topics = _topic_words(user_message)

        current_topics   = _topic_words(user_message)
        topic_drift      = self._compute_drift(current_topics)
        repeat_score     = self._compute_repeat(user_message)
        frustration_arc  = self._compute_frustration_arc(user_message)
        engagement       = self._compute_engagement()
        flags            = self._compute_flags(topic_drift, repeat_score, frustration_arc)
        recommendation   = self._recommend(flags, topic_drift, repeat_score, frustration_arc)
        dominant_bias    = self._bias_counter.most_common(1)[0][0]

        return SessionState(
            turn            = len(self._turns),
            topic_drift     = round(topic_drift, 3),
            repeat_score    = round(repeat_score, 3),
            frustration_arc = frustration_arc,
            engagement      = engagement,
            dominant_bias   = dominant_bias,
            flags           = flags,
            recommendation  = recommendation,
        )

    # ── Drift ────────────────────────────────────────────────────────────────

    def _compute_drift(self, current_topics: set[str]) -> float:
        if not self._origin_topics or not current_topics:
            return 0.0
        overlap = len(self._origin_topics & current_topics)
        union   = len(self._origin_topics | current_topics)
        jaccard = overlap / union if union else 0.0
        return 1.0 - jaccard

    # ── Repeat detection ──────────────────────────────────────────────────────

    def _compute_repeat(self, message: str) -> float:
        if len(self._turns) < 2:
            return 0.0
        # Compare against all previous turns (excluding current)
        previous = [t.message for t in self._turns[:-1]]
        sims     = [_similarity(message, p) for p in previous]
        return max(sims) if sims else 0.0

    # ── Frustration arc ───────────────────────────────────────────────────────

    def _compute_frustration_arc(self, message: str) -> str:
        score = _frustration_score(message)
        self._frustration_scores.append(score)

        if len(self._frustration_scores) < 2:
            return "none" if score < 0.3 else "rising"

        window   = self._frustration_scores[-4:]
        avg      = sum(window) / len(window)
        trend    = window[-1] - window[0]

        if avg < 0.15:
            return "none"
        if trend > 0.15:
            return "rising"
        if avg > 0.50:
            return "peaked"
        if trend < -0.15:
            return "subsiding"
        return "rising"

    # ── Engagement arc ────────────────────────────────────────────────────────

    def _compute_engagement(self) -> str:
        n = len(self._turns)
        if n <= 2:
            return "building"

        # Look at outcome trend
        recent_outcomes = [t.outcome for t in self._turns[-4:]]
        right_count  = sum(1 for o in recent_outcomes if o.startswith("right"))
        wrong_count  = sum(1 for o in recent_outcomes if o.startswith("wrong"))

        # Message length trend (engagement proxy)
        lengths  = [len(t.message.split()) for t in self._turns[-4:]]
        len_trend = lengths[-1] - lengths[0]

        if wrong_count >= 2 and len_trend < -3:
            return "disengaging"
        if right_count >= 2 and len_trend > 2:
            return "engaged"
        if len_trend < -1 and right_count < 2:
            return "plateauing"
        return "engaged"

    # ── Flags ─────────────────────────────────────────────────────────────────

    def _compute_flags(
        self,
        drift: float,
        repeat: float,
        frustration: str,
    ) -> list[str]:
        flags = []
        if repeat >= self.repeat_threshold:
            flags.append("REPEAT_ASK")
        if drift >= self.drift_threshold:
            flags.append("TOPIC_DRIFT")
        if frustration in ("rising", "peaked"):
            flags.append("FRUSTRATION")
        if frustration == "peaked":
            flags.append("CRITICAL_FRUSTRATION")
        n = len(self._turns)
        if n >= 6:
            recent_wrongs = sum(
                1 for t in self._turns[-4:] if t.outcome.startswith("wrong")
            )
            if recent_wrongs >= 3:
                flags.append("STUCK_LOOP")
        return flags

    # ── Routing recommendation ────────────────────────────────────────────────

    def _recommend(
        self,
        flags: list[str],
        drift: float,
        repeat: float,
        frustration: str,
    ) -> str:
        if "CRITICAL_FRUSTRATION" in flags or "STUCK_LOOP" in flags:
            return "clarify"   # stop, reset, ask one focused question
        if "REPEAT_ASK" in flags:
            return "reframe"   # they didn't want what we produced — try differently
        if "TOPIC_DRIFT" in flags:
            return "summarise" # surface the drift, offer to refocus
        if frustration == "rising":
            return "challenge" # surface the assumption causing the loop
        return ""              # no override — let middleware decide

    # ── Utilities ─────────────────────────────────────────────────────────────

    def reset(self):
        self._turns.clear()
        self._origin_topics.clear()
        self._frustration_scores.clear()
        self._bias_counter.clear()

    @property
    def turn_count(self) -> int:
        return len(self._turns)

    @property
    def session_summary(self) -> dict:
        if not self._turns:
            return {}
        outcomes = [t.outcome for t in self._turns]
        return {
            "turns":          len(self._turns),
            "dominant_bias":  self._bias_counter.most_common(1)[0][0],
            "bias_breakdown": dict(self._bias_counter),
            "outcome_counts": Counter(outcomes),
            "avg_frustration": round(
                sum(self._frustration_scores) / max(1, len(self._frustration_scores)), 3
            ),
        }
