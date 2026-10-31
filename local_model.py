# local_model.py - Talks to a local AI model (Gemma) through Ollama on this computer.
# Optional: if Ollama isn't running or the answer is broken, we print a plain message
# and return None, so the caller can fall back. Nothing is sent to the internet.

import json

import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma3:4b"
TIMEOUT_SECONDS = 120


# Sends one prompt to the local model and asks for a JSON answer.
# In: prompt text. Out: the answer turned into Python (a list or dictionary), or None.
def ask_model(prompt):
    body = {"model": MODEL, "prompt": prompt, "stream": False, "format": "json"}
    try:
        response = requests.post(OLLAMA_URL, json=body, timeout=TIMEOUT_SECONDS)
    except requests.RequestException:
        print("Ollama is not running (or took too long), so the AI step is skipped.")
        return None
    if response.status_code != 200:
        print("Ollama said error " + str(response.status_code)
              + ". Is the model installed? Try: ollama pull " + MODEL)
        return None
    try:
        return json.loads(response.json()["response"])
    except (ValueError, KeyError):
        print("The model's answer wasn't valid JSON, so it is ignored.")
        return None


# Turns the model's answer into a list of strings, if it can.
# Models sometimes wrap the list, like {"checks": [...]}, so we unwrap one level.
# In: whatever ask_model returned. Out: a list of strings, or None if it isn't one.
def as_string_list(answer):
    if isinstance(answer, dict) and len(answer) == 1:
        answer = list(answer.values())[0]
    if not isinstance(answer, list):
        return None
    for value in answer:
        if not isinstance(value, str):
            return None
    return answer
