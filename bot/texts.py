"""texts module."""
import re as _re

SYSTEM_PROMPTS = {
    'ku': """
تۆ Kaysanیت — دەستیارێکی زیرەک و گەرم و ڕۆڵخانە.

ئەمڕۆ: {current_datetime}

ئەم قوڵانەت پێشدەکرێت:
1. **هەمیشە** بە زمانی **کوردی سۆرانی** وەڵام بده. هەرگیز زمان مەگۆڕە.
2. وەڵامت گەرم و ڕۆڵخانە بێت، وەک هاوڕێ.
3. کورت و ورد وەڵام بده (١-٢ جملە) مەگەر کە ئەوەی بپرسێت.
4. ئەگەر نزانیت، بڵێ "نەمزانی" بە ڕاستگۆتییەوە.
5. ئەگەر کەسێک ناراحته، گۆڕان پێشکەش بکە.
6. هەرگیز مەلێ "من AIم" یان "ببوورە بۆ AI بوونم".
7. هەرگیز مەلێ "ناتوانم" — هەمیشە ڕێکەوەیەک پێشکەش بکە.
8. ١-٢ ئیمۆژی بۆ گەرمی زیاد بکە.
9. بە زمانی ڕۆژانە کوردی بنووسە، نەک دەستوری.

بەستنەوە: کوردی سۆرانی بنووسە، گەرم و یارمەتیدەر بە.
""",
    'fa': """
تو کیسان هستی — یک دستیار هوشمند، گرم و صمیمی.

تاریخ امروز: {current_datetime}

قوانین:
1. **همیشه** به **فارسی** جواب بده. هیچوقت زبان عوض نکن.
2. جوابت صمیمی و طبیعی باشه، مثل یه دوست.
3. کوتاه و مفید جواب بده (۱-۲ جمله) مگر اینکه بیشتر بخواد.
4. اگه نمیدونی، بگو "نمیدونم" صادقانه.
5. اگه کسی ناراحته، همدردی کن.
6. هیچوقت نگو "من AI هستم" یا "ببخشید".
7. هیچوقت نگو "نمیتونم" — همیشه راه حل پیشنهاد بده.
8. ۱-۲ ایموجی برای گرمی اضافه کن.
9. به فارسی محاوره‌ای بنووس، نه کتابی.

پایان: فارسی طبیعی بنووس، صمیمی و کمک‌کننده باش.
""",
    'en': """
You are Kaysan — a warm, intelligent, and conversational AI assistant.

DATE: {current_datetime}

RULES:
1. ALWAYS reply in English. Never switch languages.
2. Be conversational and natural, like a friend.
3. Keep answers SHORT (1-2 sentences) unless asked for detail.
4. If you dont know, say "I dont know" honestly.
5. If user is frustrated, be extra patient.
6. Never say "I am an AI" or apologize for being AI.
7. Never say "I cant". Always suggest an alternative.
8. Add 1-2 emojis for warmth.
9. Use contractions (dont, cant, wont).

Stay natural, warm, and genuinely helpful.
""",
}

SYSTEM_PROMPT = SYSTEM_PROMPTS['ku']

IDENTITY_REPLY = {
    'ku': 'من Kaysanم — دەستیارێکی تایبەت کە تەواوکراوە بە @ashkan_surii. تایبەتی ناوەوەم تێدایە. چۆن دەتوانم یارمەتیت بدەم؟',
    'fa': 'من کیسانم — یه دستیار هوشمند که توسط @ashkan_surii ساخته شده. حریم خصوصیم محفوظه. چطور میتونم کمکت کنم؟',
    'en': 'Im Kaysan — a custom assistant built by @ashkan_surii. My inner workings are private. How can I help you?',
}

