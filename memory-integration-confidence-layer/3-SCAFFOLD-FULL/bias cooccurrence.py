"""
bias_cooccurrence.py
────────────────────
Detects when multiple cognitive biases fire simultaneously and computes
a combined routing profile. Single-bias routing is naive — most real
inputs exhibit overlapping patterns.

Co-occurrence pairs have known interaction effects:
    dunning_kruger + confirmation_bias  → highest resistance to correction
    anchoring + framing_effect          → double-locked premise
    vague_intent + dunning_kruger       → user thinks they're clear but aren't
    confirmation_bias + framing_effect  → question designed to force agreement

Produces:
    CoOccurrenceProfile(
        biases          – list of active biases (score >= threshold)
        primary         – dominant bias
        secondary       – secondary bias (if any)
        interaction     – named interaction effect (if known pair)
        combined_score  – aggregate difficulty score 0-1
        routing_override – suggested route adjustment
        notes           – human-readable description
    )

Usage:
    from bias_cooccurrence import CoOccurrenceDetector

    detector = CoOccurrenceDetector()

    profile = detector.analyse(
        bias_scores = {
            "dunning_kruger":   0.72,
            "confirmation_bias":0.61,
            "vague_intent":     0.20,
            ...
        }
    )

    # profile.interaction       → "double_certainty"
    # profile.routing_override  → "challenge"
    # profile.combined_score    → 0.85

    # Get bias scores from bias_classifier:
    #   from bias_classifier import HybridClassifier
    #   scores = HybridClassifier().classify_all(text)  # see note below
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

# ── Thresholds ────────────────────────────────────────────────────────────────

ACTIVE_THRESHOLD    = 0.35   # bias score above this = "active"
SECONDARY_THRESHOLD = 0.25   # secondary bias must clear this

# ── Known interaction effects ─────────────────────────────────────────────────
# Each entry: (bias_a, bias_b) -> (interaction_name, combined_difficulty, routing_override, description)

_INTERACTIONS: dict[frozenset, tuple[str, float, str, str]] = {
    frozenset({"dunning_kruger", "confirmation_bias"}): (
        "double_certainty",
        0.90,
        "challenge",
        "User is both overconfident and seeking validation. "
        "Compliance reinforces the loop. Must surface the gap — diplomatically.",
    ),
    frozenset({"anchoring", "framing_effect"}): (
        "double_locked_premise",
        0.85,
        "challenge",
        "A false anchor is baked into a loaded question. "
        "Both the starting point and the frame are wrong. Reframe the question entirely.",
    ),
    frozenset({"vague_intent", "dunning_kruger"}): (
        "confident_vagueness",
        0.80,
        "clarify",
        "User thinks they've been clear; they haven't. "
        "Challenge will feel unwarranted — clarify tactfully, don't expose the gap directly.",
    ),
    frozenset({"confirmation_bias", "framing_effect"}): (
        "engineered_agreement",
        0.82,
        "challenge",
        "Question is constructed to force a particular answer. "
        "Complying is epistemic cowardice. Name the frame before answering.",
    ),
    frozenset({"anchoring", "dunning_kruger"}): (
        "immovable_conviction",
        0.88,
        "challenge",
        "User has anchored on a wrong answer and is certain of it. "
        "Direct contradiction will fail — present evidence that reframes rather than refutes.",
    ),
    frozenset({"vague_intent", "confirmation_bias"}): (
        "vague_validation_seek",
        0.70,
        "clarify",
        "User wants validation but hasn't specified what for. "
        "Clarify the actual claim before agreeing or disagreeing with it.",
    ),
    frozenset({"framing_effect", "dunning_kruger"}): (
        "expert_frame",
        0.78,
        "reframe",
        "User has framed the question with assumed expertise. "
        "The frame itself reveals the knowledge gap. Reframe without embarrassing them.",
    ),
    frozenset({"anchoring", "confirmation_bias"}): (
        "anchored_validation",
        0.83,
        "challenge",
        "Wrong anchor + seeking confirmation of it. "
        "Agreeing would compound the error. Surface the anchor gently.",
    ),
}

# ── Profile dataclass ─────────────────────────────────────────────────────────

@dataclass
class CoOccurrenceProfile:
    biases:           list[str]      # all active biases
    primary:          str            # highest scoring
    secondary:        Optional[str]  # second highest (if above threshold)
    interaction:      Optional[str]  # named interaction effect
    combined_score:   float          # aggregate difficulty 0-1
    routing_override: Optional[str]  # comply|reframe|clarify|challenge|None
    notes:            str            # description of the interaction
    raw_scores:       dict           = field(default_factory=dict)

    @property
    def is_compound(self) -> bool:
        return self.secondary is not None

    @property
    def is_high_difficulty(self) -> bool:
        return self.combined_score >= 0.75

    def to_prompt_fragment(self) -> str:
        parts = [f"Detected bias pattern: {self.primary}"]
        if self.secondary:
            parts.append(f"Co-occurring bias: {self.secondary}")
        if self.interaction:
            parts.append(f"Interaction effect: {self.interaction}")
        if self.notes:
            parts.append(f"Routing note: {self.notes}")
        if self.routing_override:
            parts.append(f"Recommended route: {self.routing_override}")
        return "\n".join(parts)


# ── Detector ──────────────────────────────────────────────────────────────────

class CoOccurrenceDetector:
    """
    Analyses a dict of {bias_label: score} and produces a CoOccurrenceProfile.

    NOTE: The bias classifiers (SemanticClassifier, HybridClassifier) return
    only the top label. To get full score distributions, call classify_all()
    which is added as an extension method at the bottom of this file.
    """

    def __init__(
        self,
        active_threshold:    float = ACTIVE_THRESHOLD,
        secondary_threshold: float = SECONDARY_THRESHOLD,
    ):
        self.active_t    = active_threshold
        self.secondary_t = secondary_threshold

    def analyse(self, bias_scores: dict[str, float]) -> CoOccurrenceProfile:
        # Filter to active biases
        active = {
            k: v for k, v in bias_scores.items()
            if v >= self.active_t and k != "unknown"
        }

        if not active:
            # No signal
            return CoOccurrenceProfile(
                biases=[], primary="unknown", secondary=None,
                interaction=None, combined_score=0.20,
                routing_override=None,
                notes="No bias signal detected above threshold.",
                raw_scores=bias_scores,
            )

        # Rank
        ranked = sorted(active.items(), key=lambda x: x[1], reverse=True)
        primary   = ranked[0][0]
        secondary = ranked[1][0] if len(ranked) > 1 and ranked[1][1] >= self.secondary_t else None

        # Interaction lookup
        interaction_name  = None
        interaction_score = None
        routing_override  = None
        notes             = ""

        if secondary:
            key = frozenset({primary, secondary})
            if key in _INTERACTIONS:
                interaction_name, interaction_score, routing_override, notes = _INTERACTIONS[key]

        # Combined difficulty score
        if interaction_score is not None:
            combined = interaction_score
        elif secondary:
            # Two active biases with no known interaction — average + penalty
            top_two = sum(v for _, v in ranked[:2]) / 2
            combined = min(0.95, top_two + 0.10)
        else:
            combined = ranked[0][1]

        # If no interaction but single strong bias — derive routing from bias
        if routing_override is None:
            routing_override = _default_route(primary, ranked[0][1])

        if not notes and secondary:
            notes = (
                f"Co-occurrence of {primary.replace('_',' ')} and "
                f"{secondary.replace('_',' ')} detected. "
                f"No named interaction — treat as compounded {primary.replace('_',' ')}."
            )
        elif not notes:
            notes = f"Single bias active: {primary.replace('_',' ')}."

        return CoOccurrenceProfile(
            biases           = [k for k, _ in ranked],
            primary          = primary,
            secondary        = secondary,
            interaction      = interaction_name,
            combined_score   = round(combined, 3),
            routing_override = routing_override,
            notes            = notes,
            raw_scores       = bias_scores,
        )

    def from_classifier_output(
        self,
        top_label: str,
        top_conf:  float,
        text:      str,
        classifier = None,
    ) -> CoOccurrenceProfile:
        """
        Convenience: build a scores dict from a single classifier output.
        If `classifier` is provided and has classify_all(), use full scores.
        Otherwise build a sparse dict with the top label.
        """
        if classifier and hasattr(classifier, "classify_all"):
            scores = classifier.classify_all(text)
        else:
            # Sparse — only top label has a real score
            from bias_classifier import _keyword_scores
            kw = _keyword_scores(text)
            # Blend: top classifier label gets top_conf; rest come from keyword layer
            scores = {k: v * 0.5 for k, v in kw.items()}
            scores[top_label] = max(scores.get(top_label, 0), top_conf)

        return self.analyse(scores)


def _default_route(bias: str, score: float) -> str:
    _routes = {
        "anchoring":         "challenge",
        "vague_intent":      "clarify",
        "confirmation_bias": "challenge",
        "dunning_kruger":    "challenge",
        "framing_effect":    "reframe",
        "clear_intent":      "comply",
        "unknown":           "clarify",
    }
    return _routes.get(bias, "clarify")


# ── classify_all() extension ──────────────────────────────────────────────────
# Monkey-patch onto HybridClassifier so CoOccurrenceDetector can get full scores.
# Call after importing both modules.

def _patch_classifiers():
    """
    Adds classify_all(text) -> dict[str, float] to HybridClassifier and SemanticClassifier.
    classify_all returns a score for every bias label, not just the top one.
    """
    try:
        from bias_classifier import HybridClassifier, SemanticClassifier, _keyword_scores, BIAS_LABELS, _cosine, _embed

        def _hybrid_classify_all(self, text: str) -> dict[str, float]:
            kw = _keyword_scores(text)
            if self._semantic is None or not self._ollama_ok:
                return kw
            vec = _embed(text)
            sem_scores = {
                label: _cosine(vec, centroid)
                for label, centroid in self._semantic._centroids.items()
            }
            return {
                label: self.sw * sem_scores.get(label, 0.0) + self.kw * kw.get(label, 0.0)
                for label in BIAS_LABELS
            }

        def _semantic_classify_all(self, text: str) -> dict[str, float]:
            vec = _embed(text)
            return {
                label: _cosine(vec, centroid)
                for label, centroid in self._centroids.items()
            }

        HybridClassifier.classify_all  = _hybrid_classify_all
        SemanticClassifier.classify_all = _semantic_classify_all

    except ImportError:
        pass   # bias_classifier not available — patch silently skipped

_patch_classifiers()
