# Voice Typer

Windows 背景小工具：按熱鍵說話，語音轉文字後用 AI 清理格式，自動貼到目前游標所在的欄位（任何 App 都通用）。
文字清理引擎可在 Claude 和 Gemini 之間切換（系統匣選單即可切換，不用重開程式）。

## 安裝與執行

1. 安裝相依套件：
   ```
   pip install -r requirements.txt
   ```
2. 直接執行：
   ```
   python main.py
   ```
   或打包成獨立 exe（見下方）。

第一次執行（或第一次切換到某個引擎）會跳出視窗要求貼上對應的 API key：

- **Claude**：在 https://console.anthropic.com 建立，需要付費儲值
- **Gemini**：在 https://aistudio.google.com/apikey 建立，有免費額度（Flash 模型，每天最多 1000 次請求）

Key 會存在 `%APPDATA%\VoiceTyper\config.json`，之後不會再問，除非你清掉那個欄位或切換到還沒設定過 key 的引擎。

## 使用方式

- 系統匣（右下角）會出現一個灰色圓點圖示，代表待命中。
- 按 **F9**（預設熱鍵，可在 `%APPDATA%\VoiceTyper\config.json` 的 `"hotkey"` 欄位改成其他鍵，例如 `"ctrl+alt+space"`）開始錄音，圖示變紅。
- 再按一次 F9 結束錄音，圖示變黃（處理中：語音辨識 + AI 清理文字），完成後自動打字貼到目前游標位置，圖示變回灰色。
- 右鍵點系統匣圖示：
  - 「文字清理引擎」子選單可以即時切換 Claude / Gemini，選了沒設過 key 的引擎會跳出視窗要你貼 key
  - 「結束」可以關閉程式

## 打包成安裝檔（可獨立執行的 .exe）

```
build.bat
```

完成後執行檔在 `dist\VoiceTyper.exe`，可以直接複製到任何 Windows 電腦執行，不需要安裝 Python。
第一次執行時 faster-whisper 仍會自動下載語音模型（約 200-500MB，取決於模型大小），需要網路連線一次；
之後就完全離線可用。

## 設定選項（`%APPDATA%\VoiceTyper\config.json`）

| 欄位 | 說明 |
|---|---|
| `cleaner_provider` | 目前使用的文字清理引擎：`claude`（預設）或 `gemini`，也可以直接在系統匣選單切換 |
| `anthropic_api_key` | Claude API key |
| `gemini_api_key` | Gemini API key |
| `whisper_model` | Whisper 模型大小：`tiny` / `base` / `small`（預設）/ `medium` / `large-v3`，越大越準但越慢 |
| `hotkey` | 觸發錄音的熱鍵，語法見 [keyboard 套件文件](https://github.com/boppreh/keyboard) |
| `language` | 語音語言，預設 `auto` 自動偵測，也可指定 `zh`、`en` 等 |

## 已知限制

- 這不是嚴格意義的「輸入法」（不會出現在 Windows 語言列），而是全域熱鍵 + 自動打字，效果類似但實作簡單很多。
- 若目標視窗是以系統管理員權限執行的程式，全域熱鍵可能偵測不到，需要以系統管理員身分執行 VoiceTyper。
- 需要麥克風權限（Windows 設定 → 隱私權 → 麥克風）。


之後不管是這台電腦還是任何其他電腦，只要：
git clone https://github.com/Autoanima/voice-typer.git
把這行丟給AI，AI就能直接接手繼續改（新開一個 Claude Code session 在那個資料夾裡工作即可）。
