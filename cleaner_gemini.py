from google import genai
from google.genai import types

from prompts import SYSTEM_PROMPT


class GeminiCleaner:
    provider = "gemini"

    def __init__(self, api_key, model="gemini-flash-latest"):
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def clean(self, raw_text):
        if not raw_text.strip():
            return ""
        response = self._client.models.generate_content(
            model=self._model,
            contents=raw_text,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
        )
        return (response.text or "").strip()
