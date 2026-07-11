"""Text-to-speech and speech-to-text via Termux:API's `termux-tts-speak`
and `termux-speech-to-text`. Requires the Termux:API app (separate from
Termux itself) to be installed for the commands to exist -- voice is
optional everywhere it's used, never required.
"""

import shutil
import subprocess


def is_available() -> bool:
    return shutil.which("termux-tts-speak") is not None


def speak(text: str) -> bool:
    """Returns False (silently) if termux-tts-speak isn't installed,
    True if the command was invoked."""
    if not is_available():
        return False
    subprocess.run(["termux-tts-speak", text], check=False)
    return True


def is_stt_available() -> bool:
    return shutil.which("termux-speech-to-text") is not None


def listen(timeout: float = 30.0) -> str:
    """Runs termux-speech-to-text (opens the device's speech recognizer)
    and returns the recognized text, stripped. Returns "" if the command
    is unavailable, times out, or nothing was understood -- callers treat
    that as "try again", never as an error."""
    if not is_stt_available():
        return ""
    try:
        result = subprocess.run(
            ["termux-speech-to-text"],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return ""
    return result.stdout.strip()
