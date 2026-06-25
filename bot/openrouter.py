"""کلاینت OpenRouter — با streaming، temperature control، quality check و multi-model."""
import logging
import asyncio

import aiohttp

from . import config

log = logging.getLogger("kaysan.or")

_HEADERS = {
    "Authorization": f"Bearer {config.OPENROUTER_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://t.me/KaysanAI_Bot",
    "X-Title": "Kaysan AI",
}


class ORError(Exception):
    pass


async def _call(model: str, messages: list, max_tokens: int = 1200,
                temperature: float = 0.7) -> tuple[str, dict]:
    """Returns (content, usage_dict)."""
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    timeout = aiohttp.ClientTimeout(total=90, connect=10)
    async with aiohttp.ClientSession(timeout=timeout) as s:
        async with s.post(config.OPENROUTER_URL, headers=_HEADERS, json=payload) as r:
            data = await r.json()
            if r.status != 200:
                msg = (data.get("error") or {}).get("message", str(data)[:160])
                raise ORError(f"{r.status}: {msg}")
            choices = data.get("choices") or []
            if not choices:
                raise ORError("empty response")
            content = (choices[0].get("message") or {}).get("content", "").strip()
            usage = data.get("usage") or {}
            return content, {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "cost": usage.get("cost", 0),
            }


async def _call_stream(model: str, messages: list, max_tokens: int = 1200,
                       temperature: float = 0.7):
    """Streaming call — yields chunks."""
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": True,
    }
    timeout = aiohttp.ClientTimeout(total=90, connect=10)
    full_content = ""
    usage = {"prompt_tokens": 0, "completion_tokens": 0, "cost": 0}
    async with aiohttp.ClientSession(timeout=timeout) as s:
        async with s.post(config.OPENROUTER_URL, headers=_HEADERS, json=payload) as r:
            if r.status != 200:
                data = await r.json()
                msg = (data.get("error") or {}).get("message", str(data)[:160])
                raise ORError(f"{r.status}: {msg}")
            async for line in r.content:
                decoded = line.decode("utf-8").strip()
                if not decoded or not decoded.startswith("data: "):
                    continue
                data_str = decoded[6:]
                if data_str == "[DONE]":
                    break
                try:
                    import json
                    chunk = json.loads(data_str)
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    token = delta.get("content", "")
                    if token:
                        full_content += token
                        yield token, full_content
                    if chunk.get("usage"):
                        usage.update({
                            "prompt_tokens": chunk["usage"].get("prompt_tokens", 0),
                            "completion_tokens": chunk["usage"].get("completion_tokens", 0),
                            "cost": chunk["usage"].get("cost", 0),
                        })
                except Exception:
                    continue
    yield None, usage


def _quality_check(reply: str, intent: str) -> bool:
    """بررسی کیفیت جواب — جواب خیلی کوتاه یا بی‌معنی رد میشه."""
    if not reply or len(reply.strip()) < 5:
        return False
    words = reply.split()
    if intent != "chat" and len(words) < config.MIN_REPLY_WORDS:
        return False
    if reply.lower() in ("ok", "sure", "yes", "no", "بله", "خیر", "باش", "نەخێر"):
        return False
    return True


async def chat(messages: list, models: list, intent: str = "chat",
               **kw) -> tuple[str, dict]:
    """مدل‌ها را به ترتیب امتحان می‌کند. Returns (content, usage)."""
    temperature = kw.pop("temperature", None)
    if temperature is None:
        temperature = config.TEMP_BY_INTENT.get(intent, 0.7)
    max_tokens = kw.pop("max_tokens", None)
    if max_tokens is None:
        max_tokens = config.MAX_TOKENS_BY_INTENT.get(intent, 1800)

    last = None
    for model in models:
        try:
            out, usage = await _call(model, messages, max_tokens=max_tokens,
                                     temperature=temperature)
            if out and _quality_check(out, intent):
                log.info("✅ model answered: %s (tokens: %d/%d, cost: $%.6f)",
                         model, usage["prompt_tokens"], usage["completion_tokens"],
                         usage["cost"])
                usage["model"] = model
                return out, usage
            elif out:
                log.warning("⚠️ quality check failed for %s, trying next model", model)
        except Exception as e:
            last = e
            log.warning("❌ model %s failed: %s", model, e)
            continue

    if last:
        raise ORError(str(last))
    raise ORError("all models failed")


