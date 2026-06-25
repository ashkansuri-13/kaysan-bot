# Kaysan AI Bot 🧠

**ربات هوش مصنوعی تلگرام — چت، جستجو، تصویر، ویس، مدیریت گروه، و ۸۰+ قابلیت دیگر**

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![License MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](docker-compose.yml)

---

## 🇮🇷 فارسی (Persian)

### معرفی

Kaysan AI یک ربات هوش مصنوعی تلگرام با بیش از ۸۰ قابلیت است. این ربات با استفاده از مدل‌های هوش مصنوعی مختلف (GPT, DeepSeek, Llama, Qwen, Gemma) کار می‌کند و از سه زبان فارسی، کردی سرانی و انگلیسی پشتیبانی می‌کند.

### قابلیت‌ها

#### 🤖 چت و هوش مصنوعی
- **چت هوشمند** با مدل‌های مختلف AI از طریق OpenRouter
- **تشخیص نیت** و انتخاب خودکار مدل مناسب (چت، کدنویسی، استدلال، خلاقیت)
- **پشتیبانی ۳ زبان**: کوردی سرانی، فارسی، انگلیسی
- **حالت‌های مختلف**: معلم، برنامه‌نویس، دوست
- **حافظه مکالمه** — ربات مکالمات قبلی رو به یاد داره
- **پشتیبانی از کانتکست طولانی** برای تحلیل اسناد بزرگ

#### 🎨 رسانه و تصویر
- **تبدیل ویس به متن** با دقت بالا (Groq Whisper)
- **تحلیل عکس** با مدل‌های Vision هوش مصنوعی
- **ساخت عکس با AI** — تولید تصویر از متن
- **تبدیل متن به عکس** — تبدیل متن به تصویر زیبا
- **ساخت میم** — تولید میم با متن دلخواه
- **تحلیل فایل** — پشتیبانی از PDF, DOCX, TXT, و فایل‌های متنی

#### 🔧 ابزارها (۲۰ ابزار)
| دستور | توضیح |
|-------|-------|
| `/qr` | ساخت QR Code |
| `/short` | کوتاه کردن لینک |
| `/screenshot` | اسکرینشات سایت |
| `/password` | ساخت رمز عبور تصادفی |
| `/calc` | ماشین حساب امن (بدون eval) |
| `/exchange` | تبدیل ارز |
| `/stock` | قیمت سهام و ارزهای دیجیتال |
| `/meme` | ساخت میم |
| `/invoice` | ساخت فاکتور |
| `/flashcard` | فلش کارت آموزشی |
| `/text2img` | تبدیل متن به عکس |
| `/weather` | آب و هوا |
| `/translate` | ترجمه ۳ زبانه |
| `/summarize` | خلاصه‌سازی متن |
| `/news` | اخبار لحظه‌ای |
| `/travel` | برنامه سفر |
| `/recipe` | دستور غذا |
| `/challenge` | چالش روزانه |
| `/expense` | ثبت هزینه |
| `/habit` | پیگیری عادت‌ها |

#### 👥 مدیریت گروه
- **خوش‌آمدگویی و وداع خودکار** — با قابلیت شخصی‌سازی متن
- **فیلتر اسپم** — حذف خودکار لینک‌های اسپم و تبلیغاتی
- **فیلتر کلمات نامناسب** — حذف پیام‌های با کلمات ممنوع
- **ضد Flood** — جلوگیری از ارسال پیام زیاد
- **Slow Mode** — تنظیم فاصله بین پیام‌ها
- **ساعات سکوت** — غیرفعال کردن ربات در ساعات مشخص
- **پنل مدیریت از پی‌وی** — مدیریت کامل گروه بدون نیاز به ادمین تلگرام
- **پاسخ خودکار به منشن** — جواب هوشمند به سؤالات
- **ترجمه خودکار** — ترجمه پیام‌های خارجی
- **پین خودکار** — پین کردن پیام‌های مهم
- **کوییز گروهی** — مسابقه دانستنی‌ها
- **نظرسنجی هوشمند** — نظرسنجی با AI
- **آمار گروه** — نمایش تعداد اعضا و فعالیت
- **قوانین گروه** — تنظیم و نمایش قوانین
- **گزارش پیام** — ارسال گزارش به ادمین‌ها
- **تگ همه اعضا** — ارسال پیام به همه

