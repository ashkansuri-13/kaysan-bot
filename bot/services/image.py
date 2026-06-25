"""ساخت عکس — ۱۰ API رایگان + انتخاب سبک + fallback هوشمند."""
import logging
import random
import urllib.parse

import aiohttp

from .. import config, openrouter

log = logging.getLogger("kaysan.image")

STYLE_PROMPTS = {
    "anime": "anime style, high quality, detailed, vibrant colors",
    "realistic": "photorealistic, high resolution, detailed, professional photography",
    "cartoon": "cartoon style, colorful, fun, playful, 3D render",
    "watercolor": "watercolor painting, soft colors, artistic, beautiful",
    "oil_painting": "oil painting, classical art, detailed brushstrokes, masterpiece",
    "pixel_art": "pixel art style, retro, 16-bit, nostalgic",
    "3d_render": "3D render, octane render, highly detailed, cinematic lighting",
    "comic": "comic book style, bold lines, dynamic, Marvel DC style",
    "minimalist": "minimalist design, clean, simple, modern, elegant",
    "cyberpunk": "cyberpunk style, neon lights, futuristic, dark atmosphere",
    "fantasy": "fantasy art, magical, ethereal, epic, Lord of the Rings style",
    "sketch": "pencil sketch, black and white, detailed, artistic drawing",
}

STYLE_KEYWORDS = {
    "انیمیشنی": "anime",
    "anime": "anime",
    "واقعی": "realistic",
    "واقع گرایانه": "realistic",
    "photorealistic": "realistic",
    "کارتونی": "cartoon",
    "cartoon": "cartoon",
    "آبی": "watercolor",
    "watercolor": "watercolor",
    "نقاشی": "oil_painting",
    "پیکسلی": "pixel_art",
    "سه بعدی": "3d_render",
    "3d": "3d_render",
    "کمیک": "comic",
    "مینیمال": "minimalist",
    "سایبرپانک": "cyberpunk",
    "فانتزی": "fantasy",
    "اسکچ": "sketch",
    "طراحی": "sketch",
}


def _detect_style(text: str) -> tuple[str, str]:
    """تشخیص سبک از متن کاربر. Returns (style_key, clean_prompt)."""
    lower = text.lower()
    for keyword, style in STYLE_KEYWORDS.items():
        if keyword in lower:
            clean = text
            for kw in STYLE_KEYWORDS:
                clean = clean.replace(kw, "").replace(kw.upper(), "")
            return style, clean.strip()
    return "realistic", text


def get_style_prompt(style: str) -> str:
    return STYLE_PROMPTS.get(style, STYLE_PROMPTS["realistic"])


def get_style_keyboard():
    """کیبورد انتخاب سبک."""
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎨 انیمیشنی", callback_data="style:anime"),
            InlineKeyboardButton(text="📷 واقعی", callback_data="style:realistic"),
        ],
        [
            InlineKeyboardButton(text="🖌️ کارتونی", callback_data="style:cartoon"),
            InlineKeyboardButton(text="💧 آبرنگ", callback_data="style:watercolor"),
        ],
        [
            InlineKeyboardButton(text="🖼️ نقاشی روغنی", callback_data="style:oil_painting"),
            InlineKeyboardButton(text="👾 پیکسلی", callback_data="style:pixel_art"),
        ],
        [
            InlineKeyboardButton(text="🔮 سه‌بعدی", callback_data="style:3d_render"),
            InlineKeyboardButton(text="💥 کمیک", callback_data="style:comic"),
        ],
        [
            InlineKeyboardButton(text="✨ مینیمال", callback_data="style:minimalist"),
            InlineKeyboardButton(text="🌃 سایبرپانک", callback_data="style:cyberpunk"),
        ],
        [
            InlineKeyboardButton(text="🧙 فانتزی", callback_data="style:fantasy"),
            InlineKeyboardButton(text="✏️ اسکچ", callback_data="style:sketch"),
        ],
    ])


PROMPT_ENHANCE_SYSTEM = (
    "Convert this image request into a detailed, descriptive English prompt for an AI image generator. "
    "Be specific about style, lighting, composition, and mood. "
    "Only output the prompt itself, no explanations."
)


