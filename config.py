import json
import os
from pathlib import Path

CONFIG_DIR = Path(os.environ.get("APPDATA", str(Path.home()))) / "VoiceTyper"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULTS = {
    "cleaner_provider": "claude",
    "anthropic_api_key": "",
    "gemini_api_key": "",
    "whisper_model": "small",
    "hotkey": "f9",
    "language": "auto",
}

PROVIDER_ENV_VAR = {
    "claude": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
}

PROVIDER_CONFIG_FIELD = {
    "claude": "anthropic_api_key",
    "gemini": "gemini_api_key",
}


def provider_chosen():
    """Whether the user has ever explicitly picked/confirmed a cleaner provider."""
    if not CONFIG_FILE.exists():
        return False
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return "cleaner_provider" in data


def load():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        save(DEFAULTS)
        return dict(DEFAULTS)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    merged = dict(DEFAULTS)
    merged.update(data)
    return merged


def save(cfg):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def get_api_key(provider):
    env_key = os.environ.get(PROVIDER_ENV_VAR[provider])
    if env_key:
        return env_key
    return load().get(PROVIDER_CONFIG_FIELD[provider], "")


def save_api_key(provider, key):
    cfg = load()
    cfg[PROVIDER_CONFIG_FIELD[provider]] = key
    save(cfg)
