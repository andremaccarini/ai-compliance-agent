# llm_client.py — lightweight HTTP client for local Ollama LLM inference

import requests, yaml

# ---------------------------------------------------------------------------
# Load model configuration from YAML
# ---------------------------------------------------------------------------

CFG = yaml.safe_load(open('configs/config.yaml', 'r'))
OLLAMA_HOST = CFG['llm']['host']
OLLAMA_MODEL = CFG['llm']['model']

def generate(prompt: str, temperature: float = 0.2, system: str = None) -> str:

    """
    Send a text prompt to the local Ollama API and return the model's response.

    Args:
        prompt:      user or system prompt to generate text for.
        temperature: sampling temperature (0.0 = deterministic, >0 = more creative).
        system:      optional system instruction defining role/persona of the model.

    Returns:
        str: generated text output from the model.

    Notes:
        - This function uses Ollama’s REST endpoint `/api/generate`.
        - The request is synchronous and non-streaming (`stream=False`).
        - Timeout set to 120s to handle larger prompts safely.
    """

    # Prepare request payload for Ollama API
    payload = {
        'model': OLLAMA_MODEL,
        'prompt': prompt,
        'options': {'temperature': temperature},
        'stream': False
    }

    # Add system message if provided
    if system:
        payload['system'] = system

    # Make POST request to local Ollama server
    r = requests.post(f"{OLLAMA_HOST}/api/generate", json=payload, timeout=120)
    r.raise_for_status()

    # Parse JSON response and extract model text
    data = r.json()
    return data.get('response', '')