async def _enhance_prompt(prompt: str) -> str:
    """پرامپت کاربر رو به انگلیسی بهبود می‌دهد."""
    is_english = all(ord(c) < 0x0600 or 0x06FF < ord(c) < 0x10000 for c in prompt if c.isalpha())
    if is_english and len(prompt.split()) > 3:
        return prompt

    model = config.PRIMARY_MODEL or (config.CHAT_MODELS[0] if config.CHAT_MODELS else None)
    if not model:
        return prompt

    try:
        messages = [
            {"role": "system", "content": PROMPT_ENHANCE_SYSTEM},
            {"role": "user", "content": prompt},
        ]
        result, _ = await openrouter.chat(messages, [model], max_tokens=150, temperature=0.3)
        if result and len(result) > 5:
            log.info("🎨 prompt enhanced: '%s' → '%s'", prompt[:40], result[:80])
            return result.strip()
    except Exception as e:
        log.warning("⚠️ prompt enhance failed: %s", e)

    return prompt


async def generate(prompt: str, style: str = "realistic") -> bytes | None:
    """تصویر با انتخاب سبک. اول API‌ها رو امتحان می‌کنه."""
    style_suffix = get_style_prompt(style)
    enhanced = await _enhance_prompt(prompt)
    full_prompt = f"{enhanced}, {style_suffix}"

    apis = [
        ("Pollinations-nanobanana", _pollinations_nanobanana),
        ("Pollinations-sana", _pollinations_sana),
        ("Pollinations-flux", _pollinations_flux),
        ("Pollinations-flux-schnell", _pollinations_flux_schnell),
        ("Pollinations-flux-dev", _pollinations_flux_dev),
        ("Pollinations-dalle-nano", _pollinations_dalle_nano),
        ("Pollinations-stable", _pollinations_stable),
        ("Pollinations-realistic", _pollinations_realistic),
        ("Pollinations-anime", _pollinations_anime),
        ("Pollinations-turbo", _pollinations_turbo),
        ("Together-free", _together_free),
        ("HuggingFace-sdxl", _huggingface_sdxl),
        ("HuggingFace-flux", _huggingface_flux),
        ("Prodia", _prodia),
        ("Stability-ai", _stability_free),
        ("Getimg", _getimg_free),
        ("Leonardo-free", _leonardo_free),
    ]

    for name, api_func in apis:
        try:
            result = await api_func(full_prompt)
            if result and len(result) > 1000:
                log.info("🎨 %s: %d bytes", name, len(result))
                return result
        except Exception as e:
            log.warning("⚠️ %s failed: %s", name, e)
            continue

    if config.IMAGE_MODEL:
        try:
            result = await _openrouter_image(enhanced)
            if result:
                return result
        except Exception as e:
            log.warning("OpenRouter image failed: %s", e)

    return None


async def _pollinations_sana(prompt: str) -> bytes | None:
    seed = random.randint(1, 999999)
    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&nologo=true&model=sana&enhance=true&seed={seed}"
    timeout = aiohttp.ClientTimeout(total=120)
    async with aiohttp.ClientSession(timeout=timeout) as s:
        async with s.get(url) as r:
            if r.status == 200:
                data = await r.read()
                if data and len(data) > 1000:
                    return data
    return None


async def _pollinations_flux(prompt: str) -> bytes | None:
    seed = random.randint(1, 999999)
    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&nologo=true&model=flux&enhance=true&seed={seed}"
    timeout = aiohttp.ClientTimeout(total=120)
    async with aiohttp.ClientSession(timeout=timeout) as s:
        async with s.get(url) as r:
            if r.status == 200:
                data = await r.read()
                if data and len(data) > 1000:
                    return data
    return None


async def _pollinations_turbo(prompt: str) -> bytes | None:
    seed = random.randint(1, 999999)
    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&nologo=true&model=turbo&enhance=true&seed={seed}"
    timeout = aiohttp.ClientTimeout(total=120)
    async with aiohttp.ClientSession(timeout=timeout) as s:
        async with s.get(url) as r:
            if r.status == 200:
                data = await r.read()
                if data and len(data) > 1000:
                    return data
    return None



