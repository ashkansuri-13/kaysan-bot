"""پرامپت‌نویس هوشمند — تبدیل سوال کاربر به پرامپت حرفه‌ای."""
import logging
import asyncio

from . import config, openrouter

log = logging.getLogger("kaysan.enhancer")

_ENHANCER_PROMPTS = {
    'ku': """تۆ پرامپت‌نوی سەرەکییت. ئەرکت ئەوەیە کە پرسیاری بەکارهێنەر بگریت و پرامپتێکی ورد و تەواو بۆ مۆدێلی AI بنووسیت.

ڕێنماییەکان:
1. پرسیار بگرە و بە وردی بیانی بۆ چی داوای لێ دەکرێت
2. ئەگەر پرسیارەکە مبهمە، ئەو بوارانەی کە دەکرێت مەtaboola بۆچی
3. زمانی پرامپت هەمان زمانی بەکارهێنەر بێت
4. پرامپت بگرە بۆ: {intent}
5. وەڵام پێشکەش بکە بە فۆرماتی:

PROMPT: [پرامپتی تەواو بۆ مۆدێلی AI]

نەک: ئەو پرامپتەی کە خۆت وەڵام بدەیت، تەنها پرامپتی بۆ مۆدێلی دواتر بنووسە.

ئێستا پرسیاری بەکارهێنەر بگرە و پرامپت دروست بکە:

پرسیار: {user_message}
بەستن: {intent}""",

    'fa': """تو یک پرامپت‌نویس حرفه‌ای هستی. کارت اینه که سوال کاربر رو بگیری و تبدیلش کنی به یه پرامپت دقیق و کامل برای مدل AI.

دستورالعمل:
1. سوال کاربر رو بخون و دقیق بفهم چی میخواد
2. اگه سوال مبهمه، احتمالات مختلف رو در نظر بگیر
3. پرامپت رو به فارسی بنویس
4. پرامپت رو برای دسته‌بندی "{intent}" آماده کن
5. خروجی رو اینطوری بده:

PROMPT: [پرامپت کامل برای مدل AI]

نکته: فقط پرامپت رو بنویس، خودت جواب نده.

الان سوال کاربر رو بگیر و پرامپت درست کن:

سوال: {user_message}
دسته: {intent}""",

    'en': """You are a professional prompt engineer. Your job is to take a user's question and convert it into a detailed, precise prompt for an AI model.

Guidelines:
1. Read the user's question carefully and understand exactly what they want
2. If the question is ambiguous, consider multiple possible interpretations
3. Add relevant context and specificity
4. The prompt should be for intent: {intent}
5. Output format:

PROMPT: [The complete prompt for the AI model]

Note: Only write the prompt, do not answer the question yourself.

Now take the user's question and create an optimized prompt:

Question: {user_message}
Intent: {intent}""",
}


async def enhance_prompt(user_message: str, lang: str, intent: str) -> str:
    """تبدیل پیام کاربر به پرامپت حرفه‌ای."""
    if not config.PROMPT_ENHANCER_MODEL:
        return user_message

    enhancer_prompt = _ENHANCER_PROMPTS.get(lang, _ENHANCER_PROMPTS['en'])
    enhancer_prompt = enhancer_prompt.replace("{user_message}", user_message).replace("{intent}", intent)

    messages = [
        {"role": "system", "content": "You are a prompt engineer. Output ONLY the enhanced prompt, nothing else."},
        {"role": "user", "content": enhancer_prompt},
    ]

    try:
        reply, _ = await asyncio.wait_for(
            openrouter.chat(messages, config.PROMPT_ENHANCER_MODEL, max_tokens=500, temperature=0.3),
            timeout=15,
        )
        if reply and "PROMPT:" in reply:
            enhanced = reply.split("PROMPT:", 1)[1].strip()
            if len(enhanced) > 10:
                log.info("Prompt enhanced: %s -> %s", user_message[:50], enhanced[:50])
                return enhanced
    except Exception as e:
        log.warning("Prompt enhancement failed: %s", e)

    return user_message


# === پیشرفته‌های جدید ===

class PromptType:
    CHAT = "chat"
    IMAGE = "image"
    CODE = "code"
    TRANSLATE = "translate"
    SUMMARIZE = "summarize"
    CREATIVE = "creative"
    ANALYSIS = "analysis"


