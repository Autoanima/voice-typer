from anthropic import Anthropic

from prompts import SYSTEM_PROMPT


class ClaudeCleaner:
    provider = "claude"

    def __init__(self, api_key, model="claude-haiku-4-5-20251001"):
        self._client = Anthropic(api_key=api_key)
        self._model = model

    def clean(self, raw_text):
        if not raw_text.strip():
            return ""
        response = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": raw_text}],
        )
        return "".join(
            block.text for block in response.content if block.type == "text"
        ).strip()