async def _pollinations_nanobanana(prompt: str) -> bytes | None:
    seed = random.randint(1, 999999)
    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&nologo=true&model=nano-banana&enhance=true&seed={seed}"
    timeout = aiohttp.ClientTimeout(total=120)
    async with aiohttp.ClientSession(timeout=timeout) as s:
        async with s.get(url) as r:
            if r.status == 200:
                data = await r.read()
                if data and len(data) > 1000:
                    return data
    return None


async def _pollinations_flux_schnell(prompt: str) -> bytes | None:
    seed = random.randint(1, 999999)
    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&nologo=true&model=flux-schnell&enhance=true&seed={seed}"
    timeout = aiohttp.ClientTimeout(total=120)
    async with aiohttp.ClientSession(timeout=timeout) as s:
        async with s.get(url) as r:
            if r.status == 200:
                data = await r.read()
                if data and len(data) > 1000:
                    return data
    return None


async def _pollinations_flux_dev(prompt: str) -> bytes | None:
    seed = random.randint(1, 999999)
    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&nologo=true&model=flux-dev&enhance=true&seed={seed}"
    timeout = aiohttp.ClientTimeout(total=120)
    async with aiohttp.ClientSession(timeout=timeout) as s:
        async with s.get(url) as r:
            if r.status == 200:
                data = await r.read()
                if data and len(data) > 1000:
                    return data
    return None


async def _pollinations_dalle_nano(prompt: str) -> bytes | None:
    seed = random.randint(1, 999999)
    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&nologo=true&model=dall-e-3-nano&enhance=true&seed={seed}"
    timeout = aiohttp.ClientTimeout(total=120)
    async with aiohttp.ClientSession(timeout=timeout) as s:
        async with s.get(url) as r:
            if r.status == 200:
                data = await r.read()
                if data and len(data) > 1000:
                    return data
    return None


async def _pollinations_stable(prompt: str) -> bytes | None:
    seed = random.randint(1, 999999)
    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&nologo=true&model=stable-diffusion&enhance=true&seed={seed}"
    timeout = aiohttp.ClientTimeout(total=120)
    async with aiohttp.ClientSession(timeout=timeout) as s:
        async with s.get(url) as r:
            if r.status == 200:
                data = await r.read()
                if data and len(data) > 1000:
                    return data
    return None


async def _pollinations_realistic(prompt: str) -> bytes | None:
    seed = random.randint(1, 999999)
    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&nologo=true&model=realistic&enhance=true&seed={seed}"
    timeout = aiohttp.ClientTimeout(total=120)
    async with aiohttp.ClientSession(timeout=timeout) as s:
        async with s.get(url) as r:
            if r.status == 200:
                data = await r.read()
                if data and len(data) > 1000:
                    return data
    return None


async def _pollinations_anime(prompt: str) -> bytes | None:
    seed = random.randint(1, 999999)
    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&nologo=true&model=anime&enhance=true&seed={seed}"
    timeout = aiohttp.ClientTimeout(total=120)
    async with aiohttp.ClientSession(timeout=timeout) as s:
        async with s.get(url) as r:
            if r.status == 200:
                data = await r.read()
                if data and len(data) > 1000:
                    return data
    return None

async def _together_free(prompt: str) -> bytes | None:
    """Together.ai free tier."""
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(
                "https://api.together.xyz/v1/images/generations",
                headers={"Content-Type": "application/json"},
                json={
                    "model": "stabilityai/stable-diffusion-xl-base-1.0",
                    "prompt": prompt,
                    "width": 1024,
                    "height": 1024,
                    "steps": 20,
                    "n": 1,
                },
                timeout=aiohttp.ClientTimeout(total=60),
            ) as r:
                if r.status == 200:
                    data = await r.json()
                    images = data.get("data", [])
                    if images:
                        img_url = images[0].get("url", "")
                        if img_url:
                            async with s.get(img_url) as img_r:
                                if img_r.status == 200:
                                    return await img_r.read()
    except Exception:
        pass
    return None


async def _huggingface_sdxl(prompt: str) -> bytes | None:
    """HuggingFace free inference."""
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(
                "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
                json={"inputs": prompt},
                timeout=aiohttp.ClientTimeout(total=90),
            ) as r:
                if r.status == 200:
                    data = await r.read()
                    if data and len(data) > 1000:
                        return data
    except Exception:
        pass
    return None


