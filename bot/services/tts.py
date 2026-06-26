"""تبدیل متن به گفتار — Gemini TTS + edge-tts (fallback)."""
import io
import logging

from .. import config

log = logging.getLogger("kaysan.tts")

_VOICE_MAP_EDGE = {
    "ku": "tr-TR-AhmetNeural",
    "fa": "fa-IR-DilaraNeural",
    "en": "en-US-AvaNeural",
}

_VOICE_MAP_GEMINI = {
    "ku": "Kore",
    "fa": "Kore",
    "en": "Charon",
}


async def _gemini_tts(text: str, lang: str = "fa") -> bytes | None:
    """Google Gemini TTS — کیفیت بالا."""
    if not config.GOOGLE_AI_KEY:
        return None
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=config.GOOGLE_AI_KEY)
        voice = _VOICE_MAP_GEMINI.get(lang, "Kore")

        response = client.models.generate_content(
            model="gemini-3.1-flash-tts-preview",
            contents=f"Say the following text exactly, with natural emotion and pacing. Text: {text}",
            config=types.GenerateContentConfig(
                response_modalities=["Audio"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice,
                        )
                    )
                ),
            ),
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.data:
                audio_data = part.inline_data.data
                if isinstance(audio_data, bytes) and len(audio_data) > 100:
                    log.info("✅ Gemini TTS: %d bytes", len(audio_data))
                    return audio_data
    except Exception as e:
        log.warning("⚠️ Gemini TTS failed: %s", e)
    return None


async def _edge_tts(text: str, lang: str = "fa") -> bytes | None:
    """Microsoft Edge TTS — fallback رایگان."""
    try:
        import edge_tts
        voice = _VOICE_MAP_EDGE.get(lang, _VOICE_MAP_EDGE["fa"])
        communicate = edge_tts.Communicate(text, voice)
        buf = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buf.write(chunk["data"])
        if buf.tell() > 0:
            return buf.getvalue()
    except Exception as e:
        log.warning("⚠️ Edge TTS failed: %s", e)
    return None


async def text_to_speech(text: str, lang: str = "fa") -> bytes | None:
    """متن را به فایل صوتی تبدیل می‌کند — اول Gemini، بعد Edge TTS."""
    result = await _gemini_tts(text, lang)
    if result:
        return result
    return await _edge_tts(text, lang)