#### 🎮 سرگرمی
- **کوییز** — مسابقه دانستنی‌ها با گزینه‌های چهارگانه
- **معما** — معماهای جذاب و سرگرم‌کننده
- **لطیفه** — جoke‌های طنزآمیز
- **فال حافظ** — فال حافظ با تعبیر
- **بازی حدس عدد** — بازی سرگرم‌کننده
- **چالش روزانه** — چالش‌های متنوع هر روز

#### 🛡️ امنیت و پایداری
- **Rate Limiting** خودکار برای جلوگیری از سوءاستفاده
- **فیلتر اسپم و کلمات نامناسب**
- **Safe Math Calculator** — محاسبه امن ریاضی بدون eval
- **Circuit Breaker** — جلوگیری از خرابی زنجیره‌ای
- **پشتیبان** خودکار از دیتابیس
- **Health Check** و **Readiness Probe** برای مانیتورینگ
- **Prometheus Metrics** — مانیتورینگ پیشرفته

### نصب

#### روش ۱: Docker (پیشنهادی)

```bash
git clone https://github.com/mohamad1313m13-cyber/kaysan-bot.git
cd kaysan-bot
cp .env.example .env
# فایل .env رو ویرایش کنید
docker-compose up -d
```

#### روش ۲: دستی

```bash
git clone https://github.com/mohamad1313m13-cyber/kaysan-bot.git
cd kaysan-bot
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# فایل .env رو ویرایش کنید
python run.py
```

### تنظیمات

فایل `.env` رو با اطلاعات خودتون پر کنید:

```env
BOT_TOKEN=your_bot_token
OPENROUTER_KEY=your_openrouter_key
OWNER_ID=your_telegram_id
DEFAULT_LANG=fa
FREE_MESSAGE_LIMIT=100
```

### تست

```bash
pytest tests/ -v
pytest tests/ --cov=bot --cov-report=html
```

---

## 🇬🇧 English

### Introduction

Kaysan AI is a Telegram bot with 80+ features powered by multiple AI models (GPT, DeepSeek, Llama, Qwen, Gemma). It supports three languages: Kurdish Sorani, Persian, and English.

### Features

#### 🤖 AI Chat & Intelligence
- **Smart chat** with multiple AI models via OpenRouter
- **Intent detection** — automatically selects the best model (chat, code, reasoning, creative)
- **Trilingual support**: Kurdish Sorani, Persian, English
- **Multiple modes**: Teacher, Programmer, Friend
- **Conversation memory** — remembers previous messages
- **Long context support** for analyzing large documents

#### 🎨 Media & Images
- **Voice-to-text** transcription with high accuracy (Groq Whisper)
- **Image analysis** with AI Vision models
- **AI image generation** — create images from text prompts
- **Text-to-image** — convert text to beautiful images
- **Meme generator** — create custom memes
- **File analysis** — supports PDF, DOCX, TXT, and text files

#### 🔧 Tools (20 Tools)
| Command | Description |
|---------|-------------|
| `/qr` | Generate QR Code |
| `/short` | Shorten URL |
| `/screenshot` | Website screenshot |
| `/password` | Generate secure password |
| `/calc` | Safe calculator (no eval) |
| `/exchange` | Currency conversion |
| `/stock` | Stock & crypto prices |
| `/meme` | Create meme |
| `/invoice` | Generate invoice |
| `/flashcard` | Educational flashcards |
| `/text2img` | Text to image |
| `/weather` | Weather forecast |
| `/translate` | Trilingual translation |
| `/summarize` | Text summarization |
| `/news` | Breaking news |
| `/travel` | Trip planner |
| `/recipe` | Recipe suggestions |
| `/challenge` | Daily challenge |
| `/expense` | Expense tracker |
| `/habit` | Habit tracker |