OPTIMAL_MODELS = {
    "chat": ["deepseek/deepseek-chat", "openai/gpt-4o-mini"],
    "image": ["openai/gpt-4o-mini", "google/gemini-2.5-flash"],
    "code": ["deepseek/deepseek-chat", "qwen/qwen3-coder:free"],
    "translate": ["deepseek/deepseek-chat", "openai/gpt-4o-mini"],
    "summarize": ["deepseek/deepseek-chat", "openai/gpt-4o-mini"],
    "creative": ["anthropic/claude-haiku-4.5", "openai/gpt-4o-mini"],
    "analysis": ["openai/gpt-4o-mini", "anthropic/claude-haiku-4.5"],
}

OPTIMAL_TEMPERATURE = {
    "chat": 0.8, "image": 0.7, "code": 0.2,
    "translate": 0.3, "summarize": 0.5,
    "creative": 0.9, "analysis": 0.4,
}

OPTIMAL_MAX_TOKENS = {
    "chat": 2000, "image": 200, "code": 4000,
    "translate": 2000, "summarize": 1500,
    "creative": 3000, "analysis": 2500,
}


def detect_prompt_type(message, intent="chat"):
    msg_lower = message.lower()
    if intent in ("image", "creative"): return "image"
    if intent in ("code", "programming"): return "code"
    if intent in ("translate", "translation"): return "translate"
    if intent in ("summarize", "summary"): return "summarize"
    
    image_kw = ["image", "picture", "ankas", "tasvir", "wene"]
    code_kw = ["code", "program"]
    translate_kw = ["translate", "tarjome"]
    summarize_kw = ["summarize", "summary"]
    creative_kw = ["story", "write", "poem"]
    analysis_kw = ["analyze", "analysis"]
    
    for kw in image_kw:
        if kw in msg_lower: return "image"
    for kw in code_kw:
        if kw in msg_lower: return "code"
    for kw in translate_kw:
        if kw in msg_lower: return "translate"
    for kw in summarize_kw:
        if kw in msg_lower: return "summarize"
    for kw in creative_kw:
        if kw in msg_lower: return "creative"
    for kw in analysis_kw:
        if kw in msg_lower: return "analysis"
    
    return "chat"


def get_optimal_model(prompt_type):
    return OPTIMAL_MODELS.get(prompt_type, OPTIMAL_MODELS["chat"])


def get_optimal_temperature(prompt_type):
    return OPTIMAL_TEMPERATURE.get(prompt_type, 0.7)


def get_optimal_max_tokens(prompt_type):
    return OPTIMAL_MAX_TOKENS.get(prompt_type, 2000)


async def enhance_prompt_engine(user_message, lang, intent="chat"):
    prompt_type = detect_prompt_type(user_message, intent)
    models = get_optimal_model(prompt_type)
    temp = get_optimal_temperature(prompt_type)
    max_tok = get_optimal_max_tokens(prompt_type)
    
    enhance_instructions = {
        "ku": "پرامپت کاربر رو بهینه کن: ",
        "fa": "پرامپت کاربر رو بهینه کن: ",
        "en": "Optimize the user prompt: ",
    }
    
    instruction = enhance_instructions.get(lang, enhance_instructions["en"])
    
    messages = [
        {"role": "system", "content": f"You are a prompt engineer for {prompt_type}. Output ONLY the optimized prompt, nothing else. Make it detailed and specific."},
        {"role": "user", "content": instruction + user_message},
    ]
    
    try:
        reply, _ = await asyncio.wait_for(
            openrouter.chat(messages, models, max_tokens=300, temperature=0.3),
            timeout=15,
        )
        if reply and len(reply) > 5:
            enhanced = reply.strip()
            for prefix in ["PROMPT:", "Output:", "Result:"]:
                if enhanced.startswith(prefix):
                    enhanced = enhanced[len(prefix):].strip()
            log.info("enhanced [%s]: %s -> %s", prompt_type, user_message[:40], enhanced[:60])
            return enhanced, prompt_type
    except Exception as e:
        log.warning("enhance failed: %s", e)
    
    return user_message, prompt_type
