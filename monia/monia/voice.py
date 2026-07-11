"""Text-to-speech via Termux:API's `termux-tts-speak`. Requires the
Termux:API app (separate from Termux itself) to be installed for the
command to exist -- voice is optional everywhere it's used, never required.
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
