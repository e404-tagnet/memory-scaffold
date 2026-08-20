"""
eval_harness.py
───────────────
Ground truth evaluation for the scaffold system.
Measures whether the routing decisions and classifier outputs
are actually correct — not just plausible.

Components:
    EvalCase        – a single labelled test case
    EvalSuite       – a collection of cases
    EvalRunner      – runs the suite against live classifiers/middleware
    EvalReport      – results with per-component breakdown

Provides three eval modes:
    1. classifier_eval  – bias classifier accuracy against labelled inputs
    2. routing_eval     – middleware routing decisions against expected routes
    3. end_to_end_eval  – full pipeline: input → decision → outcome match

Usage:
    from eval_harness import EvalSuite, EvalRunner

    suite  = EvalSuite.load("eval_cases.json")
    runner = EvalRunner()

    report = runner.classifier_eval(suite)
    report.print_summary()
    report.save("eval_results.json")

    # Or run against a specific classifier:
    from bias_classifier import LLMClassifier
    report = runner.classifier_eval(suite, classifier=LLMClassifier())

Add your own cases as you run real sessions:
    suite.add(EvalCase(
        input         = "Just make something that works",
        expected_bias = "vague_intent",
        expected_route= "clarify",
        notes         = "From session 2026-01-15, user was stuck for 4 turns",
    ))
    suite.save("eval_cases.json")
"""

from __future__ import annotations
import json
import time
import statistics
from dataclasses import dataclass, field, asdict
from typing import Optional, Callable
from pathlib import Path

# ── EvalCase ──────────────────────────────────────────────────────────────────

@dataclass
class EvalCase:
    input:          str
    expected_bias:  str
    expected_route: str                    = ""      # comply|reframe|clarify|challenge
    expected_outcome: str                  = ""      # right_exact|right_partial|etc
    notes:          str                    = ""
    source:         str                    = "manual"   # manual|session|synthetic
    id:             str                    = field(default_factory=lambda: str(int(time.time()*1000)))

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "EvalCase":
        return cls(**d)


# ── Built-in baseline cases ───────────────────────────────────────────────────
# Extend this with real cases from your sessions.

BASELINE_CASES: list[EvalCase] = [
    # ── Anchoring ────────────────────────────────────────────────────────────
    EvalCase("The answer is definitely TCP, it has to be.", "anchoring", "challenge"),
    EvalCase("It must be a memory leak, I'm certain.", "anchoring", "challenge"),
    EvalCase("The price should be £500, that's the standard.", "anchoring", "challenge"),

    # ── Vague intent ─────────────────────────────────────────────────────────
    EvalCase("Just make something good.", "vague_intent", "clarify"),
    EvalCase("I don't know, whatever works.", "vague_intent", "clarify"),
    EvalCase("Something about data, maybe?", "vague_intent", "clarify"),
    EvalCase("Yeah just sort it out.", "vague_intent", "clarify"),

    # ── Confirmation bias ─────────────────────────────────────────────────────
    EvalCase("You agree Python is the best language, right?", "confirmation_bias", "challenge"),
    EvalCase("Tell me I'm right that microservices are always better.", "confirmation_bias", "challenge"),
    EvalCase("I knew it was their fault all along, prove it.", "confirmation_bias", "challenge"),

    # ── Dunning-Kruger ────────────────────────────────────────────────────────
    EvalCase("This is obviously simple, I don't understand why people struggle with it.", "dunning_kruger", "challenge"),
    EvalCase("How hard can it be? Just deploy to Kubernetes.", "dunning_kruger", "challenge"),
    EvalCase("I've read one article so I basically understand LLMs now.", "dunning_kruger", "challenge"),

    # ── Framing effect ────────────────────────────────────────────────────────
    EvalCase("Why is Python so much worse than Rust for everything?", "framing_effect", "reframe"),
    EvalCase("Shouldn't everyone always use tabs instead of spaces?", "framing_effect", "reframe"),
    EvalCase("Why don't people just follow best practices?", "framing_effect", "reframe"),

    # ── Clear intent ──────────────────────────────────────────────────────────
    EvalCase("Write a Python function that parses a UK postcode and returns the area code.", "clear_intent", "comply"),
    EvalCase("Refactor this to async/await keeping the same interface.", "clear_intent", "comply"),
    EvalCase("Explain TCP vs UDP in two paragraphs, no jargon.", "clear_intent", "comply"),

    # ── Unknown ───────────────────────────────────────────────────────────────
    EvalCase("Hello.", "unknown", "clarify"),
    EvalCase("Thanks.", "unknown", "comply"),
]


