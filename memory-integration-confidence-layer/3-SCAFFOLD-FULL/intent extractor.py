"""
intent_extractor.py
───────────────────
Extracts structured intent from user input and maintains it across turns.

Produces:
    Intent(
        goal             – what they're trying to achieve
        constraints      – explicit limits ("under 100 lines", "no external deps")
        context          – background they've provided
        success_criteria – how they'd know it worked
        confidence       – how sure we are about the extraction (0-1)
        raw              – original text
    )

Persists per-session in memory store under "intent_history".

Usage:
    from intent_extractor import IntentExtractor

    ix = IntentExtractor()
    intent = ix.extract(user_message, session_history)

    # intent.goal             → str
    # intent.constraints      → list[str]
    # intent.context          → str
    # intent.success_criteria → str
    # intent.confidence       → float
    # intent.is_complete()    → bool — enough signal to act on?
    # intent.merge(prev)      → Intent — fold new into previous turn's intent

Drop into bayesian_middleware.pre_process():
    intent  = self.ix.extract(user_message, self.history)
    decision.meta["intent"] = intent
    # then inject intent.goal into the system prompt
"""

from __future__ import annotations
import re
import json
import time
import requests
from dataclasses import dataclass, field
from typing import Optional

OLLAMA_BASE = "http://localhost:11434"
LLM_MODEL   = "mistral"

# ── Intent dataclass ──────────────────────────────────────────────────────────

@dataclass
class Intent:
    goal:             str       = ""
    constraints:      list[str] = field(default_factory=list)
    context:          str       = ""
    success_criteria: str       = ""
    confidence:       float     = 0.0
    raw:              str       = ""
    timestamp:        float     = field(default_factory=time.time)

    def is_complete(self) -> bool:
        """Enough signal to act without clarification."""
        return bool(self.goal) and self.confidence >= 0.55

    def merge(self, previous: Optional["Intent"]) -> "Intent":
        """
        Fold this intent into the previous turn's intent.
        New fields override; missing fields inherit from previous.
        """
        if previous is None:
            return self
        return Intent(
            goal             = self.goal or previous.goal,
            constraints      = list(set(self.constraints + previous.constraints)),
            context          = self.context or previous.context,
            success_criteria = self.success_criteria or previous.success_criteria,
            confidence       = max(self.confidence, previous.confidence * 0.8),
            raw              = self.raw,
            timestamp        = self.timestamp,
        )

    def to_prompt_fragment(self) -> str:
        """Inject into system prompt so the LLM knows what the user actually wants."""
        parts = []
        if self.goal:
            parts.append(f"User's actual goal: {self.goal}")
        if self.constraints:
            parts.append(f"Constraints: {'; '.join(self.constraints)}")
        if self.context:
            parts.append(f"Background context: {self.context}")
        if self.success_criteria:
            parts.append(f"Success looks like: {self.success_criteria}")
        parts.append(f"Intent confidence: {self.confidence:.0%}")
        return "\n".join(parts)

    def to_dict(self) -> dict:
        return {
            "goal":             self.goal,
            "constraints":      self.constraints,
            "context":          self.context,
            "success_criteria": self.success_criteria,
            "confidence":       self.confidence,
            "raw":              self.raw,
            "timestamp":        self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Intent":
        return cls(**d)


# ── LLM extraction ────────────────────────────────────────────────────────────

_SYSTEM = """\
You extract structured intent from a user message in a conversation with an AI assistant.

Return ONLY a JSON object, no markdown, no explanation:
{
  "goal":             "<what they are ultimately trying to achieve, one sentence>",
  "constraints":      ["<explicit limit>", "<another limit>"],
  "context":          "<background they've provided, or empty string>",
  "success_criteria": "<how they would know it worked, or empty string>",
  "confidence":       <0.0-1.0, how clear their intent is>
}

If a field cannot be determined, use "" or [].
confidence 0.0 = completely vague, 1.0 = crystal clear.
"""


def _call_ollama(system: str, user: str, history: list[dict] = None) -> dict:
    messages = [{"role": "system", "content": system}]
    if history:
        messages += history[-6:]   # last 3 exchanges for context
    messages.append({"role": "user", "content": user})

    resp = requests.post(
        f"{OLLAMA_BASE}/api/chat",
        json={
            "model":   LLM_MODEL,
            "stream":  False,
            "messages": messages,
            "options": {"temperature": 0.1, "num_predict": 200},
        },
        timeout=20,
    )
    resp.raise_for_status()
    raw = resp.json()["message"]["content"].strip()
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    return json.loads(raw)


# ── Heuristic fallback ────────────────────────────────────────────────────────

_CONSTRAINT_PATTERNS = [
    r"(under|less than|no more than|max(?:imum)?)\s+\d+",
    r"without\s+\w+",
    r"no\s+(external|third.party|dependencies|imports)",
    r"(only|just)\s+use\s+\w+",
    r"must\s+(be|use|have|work)",
    r"(keep|maintain|preserve)\s+the\s+\w+",
]

_SUCCESS_PATTERNS = [
    r"so (that|i can|it|we)",
    r"in order to",
    r"the goal is",
    r"i want to be able to",
    r"it should (work|output|return|produce)",
]

def _heuristic_extract(text: str) -> Intent:
    constraints = []
    for p in _CONSTRAINT_PATTERNS:
        for m in re.finditer(p, text, re.I):
            constraints.append(m.group(0))

    success = ""
    for p in _SUCCESS_PATTERNS:
        m = re.search(p, text, re.I)
        if m:
            success = text[m.start():][:120]
            break

    # Rough confidence: length + constraint presence
    conf = min(0.6, len(text.split()) / 40 + len(constraints) * 0.1)

    return Intent(
        goal             = text[:120] if len(text) > 0 else "",
        constraints      = constraints,
        context          = "",
        success_criteria = success,
        confidence       = round(conf, 3),
        raw              = text,
    )


# ── Extractor class ───────────────────────────────────────────────────────────

class IntentExtractor:
    """
    Extracts and merges structured intent across turns.
    Falls back to heuristics if Ollama is unreachable.
    """

    def __init__(self, model: str = LLM_MODEL):
        self.model    = model
        self.history: list[Intent] = []

    def extract(
        self,
        user_message: str,
        session_history: list[dict] = None,
    ) -> Intent:
        try:
            data = _call_ollama(_SYSTEM, user_message, session_history)
            intent = Intent(
                goal             = data.get("goal", ""),
                constraints      = data.get("constraints", []),
                context          = data.get("context", ""),
                success_criteria = data.get("success_criteria", ""),
                confidence       = float(data.get("confidence", 0.5)),
                raw              = user_message,
            )
        except Exception as e:
            print(f"[IntentExtractor] LLM failed ({e}), using heuristics.")
            intent = _heuristic_extract(user_message)

        # Merge with previous turn's intent
        previous = self.history[-1] if self.history else None
        merged   = intent.merge(previous)
        self.history.append(merged)

        # Cap history at 20 turns
        if len(self.history) > 20:
            self.history = self.history[-20:]

        return merged

    @property
    def current(self) -> Optional[Intent]:
        return self.history[-1] if self.history else None

    def reset(self):
        self.history.clear()
