import asyncio

import edge_tts

VOICES = {
    "bn": "bn-IN-TanishaaNeural",
    "te": "te-IN-ShrutiNeural",
    "hi": "hi-IN-SwaraNeural",
    "en": "en-IN-NeerjaNeural",
}

MAX_TEXT_CHARS = 500


class TtsError(RuntimeError):
    pass


async def _stream_all(text, voice):
    audio = b""
    async for chunk in edge_tts.Communicate(text, voice=voice).stream():
        if chunk["type"] == "audio":
            audio += chunk["data"]
    return audio


def synthesize(text, target_language="bn"):
    voice = VOICES.get((target_language or "bn").lower()[:2], VOICES["bn"])
    text = (text or "").strip()[:MAX_TEXT_CHARS]
    if not text:
        raise TtsError("No text provided for TTS")
    try:
        audio = asyncio.run(_stream_all(text, voice))
    except TtsError:
        raise
    except Exception as exc:
        raise TtsError(f"Edge TTS failed: {exc}") from exc
    if not audio:
        raise TtsError("Edge TTS returned no audio")
    return audio