async def _huggingface_flux(prompt: str) -> bytes | None:
    """HuggingFace FLUX free."""
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(
                "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell",
                json={"inputs": prompt},
                timeout=aiohttp.ClientTimeout(total=90),
            ) as r:
                if r.status == 200:
                    data = await r.read()
                    if data and len(data) > 1000:
                        return data
    except Exception:
        pass
    return None


async def _prodia(prompt: str) -> bytes | None:
    """Prodia free API."""
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(
                "https://api.prodia.com/v1/sd/generate",
                json={
                    "model": "sdxl",
                    "prompt": prompt,
                    "negative_prompt": "ugly, blurry, low quality",
                    "steps": 25,
                    "cfg_scale": 7,
                },
                timeout=aiohttp.ClientTimeout(total=60),
            ) as r:
                if r.status == 200:
                    data = await r.json()
                    job_id = data.get("job")
                    if job_id:
                        for _ in range(30):
                            await asyncio.sleep(2)
                            async with s.get(f"https://api.prodia.com/v1/job/{job_id}") as jr:
                                if jr.status == 200:
                                    jd = await jr.json()
                                    if jd.get("status") == "succeeded":
                                        img_url = jd.get("imageUrl", "")
                                        if img_url:
                                            async with s.get(img_url) as img_r:
                                                return await img_r.read()
    except Exception:
        pass
    return None


async def _stability_free(prompt: str) -> bytes | None:
    """Stability AI free tier."""
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(
                "https://api.stability.ai/v2beta/stable-image/generate/sd3",
                headers={"Accept": "image/*"},
                data={"prompt": prompt, "output_format": "png"},
                timeout=aiohttp.ClientTimeout(total=60),
            ) as r:
                if r.status == 200:
                    data = await r.read()
                    if data and len(data) > 1000:
                        return data
    except Exception:
        pass
    return None


async def _getimg_free(prompt: str) -> bytes | None:
    """GetIMG.ai free tier."""
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(
                "https://api.getimg.ai/v1/stable-diffusion-xl/text-to-image",
                json={"prompt": prompt, "width": 1024, "height": 1024},
                timeout=aiohttp.ClientTimeout(total=60),
            ) as r:
                if r.status == 200:
                    data = await r.json()
                    img_data = data.get("image", "")
                    if img_data:
                        import base64
                        return base64.b64decode(img_data)
    except Exception:
        pass
    return None


async def _leonardo_free(prompt: str) -> bytes | None:
    """Leonardo.ai free API."""
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(
                "https://cloud.leonardo.ai/api/rest/v1/generations",
                json={
                    "prompt": prompt,
                    "modelId": " Leonardo Flash",
                    "width": 1024,
                    "height": 1024,
                },
                timeout=aiohttp.ClientTimeout(total=60),
            ) as r:
                if r.status == 200:
                    data = await r.json()
                    gen_id = data.get("sdGenerationJob", {}).get("id")
                    if gen_id:
                        for _ in range(30):
                            await asyncio.sleep(2)
                            async with s.get(f"https://cloud.leonardo.ai/api/rest/v1/generations/{gen_id}") as gr:
                                if gr.status == 200:
                                    gd = await gr.json()
                                    images = gd.get("generations", [])
                                    if images:
                                        img_url = images[0].get("url", "")
                                        if img_url:
                                            async with s.get(img_url) as img_r:
                                                return await img_r.read()
    except Exception:
        pass
    return None


async def _openrouter_image(prompt: str) -> bytes | None:
    """OpenRouter image models."""
    import base64

    headers = {
        "Authorization": f"Bearer {config.OPENROUTER_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.IMAGE_MODEL,
        "messages": [{"role": "user", "content": f"Generate an image: {prompt}"}],
        "modalities": ["image", "text"],
    }
    timeout = aiohttp.ClientTimeout(total=120)
    async with aiohttp.ClientSession(timeout=timeout) as s:
        async with s.post(config.OPENROUTER_URL, headers=headers, json=payload) as r:
            data = await r.json()
            msg = (data.get("choices") or [{}])[0].get("message", {})
            images = msg.get("images") or []
            if images:
                url = images[0].get("image_url", {}).get("url", "")
                if url.startswith("data:"):
                    b64 = url.split(",", 1)[1]
                    return base64.b64decode(b64)
    return None