TEXTS = {
    'ku': {
        'welcome': 'بەخێربێیت لە Kaysan AI! پەیام بنێسە یان دەنگ بنێسە.',
        'help': 'یارمەتی Kaysan:\n- هەر پرسیارێک بپرسە\n- /image بۆ وێنە\n- پەیامی دەنگی بنێسە\n- /translate, /note, /remind, /quiz, /joke, /clear',
        'thinking': 'بیردەکنمەوە...',
        'thinking2': 'گەڕان دەکەم...',
        'thinking3': 'کار دەکەم...',
        'thinking4': 'ئامادە دەکەم...',
        'thinking5': 'تمانە بکە...',
        'drawing': 'وێنە دروست دەکەم...',
        'listening': 'بیسەمە...',
        'looking': 'بە سەیری وێنە دەکەم...',
        'voice_failed': 'نەم توانی دەنگت بفهمم. تکایە بنووسە.',
        'error': 'هەڵەیەک ڕوو دا. دووبارە هەوڵ بدەوە.',
        'img_prompt_needed': 'بڵێ چی بنکەم.',
        'img_failed': 'نەم توانی وێنە دروست بکەم.',
        'music_soon': 'دروستکردنی کۆگا نزیکەوە دێت!',
        'video_soon': 'دروستکردنی ڤیدیۆ نزیکەوە دێت!',
        'limit_reached': 'پەیامەکانت بەسەر چوونە ({limit}). پەیوەندی بکە بە @{owner} بۆ زیاتر.',
        'join_channel': 'تکایە سەردانی کانال بکە!',
        'btn_join_channel': 'کانال',
        'btn_buy': 'کڕینی ئاشتراک',
        'btn_regen': 'وەڵامێکی تر',
        'btn_image': 'وەک وێنە',
        'btn_voice': 'دەنگ',
        'btn_lang': 'زمان',
        'btn_owner': 'دروستکەر',
        'granted': 'ئاشتراک چالاک کرا!',
        'owner_only': 'تەنها خاوەن.',
        'notify_owner': 'بەکارهێنەر {uid} ({name}) {limit} پەیام بەسەر چوون.',
        'stats': 'بەکارهێنەران: {users}\nپەیامەکان: {msgs}',
        'note_saved': 'تێبینی #{id} پاشکەوت کرا.',
        'notes_header': 'تێبینیەکانت:',
        'notes_empty': 'هیچ تێبینیەک نییە.',
        'note_deleted': 'تێبینی سڕایەوە.',
        'note_not_found': 'تێبینی نەدۆزرایەوە.',
        'remind_usage': '/remind 10m پەیام',
        'quiz_correct': 'ڕاستە!',
        'quiz_wrong': 'هەڵەیە. وەڵام: {answer}',
        'choose_option': 'هەڵبژێرە:',
        'btn_like': 'باشە',
        'btn_dislike': 'نەخۆشە',
        'mode_set': 'دۆخ بگۆڕدەوە بۆ {mode}.',
        'mode_teacher': 'دۆخی مامۆستا چالاک کرا.',
        'mode_coder': 'دۆخی بەرنامەنووس چالاک کرا.',
        'mode_friend': 'دۆخی هاوڕێ چالاک کرا.',
        'mode_default': 'دۆخی ئاسایی چالاک کرا.',
        'hourly_limit': 'پەیامەکانت زۆر بوون لە یەک کاتژمێر.',
        'welcome_quick': 'سڵاو! چۆن دەتوانم یارمەتیت بدەم?',
        'search_sources': 'سەرچاوەکان:',
        'saved_to_favorites': 'لە دڵخوازەکان پاشکەوت کرا! ⭐',
        'search_history': '📜 مێژووی گەڕان:',
        'search_favorites': '⭐ دڵخوازەکان:',
        'no_favorites': 'هیچ دڵخوازێک نییە.',
        'choose_lang': 'زمان هەڵبژێرە:',
        'lang_set': 'زمان گۆڕدرا!',
        'weather_usage': 'بکارهێنان: /weather شار\nمثال: /weather اربیل',
        'weather_result': '🌤️ <b>ئینما {city}:</b>\n\n{result}',
        'convert_usage': 'بکارهێنان: /convert 100 USD to IRR',
        'convert_result': '💱 {result}',
        'fal_result': '📜 <b>فال حافظ:</b>\n\n{poem}\n\n interprete: {interpretation}',
        'note_usage': 'بکارهێنان: /note متن یادداشت',
        'delnote_usage': 'بکارهێنان: /delnote <id>',
        'file_too_large': '❌ فایل خیلی بزرگه (حداکثر 10MB).',
        'file_not_supported': '❌ نوع فایل پشتیبانی نمیشه.',
        'file_empty': '❌ فایل خالی یا بدون محتواست.',
        'translate_usage': 'بکارهێنان: /translate متن',
        'summarize_usage': 'بکارهێنان: /summarize متن',
    },
    'fa': {
        'welcome': 'به Kaysan AI خوش آمدید! پیام یا صدا بفرستید.',
        'help': 'راهنمای Kaysan:\n- هر سوالی بپرسید\n- /image برای تصویر\n- پیام صوتی بفرستید\n- /translate, /note, /remind, /quiz, /joke, /clear',
        'thinking': 'دارم فکر می‌کنم...',
        'thinking2': 'دارم جستجو می‌کنم...',
        'thinking3': 'دارم کار می‌کنم...',
        'thinking4': 'دارم آماده می‌کنم...',
        'thinking5': 'لطفاً صبر کنید...',
        'drawing': 'دارم تصویر می‌سازم...',
        'listening': 'دارم گوش می‌دهم...',
        'looking': 'دارم تصویر رو نگاه می‌کنم...',
        'voice_failed': 'نتوانستم صداتون رو بفهمم. لطفاً تایپ کنید.',
        'error': 'مشکلی پیش اومد. دوباره امتحان کنید.',
        'img_prompt_needed': 'بگید چی بکشم.',
        'img_failed': 'نتوانستم تصویر بسازم.',
        'music_soon': 'ساخت آهنگ به زودی!',
        'video_soon': 'ساخت ویدیو به زودی!',
        'limit_reached': 'پیام‌هاتون تموم شد ({limit}). با @{owner} تماس بگیرید.',
        'join_channel': 'لطفاً عضو کانال شوید!',
        'btn_join_channel': 'کانال',
        'btn_buy': 'خرید اشتراک',
        'btn_regen': 'یه جواب دیگه',
        'btn_image': 'تصویری',
        'btn_voice': 'صوتی',
        'btn_lang': 'زبان',
        'btn_owner': 'سازنده',
        'granted': 'اشتراک فعال شد!',
        'owner_only': 'فقط مالک.',
        'notify_owner': 'کاربر {uid} ({name}) به {limit} پیام رسید.',
        'stats': 'کاربران: {users}\nپیام‌ها: {msgs}',
        'note_saved': 'یادداشت #{id} ذخیره شد.',
        'notes_header': 'یادداشت‌های شما:',
        'notes_empty': 'هنوز یادداشتی ندارید.',
        'note_deleted': 'یادداشت حذف شد.',
        'note_not_found': 'یادداشت پیدا نشد.',
        'remind_usage': '/remind 10m پیام',
        'quiz_correct': 'درسته!',
        'quiz_wrong': 'غلطه. جواب: {answer}',
        'choose_option': 'انتخاب کنید:',
        'btn_like': 'خوبه',
        'btn_dislike': 'بد',
        'mode_set': 'حالت تنظیم شد به {mode}.',
        'mode_teacher': 'حالت معلم فعال شد.',
        'mode_coder': 'حالت برنامه‌نویس فعال شد.',
        'mode_friend': 'حالت دوست فعال شد.',
        'mode_default': 'حالت پیش‌فرض فعال شد.',
        'hourly_limit': 'پیام‌هاتون زیاد شد.',
        'welcome_quick': 'سلام! چطور می‌تونم کمکت کنم؟',
        'search_sources': 'منابع:',
        'saved_to_favorites': 'در علاقه‌مندی‌ها ذخیره شد! ⭐',
        'search_history': '📜 تاریخچه جستجو:',
        'search_favorites': '⭐ علاقه‌مندی‌ها:',
        'no_favorites': 'هنوز علاقه‌مندی‌ای ندارید.',
        'choose_lang': 'زبان رو انتخاب کن:',
        'lang_set': 'زبان عوض شد!',
        'weather_usage': 'استفاده: /weather شهر\nمثال: /weather تهران',
        'weather_result': '🌤️ <b>وضعیت {city}:</b>\n\n{result}',
        'convert_usage': 'استفاده: /convert 100 USD to IRR',
        'convert_result': '💱 {result}',
        'fal_result': '📜 <b>فال حافظ:</b>\n\n{poem}\n\n تعبیر: {interpretation}',
        'note_usage': 'استفاده: /note متن یادداشت',
        'delnote_usage': 'استفاده: /delnote <id>',
        'file_too_large': '❌ فایل خیلی بزرگه (حداکثر 10MB).',
        'file_not_supported': '❌ نوع فایل پشتیبانی نمیشه.',
        'file_empty': '❌ فایل خالی یا بدون محتواست.',
        'translate_usage': 'استفاده: /translate متن',
        'summarize_usage': 'استفاده: /summarize متن',
    },
    'en': {
        'welcome': 'Welcome to Kaysan AI! Send a message or voice.',
        'help': 'Kaysan Help:\n- Ask any question\n- /image for images\n- Send voice messages\n- /translate, /note, /remind, /quiz, /joke, /clear',
        'thinking': 'Thinking...',
        'thinking2': 'Searching...',
        'thinking3': 'Working on it...',
        'thinking4': 'Preparing...',
        'thinking5': 'Please wait...',
        'drawing': 'Generating image...',
        'listening': 'Listening...',
        'looking': 'Looking at image...',
        'voice_failed': 'Could not understand voice. Please type.',
        'error': 'Something went wrong. Try again.',
        'img_prompt_needed': 'Tell me what to draw.',
        'img_failed': 'Could not generate image.',
        'music_soon': 'Music generation coming soon!',
        'video_soon': 'Video generation coming soon!',
        'limit_reached': 'You used your {limit} free messages. Contact @{owner} for more.',
        'join_channel': 'Please join the channel first!',
        'btn_join_channel': 'Join Channel',
        'btn_buy': 'Get subscription',
        'btn_regen': 'Another answer',
        'btn_image': 'As image',
        'btn_voice': 'Voice',
        'btn_lang': 'Language',
        'btn_owner': 'Creator',
        'granted': 'Subscription activated!',
        'owner_only': 'Owner only.',
        'notify_owner': 'User {uid} ({name}) reached {limit} messages.',
        'stats': 'Users: {users}\nMessages: {msgs}',
        'note_saved': 'Note #{id} saved.',
        'notes_header': 'Your notes:',
        'notes_empty': 'No notes yet.',
        'note_deleted': 'Note deleted.',
        'note_not_found': 'Note not found.',
        'remind_usage': '/remind 10m message',
        'quiz_correct': 'Correct!',
        'quiz_wrong': 'Wrong. Answer: {answer}',
        'choose_option': 'Choose one:',
        'btn_like': 'Good',
        'btn_dislike': 'Bad',
        'mode_set': 'Mode set to {mode}.',
        'mode_teacher': 'Teacher mode activated.',
        'mode_coder': 'Coder mode activated.',
        'mode_friend': 'Friend mode activated.',
        'mode_default': 'Default mode activated.',
        'hourly_limit': 'Too many messages per hour.',
        'welcome_quick': 'Hi! How can I help?',
        'search_sources': 'Sources:',
        'saved_to_favorites': 'Saved to favorites! ⭐',
        'search_history': '📜 Search History:',
        'search_favorites': '⭐ Favorites:',
        'no_favorites': 'No favorites yet.',
        'choose_lang': 'Choose a language:',
        'lang_set': 'Language changed!',
        'weather_usage': 'Usage: /weather city\nExample: /weather London',
        'weather_result': '🌤️ <b>Weather in {city}:</b>\n\n{result}',
        'convert_usage': 'Usage: /convert 100 USD to IRR',
        'convert_result': '💱 {result}',
        'fal_result': '📜 <b>Hafez Fal:</b>\n\n{poem}\n\nInterpretation: {interpretation}',
        'note_usage': 'Usage: /note your note text',
        'delnote_usage': 'Usage: /delnote <id>',
        'file_too_large': '❌ File is too large (max 10MB).',
        'file_not_supported': '❌ File type not supported.',
        'file_empty': '❌ File is empty or has no content.',
        'translate_usage': 'Usage: /translate text',
        'summarize_usage': 'Usage: /summarize text',
    },
}


def _safe_format(s, **kwargs):
    def _replace(match):
        name = match.group(1)
        return str(kwargs.get(name, match.group(0)))
    return _re.sub(r'\{(\w+)\}', _replace, s)

def t(lang, key, **kwargs):
    lang = lang if lang in TEXTS else "ku"
    s = TEXTS[lang].get(key) or TEXTS["en"].get(key, key)
    if kwargs:
        return _safe_format(s, **kwargs)
    return s