async def chat_stream(messages: list, models: list, intent: str = "chat",
                      **kw):
    """Streaming chat — yields (chunk, full_text_or_usage)."""
    temperature = kw.pop("temperature", None)
    if temperature is None:
        temperature = config.TEMP_BY_INTENT.get(intent, 0.7)
    max_tokens = kw.pop("max_tokens", None)
    if max_tokens is None:
        max_tokens = config.MAX_TOKENS_BY_INTENT.get(intent, 1800)

    for model in models:
        try:
            full_text = ""
            async for chunk, result in _call_stream(model, messages,
                                                     max_tokens=max_tokens,
                                                     temperature=temperature):
                if chunk is None:
                    result["model"] = model
                    if _quality_check(full_text, intent):
                        yield None, result
                        return
                    else:
                        log.warning("⚠️ streaming quality check failed for %s", model)
                        break
                full_text += chunk
                yield chunk, None
        except Exception as e:
            log.warning("❌ streaming model %s failed: %s", model, e)
            continue

    raise ORError("all streaming models failed")


def with_system(system: str, user_text: str, history: list | None = None) -> list:
    msgs = [{"role": "system", "content": system}]
    if history:
        msgs.extend(history)
    msgs.append({"role": "user", "content": user_text})
    return msgs


def vision_message(system: str, text: str, image_data_url: str) -> list:
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": [
            {"type": "text", "text": text or "Describe this image."},
            {"type": "image_url", "image_url": {"url": image_data_url}},
        ]},
    ]


def _score_response(reply: str, intent: str) -> float:
    """امتیازدهی به جواب بر اساس کیفیت. هرچه بالاتر، بهتر."""
    if not reply or not _quality_check(reply, intent):
        return 0.0
    score = 1.0
    words = reply.split()
    word_count = len(words)
    if intent == "chat":
        if 15 <= word_count <= 200:
            score += 1.0
        elif word_count < 5:
            score -= 0.5
    else:
        if word_count >= config.MIN_REPLY_WORDS:
            score += 1.0
    if any(c in reply for c in ".,;:!؟"):
        score += 0.3
    if len(reply) > 50:
        score += 0.2
    lines = reply.strip().split("\n")
    if len(lines) >= 2:
        score += 0.2
    return score


async def chat_parallel(messages: list, models: list, intent: str = "chat",
                        **kw) -> tuple[str, dict, list[dict]]:
    """ارسال همزمان به چند مدل — بهترین جواب + لیست جواب‌های دیگه.

    Returns: (best_reply, best_usage, alternatives)
    alternatives: [{"model": str, "reply": str, "score": float}, ...]
    """
    temperature = kw.pop("temperature", None)
    if temperature is None:
        temperature = config.TEMP_BY_INTENT.get(intent, 0.7)
    max_tokens = kw.pop("max_tokens", None)
    if max_tokens is None:
        max_tokens = config.MAX_TOKENS_BY_INTENT.get(intent, 1800)

    num_models = min(3, len(models))
    selected = models[:num_models]

    async def _call_one(model):
        try:
            out, usage = await _call(model, messages, max_tokens=max_tokens,
                                     temperature=temperature)
            if out:
                sc = _score_response(out, intent)
                usage["model"] = model
                return {"model": model, "reply": out, "usage": usage, "score": sc}
        except Exception as e:
            log.warning("parallel model %s failed: %s", model, e)
        return None

    results = await asyncio.gather(*[_call_one(m) for m in selected])
    valid = [r for r in results if r and r["score"] > 0]

    if not valid:
        if results:
            for r in results:
                if r:
                    return r["reply"], r["usage"], []
        raise ORError("all parallel models failed")

    valid.sort(key=lambda r: r["score"], reverse=True)
    best = valid[0]
    alternatives = [
        {"model": r["model"], "reply": r["reply"], "score": r["score"]}
        for r in valid[1:]
    ]

    log.info("🏆 parallel best: %s (score=%.1f) | alternatives: %s",
             best["model"], best["score"],
             [f"{r['model']}({r['score']:.1f})" for r in alternatives])

    return best["reply"], best["usage"], alternatives
