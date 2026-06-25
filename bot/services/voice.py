"""درک ویس — با کیفیت بالاتر."""
import io
import logging
import shutil

from pydub import AudioSegment

from .. import config

log = logging.getLogger("kaysan.voice")

_FFMPEG_AVAILABLE = shutil.which("ffmpeg") is not None


async def transcribe(file_bytes: bytes, fmt: str = "ogg") -> str | None:
    """متنِ گفته‌شده در ویس را با کیفیت بالا برمی‌گرداند."""
    if not _FFMPEG_AVAILABLE:
        log.error("ffmpeg not installed — audio transcription unavailable")
        return None

    # اول Groq Whisper (بهترین کیفیت)
    if config.GROQ_API_KEY:
        text = await _groq_transcribe(file_bytes, fmt)
        if text:
            return text

    # دوم: Google STT با زبان‌های مختلف
    text = await _google_stt_fallback(file_bytes, fmt)
    if text:
        return text

    # سوم: پیام خطا به کاربر
    log.warning("all STT methods failed")
    return None


async def _groq_transcribe(file_bytes: bytes, fmt: str) -> str | None:
    """Groq Whisper — سریع و دقیق."""
    try:
        audio = AudioSegment.from_file(io.BytesIO(file_bytes), format=fmt)
        audio = audio.set_frame_rate(16000).set_channels(1)

        # حذف نویز پس‌زمینه
        audio = audio.apply_gain(-audio.dBFS)

        wav_buf = io.BytesIO()
        audio.export(wav_buf, format="wav")
        wav_buf.seek(0)
        wav_buf.name = "audio.wav"

        import groq
        client = groq.Groq(api_key=config.GROQ_API_KEY)
        result = client.audio.transcriptions.create(
            file=wav_buf,
            model="whisper-large-v3-turbo",
            response_format="verbose_json",
            temperature=0.0,
        )
        text = result.text.strip() if hasattr(result, "text") else ""
        if text and len(text) > 1:
            log.info("✅ Groq Whisper: %s", text[:80])
            return text
    except Exception as e:
        log.warning("⚠️ Groq Whisper failed: %s", e)
    return None


async def _google_stt_fallback(file_bytes: bytes, fmt: str) -> str | None:
    """Google STT — fallback با چند زبان."""
    import speech_recognition as sr

    try:
        audio = AudioSegment.from_file(io.BytesIO(file_bytes), format=fmt)
        audio = audio.set_frame_rate(16000).set_channels(1)
        wav_buf = io.BytesIO()
        audio.export(wav_buf, format="wav")
        wav_buf.seek(0)

        r = sr.Recognizer()
        r.energy_threshold = 300
        r.dynamic_energy_threshold = True
        with sr.AudioFile(wav_buf) as source:
            audio_data = r.record(source)

        for lang in ["ckb-IR", "fa-IR", "en-US"]:
            try:
                text = r.recognize_google(audio_data, language=lang)
                if text and len(text.strip()) > 1:
                    log.info("✅ Google STT [%s]: %s", lang, text[:80])
                    return text.strip()
            except sr.UnknownValueError:
                continue
            except Exception:
                continue

        log.warning("⚠️ Google STT: no language matched")
        return None
    except Exception as e:
        log.error("❌ STT error: %s", e)
        return None
