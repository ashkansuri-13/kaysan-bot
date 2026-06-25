"""روتر: تشخیص زبان و نیتِ کاربر، و انتخاب مدل مناسب."""
import re

from . import config

_ARABIC = re.compile(r"[\u0600-\u06FF]")
_KURDISH = re.compile(r"[ێۆڵڕەھ]")


def detect_lang(text: str) -> str:
    if not text:
        return config.DEFAULT_LANG
    if _KURDISH.search(text):
        return "ku"
    if _ARABIC.search(text):
        return "fa"
    return "en"


_IMG = re.compile(
    r"(عکس|تصویر|بکش|نقاشی|وێنە|بنقاش|draw|image|picture|photo of|generate.*image|paint|portrait|sketch)",
    re.I,
)
_MUSIC = re.compile(r"(آهنگ|موزیک|موسیقی|مۆزیک|گۆرانی|song|music|melody|beat|track|album)", re.I)
_VIDEO = re.compile(r"(ویدیو|ویدئو|کلیپ|ڤیدیۆ|video|clip|animation|reel)", re.I)
_CODE = re.compile(
    r"(کد|برنامه\s*نویس|تابع|اسکریپت|باگ|کۆد|بەرنامە|code|function|script|bug|python|javascript|html|css|sql|api|regex|debug|compile|error.*code|class|def |import |from.*import)",
    re.I,
)
_REASON = re.compile(r"(حل کن|معادله|ریاضی|اثبات|منطق|چەند|solve|equation|math|prove|logic|calculate|compute|integrate|differentiate|factorial|probability|statistics)", re.I)
_CREATIVE = re.compile(r"(بنویس|شعر|داستان|ترانه|خلاقیت|write|poem|story|song|lyrics|creative|novel|essay|article|blog|script|dialogue|monologue)", re.I)
_TRANSLATE = re.compile(r"(ترجمه|وەرگێڕ|translate|แปล| tłumac|überse|traduire)", re.I)


def detect_intent(text: str) -> str:
    """دسته‌ی درخواست را برمی‌گرداند."""
    if not text:
        return "chat"
    if _IMG.search(text):
        return "image"
    if _MUSIC.search(text):
        return "music"
    if _VIDEO.search(text):
        return "video"
    if _CODE.search(text):
        return "code"
    if _REASON.search(text):
        return "reason"
    if _CREATIVE.search(text):
        return "creative"
    if _TRANSLATE.search(text):
        return "chat"
    return "chat"


def models_for(category: str) -> list:
    """زنجیره‌ی مدل برای یک دسته‌ی متنی."""
    return config.MODELS_BY_CATEGORY.get(category, config.CHAT_MODELS)
