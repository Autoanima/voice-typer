import ctypes
import logging
import os
import subprocess
import threading
from pathlib import Path

import keyboard
import pystray
from PIL import Image, ImageDraw

import config
from cleaner import PROVIDER_LABELS, build_cleaner
from inserter import insert_text
from recorder import Recorder
from transcriber import Transcriber

LOG_FILE = Path(os.environ.get("APPDATA", str(Path.home()))) / "VoiceTyper" / "voicetyper.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=str(LOG_FILE),
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s [%(threadName)s] %(levelname)s %(message)s",
)
log = logging.getLogger("voice-typer")


def _log_thread_exceptions(args):
    log.error(
        "unhandled exception in thread %s",
        args.thread.name if args.thread else "?",
        exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
    )


threading.excepthook = _log_thread_exceptions

STATE_COLORS = {
    "idle": (90, 90, 90),
    "recording": (220, 50, 50),
    "processing": (230, 170, 40),
}

PROVIDER_PROMPT_URL = {
    "claude": "https://console.anthropic.com",
    "gemini": "https://aistudio.google.com/apikey",
}

MB_YESNO = 0x00000004
MB_ICONQUESTION = 0x00000020
MB_TOPMOST = 0x00040000
IDYES = 6

state_lock = threading.Lock()
current_state = "idle"
icon = None
recorder = Recorder()
transcriber = None
cleaner = None
cfg = None


def make_icon_image(color):
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((8, 8, 56, 56), fill=color + (255,))
    return img


def set_state(new_state):
    global current_state
    with state_lock:
        current_state = new_state
    if icon:
        icon.icon = make_icon_image(STATE_COLORS[new_state])
        icon.title = f"Voice Typer - {new_state}"


def native_confirm(title, message):
    """Native MessageBox - safe to call from any thread, always foreground."""
    result = ctypes.windll.user32.MessageBoxW(
        0, message, title, MB_YESNO | MB_ICONQUESTION | MB_TOPMOST
    )
    return result == IDYES


def native_input(title, prompt):
    """Native WinForms InputBox via PowerShell.

    Earlier attempts used custom Tkinter Toplevel windows created from a
    pystray callback thread. Those had two compounding problems: Tk isn't
    reliably thread-safe to poke from a worker thread, and even once routed
    onto the Tk mainloop thread, a background process's window doesn't
    reliably get pulled into the foreground on Windows, so it could sit open
    and unnoticed - and since dialogs were serviced one at a time, an
    unnoticed dialog silently blocked every request queued after it.

    Spawning a real WinForms InputBox in its own process sidesteps all of
    that: it's a brand-new foreground process, so Windows gives it focus
    normally, and each call is fully independent (no shared queue to jam).
    """
    ps_prompt = prompt.replace('"', '`"').replace("`", "``")
    ps_title = title.replace('"', '`"').replace("`", "``")
    script = (
        "Add-Type -AssemblyName Microsoft.VisualBasic; "
        f'[Microsoft.VisualBasic.Interaction]::InputBox("{ps_prompt}", "{ps_title}", "")'
    )
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True,
            text=True,
            timeout=180,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return result.stdout.strip()
    except Exception:
        log.exception("native_input failed")
        return ""


def prompt_for_provider():
    log.info("prompting for provider choice")
    if native_confirm(
        "Voice Typer 設定",
        "請選擇文字清理要用哪個 AI：\n\n「是」= Claude（付費 API）\n「否」= Gemini（有免費額度）",
    ):
        return "claude"
    return "gemini"


def prompt_for_key(provider):
    label = PROVIDER_LABELS[provider]
    url = PROVIDER_PROMPT_URL[provider]
    log.info("prompting for %s key", provider)
    key = native_input(
        "Voice Typer 設定",
        f"請貼上 {label} 的 API key\n(可在 {url} 取得)：",
    )
    key = (key or "").strip()
    log.info("got key input, non-empty=%s", bool(key))
    if key:
        config.save_api_key(provider, key)
    return key


def ensure_provider_key(provider):
    key = config.get_api_key(provider)
    if key:
        return key
    return prompt_for_key(provider)


def switch_provider(provider):
    global cleaner, cfg
    log.info("switch_provider(%s) called", provider)
    try:
        key = ensure_provider_key(provider)
        if not key:
            return
        try:
            new_cleaner = build_cleaner(provider, key)
        except Exception:
            log.exception("build_cleaner(%s) failed", provider)
            return
        cleaner = new_cleaner
        cfg["cleaner_provider"] = provider
        config.save(cfg)
        if icon:
            icon.update_menu()
        log.info("switched cleaner engine to %s", provider)
    except Exception:
        log.exception("switch_provider(%s) crashed", provider)


def toggle_recording():
    with state_lock:
        state = current_state
    if state == "idle":
        recorder.start()
        set_state("recording")
    elif state == "recording":
        set_state("processing")
        threading.Thread(target=process_recording, daemon=True).start()


def process_recording():
    audio = recorder.stop()
    try:
        if audio.size == 0:
            return
        raw_text = transcriber.transcribe(audio, language=cfg.get("language", "auto"))
        if not raw_text:
            return
        cleaned = cleaner.clean(raw_text)
        insert_text(cleaned or raw_text)
    except Exception:
        log.exception("process_recording failed")
    finally:
        set_state("idle")


def on_quit(icon_obj, item):
    log.info("on_quit called")
    keyboard.unhook_all_hotkeys()
    icon_obj.stop()


def is_provider(provider):
    return lambda item: cfg.get("cleaner_provider") == provider


def build_menu():
    provider_items = [
        pystray.MenuItem(
            label,
            (lambda p: lambda: switch_provider(p))(provider),
            checked=is_provider(provider),
            radio=True,
        )
        for provider, label in PROVIDER_LABELS.items()
    ]
    return pystray.Menu(
        pystray.MenuItem("按一下開始/結束錄音", lambda: None, enabled=False),
        pystray.MenuItem(lambda item: f"熱鍵：{cfg.get('hotkey')}", lambda: None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("文字清理引擎", pystray.Menu(*provider_items)),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("結束", on_quit),
    )


def main():
    global icon, transcriber, cleaner, cfg

    log.info("=== voice-typer starting ===")

    need_provider_pick = not config.provider_chosen()
    cfg = config.load()

    if need_provider_pick:
        chosen = prompt_for_provider()
        cfg["cleaner_provider"] = chosen
        config.save(cfg)

    provider = cfg.get("cleaner_provider", "claude")

    api_key = ensure_provider_key(provider)
    if not api_key:
        log.info("沒有提供 API key，結束程式。")
        return

    icon = pystray.Icon("voice-typer", make_icon_image(STATE_COLORS["idle"]), "Voice Typer", build_menu())

    log.info("正在載入語音辨識模型...")
    transcriber = Transcriber(model_size=cfg.get("whisper_model", "small"))
    cleaner = build_cleaner(provider, api_key)
    log.info("準備完成。按下熱鍵開始/結束錄音：%s", cfg.get("hotkey", "f9"))
    log.info("文字清理引擎：%s", PROVIDER_LABELS[provider])

    keyboard.add_hotkey(cfg.get("hotkey", "f9"), toggle_recording)

    log.info("tray icon starting")
    icon.run()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log.exception("main() crashed")
        raise