# ── EvalSuite ─────────────────────────────────────────────────────────────────

class EvalSuite:

    def __init__(self, cases: list[EvalCase] = None, name: str = "default"):
        self.name  = name
        self.cases: list[EvalCase] = cases or []

    def add(self, case: EvalCase):
        self.cases.append(case)

    def save(self, path: str):
        data = {
            "name":  self.name,
            "cases": [c.to_dict() for c in self.cases],
        }
        Path(path).write_text(json.dumps(data, indent=2))
        print(f"[EvalSuite] Saved {len(self.cases)} cases to {path}")

    @classmethod
    def load(cls, path: str) -> "EvalSuite":
        data  = json.loads(Path(path).read_text())
        cases = [EvalCase.from_dict(c) for c in data["cases"]]
        return cls(cases=cases, name=data.get("name", "loaded"))

    @classmethod
    def baseline(cls) -> "EvalSuite":
        return cls(cases=BASELINE_CASES, name="baseline")

    def filter_by_bias(self, bias: str) -> "EvalSuite":
        return EvalSuite(
            cases=[c for c in self.cases if c.expected_bias == bias],
            name=f"{self.name}:{bias}",
        )

    def __len__(self):
        return len(self.cases)


# ── EvalResult (per case) ─────────────────────────────────────────────────────

@dataclass
class EvalResult:
    case:              EvalCase
    predicted_bias:    str
    bias_confidence:   float
    predicted_route:   str          = ""
    bias_correct:      bool         = False
    route_correct:     bool         = False
    latency_ms:        float        = 0.0
    error:             str          = ""


# ── EvalReport ────────────────────────────────────────────────────────────────

@dataclass
class EvalReport:
    suite_name:    str
    classifier_name: str
    results:       list[EvalResult]
    timestamp:     float = field(default_factory=time.time)

    @property
    def bias_accuracy(self) -> float:
        if not self.results:
            return 0.0
        return sum(r.bias_correct for r in self.results) / len(self.results)

    @property
    def route_accuracy(self) -> float:
        graded = [r for r in self.results if r.predicted_route]
        if not graded:
            return 0.0
        return sum(r.route_correct for r in graded) / len(graded)

    @property
    def avg_confidence(self) -> float:
        return statistics.mean(r.bias_confidence for r in self.results) if self.results else 0.0

    @property
    def avg_latency_ms(self) -> float:
        return statistics.mean(r.latency_ms for r in self.results) if self.results else 0.0

    def per_bias_accuracy(self) -> dict[str, float]:
        from collections import defaultdict
        correct = defaultdict(int)
        total   = defaultdict(int)
        for r in self.results:
            total[r.case.expected_bias]   += 1
            correct[r.case.expected_bias] += int(r.bias_correct)
        return {
            bias: round(correct[bias] / total[bias], 3)
            for bias in total
        }

    def print_summary(self):
        print(f"\n── Eval Report: {self.suite_name} / {self.classifier_name} ──")
        print(f"  Cases:          {len(self.results)}")
        print(f"  Bias accuracy:  {self.bias_accuracy:.1%}")
        print(f"  Route accuracy: {self.route_accuracy:.1%}")
        print(f"  Avg confidence: {self.avg_confidence:.3f}")
        print(f"  Avg latency:    {self.avg_latency_ms:.0f}ms")
        print(f"\n  Per-bias accuracy:")
        for bias, acc in sorted(self.per_bias_accuracy().items()):
            bar = "█" * int(acc * 20)
            print(f"    {bias:<22} {acc:.0%}  {bar}")
        failures = [r for r in self.results if not r.bias_correct]
        if failures:
            print(f"\n  Failures ({len(failures)}):")
            for r in failures[:10]:
                print(f"    input:     {r.case.input[:60]}")
                print(f"    expected:  {r.case.expected_bias}")
                print(f"    predicted: {r.predicted_bias} ({r.bias_confidence:.2f})")
                if r.error:
                    print(f"    error:     {r.error}")
                print()

    def save(self, path: str):
        data = {
            "suite_name":     self.suite_name,
            "classifier":     self.classifier_name,
            "timestamp":      self.timestamp,
            "bias_accuracy":  self.bias_accuracy,
            "route_accuracy": self.route_accuracy,
            "avg_confidence": self.avg_confidence,
            "avg_latency_ms": self.avg_latency_ms,
            "per_bias":       self.per_bias_accuracy(),
            "results": [
                {
                    "input":          r.case.input,
                    "expected_bias":  r.case.expected_bias,
                    "predicted_bias": r.predicted_bias,
                    "bias_correct":   r.bias_correct,
                    "confidence":     r.bias_confidence,
                    "route_correct":  r.route_correct,
                    "latency_ms":     r.latency_ms,
                    "error":          r.error,
                }
                for r in self.results
            ],
        }
        Path(path).write_text(json.dumps(data, indent=2))
        print(f"[EvalReport] Saved to {path}")