#### 👥 Group Management
- **Auto welcome & goodbye** — with customizable messages
- **Spam filter** — auto-delete spam and promotional links
- **Bad words filter** — auto-delete inappropriate messages
- **Anti-flood** — prevent message flooding
- **Slow Mode** — set delay between messages
- **Quiet hours** — disable bot during specific hours
- **Admin panel from DM** — manage groups without Telegram admin
- **Auto-reply to mentions** — smart answers to questions
- **Auto-translate** — translate foreign messages automatically
- **Auto-pin** — pin important messages
- **Group quiz** — trivia competitions
- **Smart polls** — AI-powered polls
- **Group stats** — member count and activity
- **Group rules** — set and display rules
- **Message report** — send reports to admins
- **Tag all** — message all members

#### 🎮 Entertainment
- **Quiz** — trivia with multiple choice options
- **Riddles** — engaging brain teasers
- **Jokes** — funny and clean humor
- **Hafez Fal** — Persian poetry fortune
- **Number guessing game** — fun interactive game
- **Daily challenge** — varied daily challenges

#### 🛡️ Security & Reliability
- **Automatic Rate Limiting** to prevent abuse
- **Spam & bad words filtering**
- **Safe Math Calculator** — secure math without eval
- **Circuit Breaker** — prevent cascading failures
- **Automatic database backup**
- **Health Check & Readiness Probe** for monitoring
- **Prometheus Metrics** — advanced monitoring

### Installation

#### Option 1: Docker (Recommended)

```bash
git clone https://github.com/mohamad1313m13-cyber/kaysan-bot.git
cd kaysan-bot
cp .env.example .env
# Edit .env with your credentials
docker-compose up -d
```

#### Option 2: Manual

```bash
git clone https://github.com/mohamad1313m13-cyber/kaysan-bot.git
cd kaysan-bot
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
python run.py
```

### Configuration

Fill in `.env` with your credentials:

```env
BOT_TOKEN=your_bot_token
OPENROUTER_KEY=your_openrouter_key
OWNER_ID=your_telegram_id
DEFAULT_LANG=en
FREE_MESSAGE_LIMIT=100
```

### Testing

```bash
pytest tests/ -v
pytest tests/ --cov=bot --cov-report=html
```

---

## 🇰🇷 کوردی سرانی (Kurdish Sorani)

### پێناسەکردن

Kaysan AI botێکی تلەگرامە بە ٨٠+ تایبەتی، بە مۆدێلە جیاوازەکانی AI (GPT, DeepSeek, Llama, Qwen, Gemma) کاردەکات. سێ زمان پشتیبانی دەکات: کوردی سۆرانی، فارسی، و ئینگلیزی.

### تایبەتییەکان

#### 🤖 چت و زیرەکی دەستکرد
- **چتی زیرەک** بە مۆدێلە جیاوازەکانی AI لەڕێگای OpenRouter
- **دیاریکردنی نیت** — دۆزرینەوەی خۆکاری مۆدێلی گونجاو (چت، کۆد، بیرکردنەوە، دروستکردن)
- **پشتیبانی سێ زمان**: کوردی سۆرانی، فارسی، ئینگلیزی
- **دۆخە جیاوازەکان**: مامۆستا، بەرنامەنووس، هاوڕێ
- **بیرکردنەوەی گفتوگۆ** — bot قوڵانەی پێشوو بیردەکاتەوە
- **پشتیبانی کۆنتێکستی درێژ** بۆ شیکارکردنی بەڵگەنامەی گەورە

