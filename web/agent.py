# Agent Capabilities System

CAPABILITY_KEYWORDS = {
    "ku": ["taybeti", "taybetiiyekan", "ci detuanit", "ci kardaket", "qabletit", "tuenayi"],
    "fa": ["ghabliyat", "tavanayi", "chikar", "chand", "emkanat", "vizhegi", "ghabliyatha", "chi dari", "chi baladam"],
    "en": ["capabilities", "features", "what can you do", "abilities", "what do you do", "help me", "commands"]
}

IMAGE_KEYWORDS = {
    "ku": ["wene", "wene drrust bke", "weney", "ankas", "tasvir"],
    "fa": ["ankas", "tasvir", "vine", "sakht ankas", "tolid tasvir", "generate image", "create image"],
    "en": ["image", "picture", "photo", "draw", "generate image", "create image", "make image"]
}

VOICE_KEYWORDS = {
    "ku": ["deng", "deng bnese", "voys", "wes"],
    "fa": ["sada", "voice", "payam soti", "ersal sada"],
    "en": ["voice", "audio", "speak", "say", "send voice"]
}

def detect_feature_request(message, lang):
    msg_lower = message.lower()
    for kw in CAPABILITY_KEYWORDS.get(lang, CAPABILITY_KEYWORDS["en"]):
        if kw.lower() in msg_lower:
            return "capabilities"
    for kw in IMAGE_KEYWORDS.get(lang, IMAGE_KEYWORDS["en"]):
        if kw.lower() in msg_lower:
            return "image_request"
    for kw in VOICE_KEYWORDS.get(lang, VOICE_KEYWORDS["en"]):
        if kw.lower() in msg_lower:
            return "voice_request"
    return None

def get_feature_response(feature_type, lang):
    if feature_type == "capabilities":
        if lang == "ku":
            return "taybetiiyekan:\n\nchat: detuanit soal bkit\nimage: l telegeram bnese\nvoice: l telegeram bnese\nqr: /qr\nshort: /short\ncalc: /calc\nweather: /weather\ntranslate: /translate\nnews: /news\nmeme: /meme\nquiz: /quiz\njoke: /joke"
        elif lang == "fa":
            return "ghabliyatha:\n\nchat: har soali beporsid\nimage: dar telegeram befrestid\nvoice: dar telegeram befrestid\nqr: /qr\nshort: /short\ncalc: /calc\nweather: /weather\ntranslate: /translate\nnews: /news\nmeme: /meme\nquiz: /quiz\njoke: /joke"
        else:
            return "capabilities:\n\nchat: ask any question\nimage: send via Telegram\nvoice: send via Telegram\nqr: /qr\nshort: /short\ncalc: /calc\nweather: /weather\ntranslate: /translate\nnews: /news\nmeme: /meme\nquiz: /quiz\njoke: /joke"
    elif feature_type == "image_request":
        if lang == "ku":
            return "wene drrost krdn ba AI:\n\nl yerda natanit wene drrost bkit. telegeram aya! @ashkan_surii"
        elif lang == "fa":
            return "sakht ankas ba AI:\n\ndinja emkanat nist. be telegeram beravid! @ashkan_surii"
        else:
            return "generate AI images:\n\nyou cant create images here. go to telegram! @ashkan_surii"
    elif feature_type == "voice_request":
        if lang == "ku":
            return "nardnii deng:\n\nl yerda natanit deng bnese. telegeram aya! @ashkan_surii"
        elif lang == "fa":
            return "ersal sada:\n\ndinja emkanat nist. be telegeram beravid! @ashkan_surii"
        else:
            return "send voice messages:\n\nyou cant send voice here. go to telegram! @ashkan_surii"
    return None
