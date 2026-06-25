"""تبدیل متن به گفتار — edge-tts (رایگان، باکیفیت)."""
import io
import logging

import edge_tts

log = logging.getLogger("kaysan.tts")

_VOICE_MAP = {
    "ku": "tr-TR-AhmetNeural",
    "fa": "fa-IR-DilaraNeural",
    "en": "en-US-AvaNeural",
}


async def text_to_speech(text: str, lang: str = "fa") -> bytes | None:
    """متن را به فایل صوتی OGG تبدیل می‌کند."""
    voice = _VOICE_MAP.get(lang, _VOICE_MAP["fa"])
    try:
        communicate = edge_tts.Communicate(text, voice)
        buf = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buf.write(chunk["data"])
        if buf.tell() > 0:
            return buf.getvalue()
    except Exception as e:
        log.warning("TTS failed: %s", e)
    return None