#### 🎨 میدیا و وێنە
- **گۆڕینی دەنگ بۆ نووسین** بە وردی بەرز (Groq Whisper)
- **شیکارکردنی وێنە** بە مۆدێلەکانی Vision
- **دروستکردنی وێنە بە AI** — دروستکردنی وێنە لە نووسین
- **گۆڕینی نووسین بۆ وێنە** — وەرگێڕانی نووسین بۆ وێنەی سروشت
- **دروستکردنی میم** — دروستکردنی میم بە نووسینی دڵخواست
- **شیکارکردنی فایل** — پشتیبانی PDF, DOCX, TXT

#### 🔧 ئامرازەکان (٢٠ ئامراز)
| فرمان | وەسف |
|-------|------|
| `/qr` | دروستکردنی QR Code |
| `/short` | کورتکردنی لینک |
| `/screenshot` | وێنەی وێبسایت |
| `/password` | دروستکردنی وشەی نهێنی |
| `/calc` | ماشین حسابی سەلامەت |
| `/exchange` | گۆڕینی پارە |
| `/stock` | نرخی بۆرس |
| `/meme` | دروستکردنی میم |
| `/invoice` | دروستکردنی فاکتۆر |
| `/flashcard` | فلش کارتی فێرکاران |
| `/text2img` | گۆڕینی نووسین بۆ وێنە |
| `/weather` | کەش و هەوا |
| `/translate` | وەرگێڕانی سێ زمان |
| `/summarize` | کورتکردنی نووسین |
| `/news` | هەواڵە |
| `/travel` | پلانی سەفەر |
| `/recipe` | ئامرازی خواردن |
| `/challenge` | بیرنەرەی ڕۆژانە |
| `/expense` | تۆمارکردنی خرج |
| `/habit` | شێوە |

#### 👥 بەڕێوبرانەی گرووپ
- **بەخێربێیت و دەستپێشکەری خۆکار** — بە تایبەتیکردنی نووسین
- **فیلترکردنی ئیسپام** — حذفکردنی خۆکاری لینکەکانی ئیسپام
- **فیلترکردنی وشە ناخۆشەکان** — حذفکردنی پەیام ناخۆشەکان
- **ضد Flood** —ڕێگری لە بنارکردنی زۆر پەیام
- **Slow Mode** — ڕێکخستنی نێوان پەیامەکان
- **کاتە بێدەنگەکان** — ناچالاکردنی bot لە کاتی دیاریکراو
- **پنێلی بەڕێوبرانە** — بەڕێوبرانەی تەواوی گرووپ
- **وەڵامی خۆکار بە منشن** — وەڵامی زیرەک بە پرسیارەکان
- **وەرگێڕانی خۆکار** — وەرگێڕانی پەیامە پارێزراوەکان
- **پینکردنی خۆکار** — پینکردنی پەیام گرنگەکان
- **کوییزی گرووپ** — یاریی زانست
- **دەنگدانی زیرەک** — دەنگدان بە AI
- **ئاماری گرووپ** — ژمارەی ئەندامان
- **ڕێکخراوەکانی گرووپ** — ڕێکخستن و پیشاندانی ڕێکخراوەکان
- **ڕاپۆرتکردنی پەیام** — ناردنی ڕاپۆرت بۆ بەڕێوان
- **تەگکردنی هەموو** — ناردنی پەیام بۆ هەموو

#### 🎮 خۆشییەکان
- **کوییز** — یاریی زانست بە گزینەی چوارگانە
- **مەزەڵ** — مەزەڵە خۆشەکان
- **لوطیفە** — لوطیفەی سەرسوڕهێنەر
- **فالی حەڤیز** — فال حەڤیز بە تەعبیر
- **یاریی ژمێر** — یاریی خۆش
- **بیرنەرەی ڕۆژانە** — بیرنەرە جیاوازە ڕۆژانە

