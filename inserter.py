from pynput.keyboard import Controller

_keyboard = Controller()


def insert_text(text):
    if not text:
        return
    # pynput's type() sends real Unicode characters via SendInput, so it works
    # regardless of the active keyboard layout/IME in the focused app.
    _keyboard.type(text)
