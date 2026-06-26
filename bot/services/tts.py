"""تبدیل متن به گفتار — Gemini TTS + edge-tts (fallback)."""
import io
import logging
import subprocess
import tempfile

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


def _pcm_to_ogg(pcm_data: bytes, sample_rate: int = 24000) -> bytes | None:
    """تبدیل raw PCM به OGG/Opus برای تلگرام."""
    try:
        with tempfile.NamedTemporaryFile(suffix=".pcm", delete=False) as pcm_f:
            pcm_f.write(pcm_data)
            pcm_path = pcm_f.name
        ogg_path = pcm_path.replace(".pcm", ".ogg")
        subprocess.run([
            "ffmpeg", "-y", "-f", "s16le", "-ar", str(sample_rate), "-ac", "1",
            "-i", pcm_path, "-c:a", "libopus", "-b:a", "64k", ogg_path
        ], capture_output=True, timeout=10)
        with open(ogg_path, "rb") as f:
            ogg_data = f.read()
        import os
        os.unlink(pcm_path)
        os.unlink(ogg_path)
        if ogg_data and len(ogg_data) > 100:
            return ogg_data
    except Exception as e:
        log.warning("PCM to OGG conversion failed: %s", e)
    return None


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
                    ogg = _pcm_to_ogg(audio_data)
                    if ogg:
                        log.info("✅ Gemini TTS: %d bytes (OGG)", len(ogg))
                        return ogg
                    log.info("✅ Gemini TTS: %d bytes (raw PCM)", len(audio_data))
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
