from faster_whisper import WhisperModel


class Transcriber:
    def __init__(self, model_size="small"):
        # CPU + int8 keeps this usable without a GPU; swap to "cuda"/"float16" if available.
        self._model = WhisperModel(model_size, device="cpu", compute_type="int8")

    def transcribe(self, audio, language="auto"):
        lang = None if language == "auto" else language
        segments, _ = self._model.transcribe(audio, language=lang, vad_filter=True)
        return "".join(segment.text for segment in segments).strip()
