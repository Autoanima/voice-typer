@echo off
pyinstaller --noconfirm --onefile --windowed --name VoiceTyper ^
  --collect-all faster_whisper ^
  --collect-all ctranslate2 ^
  --collect-all google.genai ^
  --collect-all google.auth ^
  main.py
echo.
echo Build complete: dist\VoiceTyper.exe