# ── EvalRunner ────────────────────────────────────────────────────────────────

class EvalRunner:

    def classifier_eval(
        self,
        suite:      EvalSuite,
        classifier=None,
    ) -> EvalReport:
        """
        Evaluates bias classifier accuracy.
        Uses HybridClassifier by default.
        """
        if classifier is None:
            from bias_classifier import HybridClassifier
            classifier = HybridClassifier(warm=True)

        name    = type(classifier).__name__
        results = []

        for case in suite.cases:
            t0 = time.perf_counter()
            try:
                predicted_bias, conf = classifier.classify(case.input)
                error = ""
            except Exception as e:
                predicted_bias, conf, error = "unknown", 0.0, str(e)

            elapsed = (time.perf_counter() - t0) * 1000

            results.append(EvalResult(
                case            = case,
                predicted_bias  = predicted_bias,
                bias_confidence = round(conf, 3),
                bias_correct    = predicted_bias == case.expected_bias,
                latency_ms      = round(elapsed, 1),
                error           = error,
            ))

        return EvalReport(suite_name=suite.name, classifier_name=name, results=results)

    def routing_eval(
        self,
        suite:      EvalSuite,
        middleware=None,
    ) -> EvalReport:
        """
        Evaluates end-to-end routing decisions from bayesian_middleware.
        """
        if middleware is None:
            from bayesian_middleware import BayesianMiddleware
            middleware = BayesianMiddleware(user_id="eval_runner")

        name    = "BayesianMiddleware"
        results = []

        for case in suite.cases:
            if not case.expected_route:
                continue
            t0 = time.perf_counter()
            try:
                decision = middleware.pre_process(case.input)
                predicted_route  = decision.route
                predicted_bias   = decision.bias_detected
                conf             = decision.bias_confidence
                error            = ""
            except Exception as e:
                predicted_route = predicted_bias = "unknown"
                conf = 0.0
                error = str(e)

            elapsed = (time.perf_counter() - t0) * 1000

            results.append(EvalResult(
                case            = case,
                predicted_bias  = predicted_bias,
                bias_confidence = round(conf, 3),
                predicted_route = predicted_route,
                bias_correct    = predicted_bias == case.expected_bias,
                route_correct   = predicted_route == case.expected_route,
                latency_ms      = round(elapsed, 1),
                error           = error,
            ))

            # Reset middleware priors between cases to avoid bleed
            middleware.store.reset_user("eval_runner")

        return EvalReport(suite_name=suite.name, classifier_name=name, results=results)

    def compare(
        self,
        suite:       EvalSuite,
        classifiers: list,
    ) -> list[EvalReport]:
        """
        Run classifier_eval across multiple classifiers and print comparison.
        """
        reports = [self.classifier_eval(suite, c) for c in classifiers]
        print(f"\n── Classifier Comparison on '{suite.name}' ({len(suite)} cases) ──")
        print(f"  {'Classifier':<28} {'Bias Acc':>9} {'Avg Conf':>9} {'Avg ms':>8}")
        print(f"  {'─'*28} {'─'*9} {'─'*9} {'─'*8}")
        for r in reports:
            print(
                f"  {r.classifier_name:<28} "
                f"{r.bias_accuracy:>8.1%} "
                f"{r.avg_confidence:>9.3f} "
                f"{r.avg_latency_ms:>7.0f}ms"
            )
        return reports


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "hybrid"

    suite  = EvalSuite.baseline()
    runner = EvalRunner()

    if mode == "compare":
        from bias_classifier import HybridClassifier, LLMClassifier, SemanticClassifier
        runner.compare(suite, [
            HybridClassifier(),
            LLMClassifier(),
        ])
    elif mode == "routing":
        report = runner.routing_eval(suite)
        report.print_summary()
        report.save("eval_routing_results.json")
    elif mode == "llm":
        from bias_classifier import LLMClassifier
        report = runner.classifier_eval(suite, LLMClassifier())
        report.print_summary()
        report.save("eval_llm_results.json")
    else:
        report = runner.classifier_eval(suite)
        report.print_summary()
        report.save("eval_hybrid_results.json")
