# agent_hydra_control.py
# Phase 7: Hydra-based Agent Control + Multi-Agent Playground + Routing Memory

import os
import datetime
import subprocess
from omegaconf import OmegaConf

# === Load Hydra-style config ===
config = OmegaConf.load("config.yaml")

OLLAMA_MODELS = config.models

LOG_DIR = os.path.join(os.getcwd(), config.logging.log_dir)
os.makedirs(LOG_DIR, exist_ok=True)

SESSION_FILE = os.path.join(
    LOG_DIR, f"session_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
)

CONTEXT_MEMORY = []  # Stores recent user prompts + agent responses

# === Helper: Log to file ===
def log(message):
    with open(SESSION_FILE, "a") as f:
        f.write(message + "\n")

# === Helper: Ask specific Ollama model ===
def ask_ollama(model: str, prompt: str) -> str:
    try:
        result = subprocess.run([
            "ollama", "run", model
        ], input=prompt.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)

        output = result.stdout.decode()
        log(f"\n[{model.upper()} RESPONSE]\n{output}")
        return output

    except Exception as e:
        log(f"[ERROR with model {model}] {str(e)}")
        return f"[ERROR] {str(e)}"

# === Advanced routing based on memory/context ===
def route_prompt(prompt: str) -> str:
    word_count = len(prompt.split())
    keywords = ["analyse", "compare", "debate", "strategy", "research"]
    deep_thought = any(k in prompt.lower() for k in keywords)

    if word_count < 15:
        model = OLLAMA_MODELS.fast
    elif deep_thought:
        model = OLLAMA_MODELS.deep_b
    else:
        model = OLLAMA_MODELS.deep_a

    CONTEXT_MEMORY.append({"prompt": prompt, "model": model})
    if len(CONTEXT_MEMORY) > 10:
        CONTEXT_MEMORY.pop(0)

    log(f"\n[ROUTED TO: {model.upper()}]\nPrompt: {prompt}")
    return ask_ollama(model, prompt)

# === MAIN LOOP ===
if __name__ == "__main__":
    print("\U0001F916 HYDRA AGENT CONTROL ONLINE — Type 'exit' to quit")
    log("[SESSION START]")

    while True:
        user_input = input("\nYou: ")

        if user_input.lower() in ["exit", "quit"]:
            print("Exiting. Goodbye!")
            log("[SESSION ENDED]")
            break

        log(f"\n[USER INPUT]\n{user_input}")
        response = route_prompt(user_input)
        print(f"\nAgent: {response.strip()}")
