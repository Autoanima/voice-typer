from cleaner_claude import ClaudeCleaner
from cleaner_gemini import GeminiCleaner

PROVIDERS = {
    "claude": ClaudeCleaner,
    "gemini": GeminiCleaner,
}

PROVIDER_LABELS = {
    "claude": "Claude（付費 API）",
    "gemini": "Gemini（有免費額度）",
}


def build_cleaner(provider, api_key):
    cls = PROVIDERS.get(provider)
    if cls is None:
        raise ValueError(f"unknown cleaner provider: {provider}")
    return cls(api_key=api_key)
