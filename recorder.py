import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000


class Recorder:
    def __init__(self):
        self._chunks = []
        self._stream = None

    def start(self):
        self._chunks = []
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            callback=self._callback,
        )
        self._stream.start()

    def _callback(self, indata, frames, time_info, status):
        self._chunks.append(indata.copy())

    def stop(self):
        if self._stream is None:
            return np.zeros((0,), dtype="float32")
        self._stream.stop()
        self._stream.close()
        self._stream = None
        if not self._chunks:
            return np.zeros((0,), dtype="float32")
        audio = np.concatenate(self._chunks, axis=0).flatten()
        self._chunks = []
        return audio
