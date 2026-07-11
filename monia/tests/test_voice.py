from monia import voice


def test_is_available_false_without_termux_api():
    # this sandbox has no termux-tts-speak binary
    assert voice.is_available() is False


def test_speak_returns_false_when_unavailable():
    assert voice.speak("bonjour") is False


def test_is_stt_available_false_without_termux_api():
    # this sandbox has no termux-speech-to-text binary either
    assert voice.is_stt_available() is False


def test_listen_returns_empty_string_when_unavailable():
    assert voice.listen() == ""
