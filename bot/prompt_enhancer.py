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
