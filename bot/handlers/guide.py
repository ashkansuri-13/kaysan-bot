"""راهنمای جامع کار با کیسان - برای کاربران جدید."""
from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery, Message

from ..keyboards import guide_kb, main_menu_kb, back_kb
from ..texts import t
from .. import database as db

router = Router()


GUIDE_TEXTS = {
    "ku": {
        "welcome": """📖 <b>ڕێنمای کیسان</b>

سڵاو {name}! 👋
من Kaysanم — دەستیارێکی زیرەک بە هوشی دەستکرد.

ئەم ڕێنما بۆ تۆیە کە زووتر فێر بیت چۆن بەکارم بهێنیت.

🎯 <b>چۆن دەست بکەیت:</b>
1️⃣ تەنها بنووسە یان دەنگ بنێسە
2️⃣ دکمەکان بکە بۆ کار جیاواز
3️⃣ هەر پرسیارێک بپرسە — من یارمەتیت دەدەم!

💡 <b>تێبینی گرنگ:</b>
- نیازی بۆ ئەوەی دستورات بنووسیت نییە
- تەنها پەیام بنێسە یان دکمە بکە
- من ٣ زمان تێدەگەم: کوردی، فارسی، ئینگلیزی

دۆزی ڕێنمای خۆت هەڵبژێرە! ⬇️""",
        "start": """🚀 <b>دەستپێکردن</b>

1️⃣ <b>زمان هەڵبژێرە:</b>
دکمەی ⚙️ بکە و زمان خۆت هەڵبژێرە

2️⃣ <b>پەیام بنێسە:</b>
تەنها بنووسە یان دەنگ بنێسە — من ئەنجام دەدەم!

3️⃣ <b>دکمە بکە:</b>
بۆ کاری تایبەت دکمە بکە

💡 <b>example:</b>
بنووسە: «سڵاو حالت چۆنه؟»
یان دکمەی 💬 بکە""",
        "chat": """💬 <b>چت کردن</b>

تەنها بنووسە یان دەنگ بنێسە!

📝 <b>example:</b>
- «سڵاو حالت چۆنه؟»
- «یارمەتیم بە لەم بابەتەدا»
- «بۆچی ئاسمان شینە؟»

🎯 <b>توانایییەکان:</b>
- گفتوگۆی زیرەک
- وەرگێڕان
- یارمەتی لە کار
- فێرکردن
- وەک هاوڕێ""",
        "image": """🎨 <b>دروستکردنی وێنە</b>

1️⃣ دکمەی 🎨 بکە
2️⃣ سبک هەڵبژێرە (واقعی، انیمیشنی، ...)
3️⃣ وەسفی وێنە بنووسە

📝 <b>example:</b>
- «وانەی گۆڕەیەک لە لێگەیەکی جوان»
- «گربەیەک بە چاوی شین»
- «ناوچەیەکی سروشتی لە کوردستان»""",
        "voice": """🎤 <b>ناردنی دەنگ</b>

1️⃣ دکمەی 🎤 بکە
2️⃣ دەنگ بنێسە
3️⃣ من گۆڕدەمە بۆ نووسین!

💡 <b>example:</b>
- دەنگ بنێسە بۆ چت کردن
- دەنگ بنێسە بۆ وەرگێڕان
- دەنگ بنێسە بۆ تۆمارکردن""",
        "tools": """🔧 <b>ئامرازەکان</b>

📱 <b>QR Code:</b> دروستکردنی QR
🔗 <b>کوتاه کردن لینک:</b> کورتکردنی URL
🧮 <b>ماشین حساب:</b> حیساب کردن
💱 <b>تبدیل ارز:</b> گۆڕینی پارە
🔑 <b>رمز عبور:</b> دروستکردنی وشەی نهێنی
📸 <b>اسکرینشات:</b> وێنەی وێبسایت
📊 <b>بۆرس:</b> نرخی بۆرس
🌤️ <b>کەش:</b> کەش و هەوا""",
        "group": """👥 <b>بەڕێوبرانەی گرووپ</b>

🔹 <b>خۆکار:</b>
- بەخێربێیتی نوێ
- فیلتر ئیسپام
- فیلتر وشە ناخۆشەکان

🔹 <b>دستی:</b>
- کوییزی گرووپ
- ئاماری گرووپ
- وەرگێڕانی خۆکار

📝 <b>example:</b>
بوت بۆ گرووپ زیاد بکە و دکمەی ⚙️ بکە""",
    },
    "fa": {
        "welcome": """📖 <b>راهنمای کیسان</b>

سلام {name}! 👋
من کیسانم — دستیار هوشمند شما با هوش مصنوعی.

این راهنما برای شماست تا زودتر یاد بگیرید چطور از من استفاده کنید.

🎯 <b>چطور شروع کنیم:</b>
1️⃣ فقط بنویسید یا صدا بفرستید
2️⃣ روی دکمه‌ها کلیک کنید
3️⃣ هر سوالی بپرسید — من کمک میکنم!

💡 <b>نکته مهم:</b>
- نیازی به تایپ دستورات نیست
- فقط پیام بفرستید یا دکمه بزنید
- من ۳ زبان بلدم: فارسی، کردی، انگلیسی

راهنمای خود را انتخاب کنید! ⬇️""",
        "start": """🚀 <b>شروع</b>

1️⃣ <b>زبان را انتخاب کنید:</b>
روی ⚙️ کلیک کنید و زبان خود را انتخاب کنید

2️⃣ <b>پیام بفرستید:</b>
فقط بنویسید یا صدا بفرستید — من جواب میدم!

3️⃣ <b>دکمه بزنید:</b>
برای کار خاص دکمه بزنید

💡 <b>مثال:</b>
بنویسید: «سلام حالت چطوره؟»
یا روی 💬 کلیک کنید""",
        "chat": """💬 <b>چت کردن</b>

فقط بنویسید یا صدا بفرستید!

📝 <b>مثال:</b>
- «سلام حالت چطوره؟»
- «کمکم کن در این موضوع»
- «چرا آسمان آبیه؟»

🎯 <b>توانایی‌ها:</b>
- گفتگوی هوشمند
- ترجمه
- کمک در کار
- آموزش
- مثل یک دوست""",
        "image": """🎨 <b>ساخت تصویر</b>

1️⃣ روی 🎨 کلیک کنید
2️⃣ سبک را انتخاب کنید (واقعی، انیمیشنی، ...)
3️⃣ توضیح تصویر را بنویسید

📝 <b>مثال:</b>
- «غروب زیبا در یک دریاچه»
- «گربه با چشم‌های آبی»
- «منظره طبیعی در کردستان»""",
        "voice": """🎤 <b>ارسال صدا</b>

1️⃣ روی 🎤 کلیک کنید
2️⃣ صدا بفرستید
3️⃣ من تبدیل میکنم به متن!

💡 <b>مثال:</b>
- صدا بفرستید برای چت کردن
- صدا بفرستید برای ترجمه
- صدا بفرستید برای یادداشت""",
        "tools": """🔧 <b>ابزارها</b>

📱 <b>QR Code:</b> ساخت QR
🔗 <b>کوتاه کردن لینک:</b> کوتاه کردن URL
🧮 <b>ماشین حساب:</b> محاسبه
💱 <b>تبدیل ارز:</b> تبدیل پول
🔑 <b>رمز عبور:</b> ساخت رمز
📸 <b>اسکرینشات:</b> عکس سایت
📊 <b>بورس:</b> قیمت سهام
🌤️ <b>آب و هوا:</b> وضعیت هوا""",
        "group": """👥 <b>مدیریت گروه</b>

🔹 <b>خودکار:</b>
- خوش‌آمدگویی جدید
- فیلتر اسپم
- فیلتر کلمات نامناسب

🔹 <b>دستی:</b>
- کوییز گروهی
- آمار گروه
- ترجمه خودکار

📝 <b>مثال:</b>
بات را به گروه اضافه کنید و روی ⚙️ کلیک کنید""",
    },
    "en": {
        "welcome": """📖 <b>Kaysan Guide</b>

Hello {name}! 👋
Im Kaysan — your smart AI assistant.

This guide helps you get started quickly.

🎯 <b>How to start:</b>
1️⃣ Just type or send voice
2️⃣ Tap the buttons
3️⃣ Ask anything — Im here to help!

💡 <b>Important:</b>
- No need to type commands
- Just send messages or tap buttons
- I speak 3 languages: Kurdish, Persian, English

Choose your guide! ⬇️""",
        "start": """🚀 <b>Getting Started</b>

1️⃣ <b>Choose language:</b>
Tap ⚙️ and select your language

2️⃣ <b>Send a message:</b>
Just type or send voice — I will answer!

3️⃣ <b>Tap buttons:</b>
Use buttons for specific tasks

💡 <b>Example:</b>
Type: "Hello, how are you?"
Or tap 💬""",
        "chat": """💬 <b>Chatting</b>

Just type or send a message!

📝 <b>Examples:</b>
- "Hello, how are you?"
- "Help me with this topic"
- "Why is the sky blue?"

🎯 <b>Abilities:</b>
- Smart conversation
- Translation
- Work assistance
- Learning
- Like a friend""",
        "image": """🎨 <b>Image Generation</b>

1️⃣ Tap 🎨
2️⃣ Choose style (realistic, anime, ...)
3️⃣ Describe the image

📝 <b>Examples:</b>
- "Beautiful sunset over a lake"
- "Cat with blue eyes"
- "Natural landscape in Kurdistan"""",
        "voice": """🎤 <b>Voice Messages</b>

1️⃣ Tap 🎤
2️⃣ Send a voice message
3️⃣ I will transcribe it!

💡 <b>Examples:</b>
- Send voice to chat
- Send voice to translate
- Send voice to take notes""",
        "tools": """🔧 <b>Tools</b>

📱 <b>QR Code:</b> Create QR
🔗 <b>Short Link:</b> Shorten URL
🧮 <b>Calculator:</b> Math calculations
💱 <b>Currency:</b> Convert money
🔑 <b>Password:</b> Generate password
📸 <b>Screenshot:</b> Website screenshot
📊 <b>Stocks:</b> Stock prices
🌤️ <b>Weather:</b> Weather forecast""",
        "group": """👥 <b>Group Management</b>

🔹 <b>Automatic:</b>
- Welcome new members
- Spam filter
- Bad words filter

🔹 <b>Manual:</b>
- Group quiz
- Group stats
- Auto translate

📝 <b>Example:</b>
Add bot to group and tap ⚙️""",
    }
}


@router.callback_query(F.data == "menu:help")
async def cb_guide(call: CallbackQuery):
    uid = call.from_user.id
    lang = await db.get_lang(uid)
    user = call.from_user
    
    texts = GUIDE_TEXTS.get(lang, GUIDE_TEXTS["fa"])
    welcome = texts["welcome"].format(name=user.first_name or user.full_name or "دوست")
    
    await call.message.edit_text(
        welcome,
        parse_mode=ParseMode.HTML,
        reply_markup=guide_kb(lang)
    )
    await call.answer()


@router.callback_query(F.data.startswith("guide:"))
async def cb_guide_section(call: CallbackQuery):
    uid = call.from_user.id
    lang = await db.get_lang(uid)
    section = call.data.split(":")[1]
    
    texts = GUIDE_TEXTS.get(lang, GUIDE_TEXTS["fa"])
    
    if section == "back":
        await call.message.edit_text(
            texts["welcome"].format(name=call.from_user.first_name or "دوست"),
            parse_mode=ParseMode.HTML,
            reply_markup=guide_kb(lang)
        )
    elif section in texts:
        await call.message.edit_text(
            texts[section],
            parse_mode=ParseMode.HTML,
            reply_markup=guide_kb(lang)
        )
    
    await call.answer()