#### 🛡️ ئاسایش و بەرگری
- **Rate Limiting** خۆکار بۆ ڕێگری لە بەکارهێنانی خراپ
- **فیلترکردنی ئیسپام و وشە ناخۆشەکان**
- **ماشین حسابی سەلامەت** — بیرکردنەوە بە سەلامەتی بێ eval
- **Circuit Breaker** — ڕێگری لە خراپی زنجیرەیی
- **بەکڵێنەوەی خۆکار** — بەکڵێنەوەی دیتابەیس
- **Health Check و Readiness Probe** بۆ مۆنیتورینگ
- **Prometheus Metrics** — مۆنیتورینگی پێشکەوتوو

### دامەزراندن

#### شێوازی ١: Docker (پێشنیارکراو)

```bash
git clone https://github.com/mohamad1313m13-cyber/kaysan-bot.git
cd kaysan-bot
cp .env.example .env
# فایل .env بگۆڕە
docker-compose up -d
```

#### شێوازی ٢: بە دست

```bash
git clone https://github.com/mohamad1313m13-cyber/kaysan-bot.git
cd kaysan-bot
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# فایل .env بگۆڕە
python run.py
```

### ڕێکخستن

فایل `.env` بە زانیاریی خۆت پڕ بکە:

```env
BOT_TOKEN=your_bot_token
OPENROUTER_KEY=your_openrouter_key
OWNER_ID=your_telegram_id
DEFAULT_LANG=ku
FREE_MESSAGE_LIMIT=100
```

### تاقیکردنەوە

```bash
pytest tests/ -v
pytest tests/ --cov=bot --cov-report=html
```

---

## 📁 Project Structure / پێکهاتەی پڕۆژێکت

```
kaysan-bot/
├── run.py                  # Entry point
├── bot/
│   ├── config.py           # Configuration
│   ├── database.py         # SQLite database
│   ├── router.py           # Language & intent detection
│   ├── openrouter.py       # OpenRouter API client
│   ├── keyboards.py        # Telegram keyboards
│   ├── texts.py            # Trilingual texts
│   ├── middleware.py        # Rate limiting
│   ├── health.py           # Health check
│   ├── metrics.py          # Prometheus metrics
│   ├── circuit_breaker.py  # Circuit breaker
│   ├── backup.py           # Database backup
│   ├── handlers/           # Command handlers
│   │   ├── core.py         # Core processing
│   │   ├── chat.py         # Text chat
│   │   ├── media.py        # Voice & images
│   │   ├── search.py       # Web search
│   │   ├── groups.py       # Group features
│   │   ├── panel.py        # Admin panel
│   │   ├── tools.py        # 20 utility tools
│   │   ├── quiz.py         # Quiz & trivia
│   │   ├── translate.py    # Translation
│   │   └── extras.py       # Extra features
│   └── services/
│       ├── voice.py        # Voice transcription
│       ├── image.py        # Image generation
│       └── tts.py          # Text to speech
├── tests/                  # Test suite
├── web/                    # Web interface
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## 🔧 Environment Variables / متغیرهای محیطی

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BOT_TOKEN` | ✅ | - | Telegram bot token |
| `OPENROUTER_KEY` | ✅ | - | OpenRouter API key |
| `OWNER_ID` | ✅ | - | Owner Telegram ID |
| `DEFAULT_LANG` | ❌ | `ku` | Default language (ku/fa/en) |
| `FREE_MESSAGE_LIMIT` | ❌ | `100` | Free message limit |
| `DAILY_COST_LIMIT` | ❌ | `5.0` | Daily cost limit ($) |
| `CHANNEL_USERNAME` | ❌ | - | Required channel |
| `GROQ_API_KEY` | ❌ | - | Groq API key (voice) |
| `REDIS_URL` | ❌ | - | Redis URL (cache) |
| `SENTRY_DSN` | ❌ | - | Sentry DSN (errors) |

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
