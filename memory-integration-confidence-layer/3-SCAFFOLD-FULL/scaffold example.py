"""
scaffold_example.py
───────────────────
Full pipeline: all six modules wired together.

    User input
        ↓
    [IntentExtractor]      – what do they actually want?
        ↓
    [BiasClassifier]       – how are they asking?
        ↓
    [CoOccurrenceDetector] – are multiple biases compounding?
        ↓
    [SessionTracker]       – is this a repeat? are they drifting? frustrated?
        ↓
    [ConfidenceFloor]      – do we have enough signal to produce anything?
        ↓
    [BayesianMiddleware]   – route decision + system prompt injection
        ↓
    Ollama LLM
        ↓
    [OutcomeFeedback]      – infer outcome from next user message
        ↓
    MemoryStore write-back
"""

import json
import requests
from bayesian_middleware  import BayesianMiddleware
from intent_extractor    import IntentExtractor
from outcome_feedback    import OutcomeFeedback
from session_tracker     import SessionTracker
from confidence_floor    import ConfidenceFloor
from bias_cooccurrence   import CoOccurrenceDetector
from bias_classifier     import HybridClassifier

OLLAMA_URL   = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "mistral"


def call_ollama(system_prompt: str, user_message: str, history: list[dict]) -> str:
    messages = [{"role": "system", "content": system_prompt}]
    messages += history
    messages.append({"role": "user", "content": user_message})

    resp = requests.post(OLLAMA_URL, json={
        "model":    OLLAMA_MODEL,
        "messages": messages,
        "stream":   False,
    })
    resp.raise_for_status()
    return resp.json()["message"]["content"]


def run_agent(user_id: str = "e404"):
    # ── Module init ──────────────────────────────────────────────────────────
    mw         = BayesianMiddleware(user_id=user_id)
    ix         = IntentExtractor()
    fb         = OutcomeFeedback()
    tracker    = SessionTracker()
    floor      = ConfidenceFloor()
    codetector = CoOccurrenceDetector()
    classifier = HybridClassifier(warm=True)

    history          = []
    last_user_msg    = ""
    last_ai_response = ""
    last_outcome     = "right_partial"

    print(f"\n── Full Scaffold Agent (user: {user_id}) ──")
    print("Commands: 'quit' | 'snapshot' | 'eval' | 'reset'\n")

    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue

        if user_input.lower() == "quit":
            break

        if user_input.lower() == "snapshot":
            snap = mw.snapshot()
            print(json.dumps(snap, indent=2))
            print("Session:", json.dumps(tracker.session_summary, indent=2))
            continue

        if user_input.lower() == "reset":
            mw.reset(); ix.reset(); fb.reset(); tracker.reset()
            history.clear()
            print("[scaffold] All state reset.\n")
            continue

        if user_input.lower() == "eval":
            from eval_harness import EvalSuite, EvalRunner
            report = EvalRunner().classifier_eval(EvalSuite.baseline(), classifier)
            report.print_summary()
            continue

        # ── 1. Outcome feedback from previous turn ───────────────────────────
        if last_user_msg and last_ai_response:
            signal  = fb.infer(last_user_msg, last_ai_response, user_input)
            outcome = mw.post_process(last_ai_response, mw._last_decision, signal.to_outcome_key())
            last_outcome = outcome
            print(f"[feedback] {signal.outcome} (conf={signal.confidence:.2f}) — {signal.reason}")

        # ── 2. Intent extraction ─────────────────────────────────────────────
        intent = ix.extract(user_input, history)
        print(f"[intent] goal='{intent.goal[:60]}' conf={intent.confidence:.2f} complete={intent.is_complete()}")

        # ── 3. Bias classification + co-occurrence ───────────────────────────
        bias_scores = classifier.classify_all(user_input) if hasattr(classifier, "classify_all") else {}
        bias, conf  = classifier.classify(user_input)
        profile     = codetector.analyse(bias_scores) if bias_scores else codetector.from_classifier_output(bias, conf, user_input, classifier)

        print(f"[bias] primary={bias} conf={conf:.2f}", end="")
        if profile.secondary:
            print(f" secondary={profile.secondary} interaction={profile.interaction}", end="")
        print()

        # ── 4. Session state ─────────────────────────────────────────────────
        session = tracker.update(user_input, bias, last_outcome)
        if session.flags:
            print(f"[session] flags={session.flags} recommendation={session.recommendation}")

        # ── 5. Confidence floor ──────────────────────────────────────────────
        snap       = mw.snapshot()
        floor_dec  = floor.evaluate(
            ai_prior          = snap["ai_prior"],
            intent_confidence = intent.confidence,
            bias              = bias,
            session_flags     = session.flags,
            recent_hit_rate   = snap["hit_rate"],
        )
        print(f"[floor] mode={floor_dec.mode} conf={floor_dec.effective_conf:.3f}")

        if floor_dec.should_refuse:
            print(f"\nAgent: {floor_dec.refusal_reason}\n")
            last_user_msg    = user_input
            last_ai_response = floor_dec.refusal_reason
            history.append({"role": "user",      "content": user_input})
            history.append({"role": "assistant", "content": floor_dec.refusal_reason})
            continue

        # ── 6. Middleware routing ─────────────────────────────────────────────
        decision = mw.pre_process(user_input)

        # Session recommendation can override route
        if session.recommendation and session.recommendation != "summarise":
            decision.route = session.recommendation

        # Co-occurrence can override route
        if profile.routing_override and profile.is_high_difficulty:
            decision.route = profile.routing_override

        # Floor clarify prompt injection
        if floor_dec.should_clarify:
            decision.system_injection += f"\n\nIMPORTANT: {floor_dec.clarify_prompt}"

        # Intent injection
        decision.system_injection += f"\n\nINTENT CONTEXT:\n{intent.to_prompt_fragment()}"

        # Co-occurrence injection
        if profile.is_compound:
            decision.system_injection += f"\n\nBIAS CONTEXT:\n{profile.to_prompt_fragment()}"

        # Session injection
        decision.system_injection += f"\n\nSESSION CONTEXT:\n{session.to_prompt_fragment()}"

        print(f"[route] {decision.route} | bias={decision.bias_detected}")

        # Store last decision for post_process
        mw._last_decision = decision

        # ── 7. Call Ollama ────────────────────────────────────────────────────
        response = call_ollama(decision.system_injection, user_input, history)
        print(f"\nAgent: {response}\n")

        # ── 8. Update history ─────────────────────────────────────────────────
        last_user_msg    = user_input
        last_ai_response = response
        history.append({"role": "user",      "content": user_input})
        history.append({"role": "assistant", "content": response})
        if len(history) > 20:
            history = history[-20:]


if __name__ == "__main__":
    run_agent()
