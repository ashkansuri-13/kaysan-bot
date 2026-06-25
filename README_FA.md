<div align="center">

# 🧠 ربات هوش مصنوعی کیسان

**ربات تلگرام با ۶۰+ قابلیت**

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](docker-compose.yml)
[![Tests](https://img.shields.io/badge/Tests-829+-brightgreen?style=for-the-badge)](tests/)
[![Aiogram](https://img.shields.io/badge/Aiogram-3-0077B5?style=for-the-badge&logo=python&logoColor=white)](https://docs.aiogram.dev/)

[فارسی](README_FA.md) | [English](README_EN.md) | [کوردی](README_KU.md)

</div>

---

## 📸 اسکرین‌شات‌ها

> اسکرین‌شات‌ها به زودی اضافه میشن! برای دیدن ربات در عمل به کانال ما بپیوندید: [@ashkan_surii](https://t.me/ashkan_surii)

| چت | مدیریت گروه | مینی اپ |
|-----|-----------|---------|
| *مکالمات هوشمند با AI* | *مدیریت خودکار و ابزارها* | *رابط کاربری مدرن* |

---

## 🏗️ تکنولوژی‌ها

| لایه | تکنولوژی |
|------|---------|
| **زبان** | Python 3.12 |
| **فریمورک بات** | Aiogram 3 |
| **دیتابیس** | SQLite (حالت WAL) |
| **کش** | Redis |
| **ارائه‌دهنده AI** | OpenRouter |
| **صدا** | Groq Whisper |
| **کانتینر** | Docker |
| **مانیتورینگ** | Prometheus |
| **سرور وب** | aiohttp |

---

## 🏛️ معماری

```
┌─────────────┐
│  تلگرام     │
│  کاربران     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Aiogram 3  │  ← روتیر پیام
│  Dispatcher │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  هندلرها    │  ← ۲۰+ هندلر دستورات
│  و فیلترها  │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐
│  موتور AI   │────▶│  OpenRouter │
│  (نیت)      │     │  چند مدلی   │
└──────┬──────┘     └─────────────┘
       │
       ▼
┌─────────────┐
│  دیتابیس    │  ← اطلاعات کاربران
│  SQLite     │
└─────────────┘
```

---

## ✨ قابلیت‌ها

### 🤖 چت و هوش مصنوعی
- **چت چند مدلی** — GPT, DeepSeek, Llama, Qwen, Gemma از طریق OpenRouter
- **تشخیص نیت** — انتخاب خودکار بهترین مدل
- **پشتیبانی ۳ زبان** — کوردی سرانی، فارسی، انگلیسی
- **حالت‌های مختلف** — معلم، برنامه‌نویس، دوست
- **حافظه مکالمه** — به یاد آوردن زمینه پیام‌ها
- **پاسخ‌های استریم** — خروجی بلادرنگ AI

### 🎨 رسانه و تصویر
- **تبدیل ویس به متن** — تبدیل با دقت بالا (Groq Whisper)
- **تحلیل عکس** — توصیف و تحلیل تصاویر با AI
- **ساخت عکس با AI** — تولید تصویر از متن
- **تبدیل متن به عکس** — تبدیل متن به تصویر زیبا
- **ساخت میم** — تولید میم سفارشی
- **تحلیل فایل** — پشتیبانی از PDF, DOCX, TXT

### 🔧 ۲۰+ ابزار کاربردی

| دستور | توضیح |
|-------|-------|
| `/qr` | ساخت QR Code |
| `/short` | کوتاه کردن لینک |
| `/screenshot` | اسکرینشات سایت |
| `/password` | ساخت رمز عبور |
| `/calc` | ماشین حساب امن |
| `/exchange` | تبدیل ارز |
| `/stock` | قیمت سهام و ارز دیجیتال |
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

### 👥 مدیریت گروه
- **خوش‌آمدگویی و وداع خودکار** — با قابلیت شخصی‌سازی
- **فیلتر اسپم** — حذف خودکار لینک‌های اسپم
- **فیلتر کلمات نامناسب** — حذف پیام نامناسب
- **ضد Flood** — جلوگیری از پیام زیاد
- **Slow Mode** — فاصله بین پیام‌ها
- **ساعات سکوت** — غیرفعال در ساعات خاص
- **پنل مدیریت از پی‌وی** — مدیریت بدون ادمین تلگرام
- **پاسخ خودکار به منشن** — جواب هوشمند
- **ترجمه خودکار** — ترجمه پیام خارجی
- **کوییز گروهی** — مسابقه دانستنی
- **آمار گروه** — تعداد اعضا و فعالیت
- **تگ همه** — ارسال پیام به همه

### 👑 پنل ادمین
- **مدیریت کاربران** — مشاهده، بن، آنبند
- **ارسال پیام همگانی** — ارسال به همه کاربران
- **آمار استفاده** — ردیابی پیام‌ها، هزینه‌ها
- **مدیریت اشتراک** — اعطای دسترسی ویژه
- **کنترل مدل AI** — تست و مانیتورینگ
- **مانیتورینگ سیستم** — بررسی سلامت و آپتایم
- **کنترل بکاپ** — مدیریت پشتیبان دیتابیس

### 🎮 سرگرمی
- **کوییز** — مسابقه دانستنی
- **معما** — معماهای جذاب
- **لطیفه** — جoke‌های طنز
- **فال حافظ** — فال با تعبیر
- **بازی حدس عدد** — بازی تعاملی
- **چالش روزانه** — چالش‌های متنوع

### 🛡️ امنیت و پایداری
- **Rate Limiting** — جلوگیری از سوءاستفاده (۳۰ درخواست/دقیقه)
- **فیلتر اسپم و کلمات نامناسب**
- **Safe Math Calculator** — محاسبه امن بدون eval
- **Circuit Breaker** — جلوگیری از خرابی زنجیره‌ای
- **پشتیبان خودکار** از دیتابیس
- **Health Check** — پورت ۸۰۸۰
- **Prometheus Metrics** — پورت ۹۰۹۰

---

## 🔌 یکپارچه‌سازی‌ها

| سرویس | کاربرد |
|-------|--------|
| **OpenRouter** | AI چند مدلی (GPT, DeepSeek, Llama, Qwen, Gemma) |
| **Groq Whisper** | تبدیل صدا با دقت بالا |
| **Telegram Bot API** | ارتباط بات و مینی اپ |
| **Redis** | کش و ذخیره جلسه |
| **Prometheus** | متریک و مانیتورینگ |
| **Sentry** | ردیابی خطا (اختیاری) |

---

## 🚀 نصب

### نصب یک خطی

```bash
bash <(curl -s https://raw.githubusercontent.com/ashkansuri-13/kaysan-bot/master/install.sh)
```

### Docker (پیشنهادی)

```bash
git clone https://github.com/ashkansuri-13/kaysan-bot.git
cd kaysan-bot
cp .env.example .env
docker-compose up -d
```

### دستی

```bash
git clone https://github.com/ashkansuri-13/kaysan-bot.git
cd kaysan-bot
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python run.py
```

---

## ⚙️ تنظیمات

فایل `.env` رو بسازید:

```env
BOT_TOKEN=توکن_بات
OPENROUTER_KEY=کلید_اپن‌روتر
OWNER_ID=آیدی_مالک
DEFAULT_LANG=fa
FREE_MESSAGE_LIMIT=100
DAILY_COST_LIMIT=5.0
CHANNEL_USERNAME=نام_کانال
GROQ_API_KEY=کلید_گروک
REDIS_URL=redis://localhost:6379/0
SENTRY_DSN=dsn_سنتری
```

---

## 🧪 تست

```bash
# اجرای ۸۲۹ تست
pytest tests/ -v

# اجرا با کاوریج
pytest tests/ --cov=bot --cov-report=html
```

---

## 📁 ساختار پروژه

```
kaysan-bot/
├── run.py                  # نقطه ورود
├── bot/
│   ├── config.py           # تنظیمات
│   ├── database.py         # دیتابیس SQLite (۱۶ جدول)
│   ├── router.py           # تشخیص زبان و نیت
│   ├── openrouter.py       # کلاینت OpenRouter
│   ├── keyboards.py        # کیبوردهای تلگرام
│   ├── texts.py            # متن‌های ۳ زبانه
│   ├── middleware.py        # Rate Limiting
│   ├── health.py           # Health Check (پورت ۸۰۸۰)
│   ├── metrics.py          # Prometheus (پورت ۹۰۹۰)
│   ├── circuit_breaker.py  # Circuit Breaker
│   ├── backup.py           # پشتیبان دیتابیس
│   ├── handlers/           # ۲۰+ هندلر
│   │   ├── core.py         # پردازش اصلی AI
│   │   ├── chat.py         # چت متنی
│   │   ├── media.py        # ویس و تصویر
│   │   ├── search.py       # جستجوی وب
│   │   ├── groups.py       # مدیریت گروه
│   │   ├── panel.py        # پنل ادمین
│   │   ├── tools.py        # ۲۰+ ابزار
│   │   ├── quiz.py         # کوییز
│   │   ├── translate.py    # ترجمه
│   │   ├── notes.py        # یادداشت
│   │   ├── remind.py       # یادآوری
│   │   ├── extras.py       # قابلیت‌های اضافی
│   │   └── webapp.py       # مینی اپ تلگرام
│   └── services/
│       ├── voice.py        # تبدیل صدا (Groq)
│       ├── image.py        # تولید تصویر
│       └── tts.py          # تبدیل متن به صدا
├── tests/                  # ۵۵ فایل تست، ۸۲۹ تست
├── web/                    # رابط وب (Glassmorphism)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## 🔧 متغیرهای محیطی

| متغیر | ضروری | پیش‌فرض | توضیح |
|-------|-------|---------|-------|
| `BOT_TOKEN` | ✅ | - | توکن ربات تلگرام |
| `OPENROUTER_KEY` | ✅ | - | کلید OpenRouter |
| `OWNER_ID` | ✅ | - | آیدی مالک |
| `DEFAULT_LANG` | ❌ | `ku` | زبان پیش‌فرض (ku/fa/en) |
| `FREE_MESSAGE_LIMIT` | ❌ | `100` | حد پیام رایگان |
| `DAILY_COST_LIMIT` | ❌ | `5.0` | حد هزینه روزانه |
| `CHANNEL_USERNAME` | ❌ | - | کانال اجباری |
| `GROQ_API_KEY` | ❌ | - | کلید Groq (صدا) |
| `REDIS_URL` | ❌ | - | آدرس Redis |
| `SENTRY_DSN` | ❌ | - | DSN سنتری |

---

## 🤖 مدل‌های هوش مصنوعی

| مدل | ارائه‌دهنده | کاربرد |
|-----|-----------|--------|
| `mimo/mimo-auto` | Xiaomi MiMo | اصلی |
| `deepseek/deepseek-chat` | DeepSeek | جایگزین |
| `openai/gpt-4o-mini` | OpenAI | جایگزین |
| `anthropic/claude-haiku-4.5` | Anthropic | جایگزین |

---

## 📄 مجوز

مجوز MIT — جزئیات در [LICENSE](LICENSE)

---

<div align="center">

**ساخته شده با ❤️ توسط [@ashkan_surii](https://t.me/ashkan_surii)**

</div>
