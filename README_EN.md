<div align="center">

# 🧠 Kaysan AI Bot

**Telegram AI Bot — 60+ Features**

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](docker-compose.yml)
[![Tests](https://img.shields.io/badge/Tests-829+-brightgreen?style=for-the-badge)](tests/)
[![Aiogram](https://img.shields.io/badge/Aiogram-3-0077B5?style=for-the-badge&logo=python&logoColor=white)](https://docs.aiogram.dev/)

[فارسی](README_FA.md) | **English** | [کوردی](README_KU.md)

</div>

---

## 📸 Screenshots

> Screenshots coming soon! Join our channel to see the bot in action: [@ashkan_surii](https://t.me/ashkan_surii)

| Chat | Group Management | Mini App |
|------|-----------------|----------|
| *AI-powered conversations* | *Auto moderation & tools* | *Glassmorphism UI* |

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Language** | Python 3.12 |
| **Bot Framework** | Aiogram 3 |
| **Database** | SQLite (WAL mode) |
| **Cache** | Redis |
| **AI Provider** | OpenRouter |
| **Voice** | Groq Whisper |
| **Container** | Docker |
| **Monitoring** | Prometheus |
| **Web Server** | aiohttp |

---

## 🏛️ Architecture

```
┌─────────────┐
│  Telegram    │
│  Users       │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Aiogram 3  │  ← Message Router
│  Dispatcher │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Handlers   │  ← 20+ Command Handlers
│  & Filters  │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐
│  AI Engine  │────▶│  OpenRouter │
│  (Intent)   │     │  Multi-Model│
└──────┬──────┘     └─────────────┘
       │
       ▼
┌─────────────┐
│  SQLite DB  │  ← User Data & History
└─────────────┘
```

---

## ✨ Features

### 🤖 AI Chat & Intelligence
- **Multi-model chat** — GPT, DeepSeek, Llama, Qwen, Gemma via OpenRouter
- **Intent detection** — automatically selects the best model for each request
- **3-language support** — Kurdish Sorani, Persian, English with auto-detection
- **Multiple modes** — Teacher, Programmer, Friend
- **Conversation memory** — remembers context across messages
- **Streaming responses** — real-time AI output

### 🎨 Media & Images
- **Voice-to-text** — high accuracy transcription (Groq Whisper)
- **Image analysis** — AI vision models describe and analyze images
- **AI image generation** — create images from text prompts
- **Text-to-image** — convert text to beautiful visuals
- **Meme generator** — create custom memes with AI
- **File analysis** — supports PDF, DOCX, TXT

### 🔧 20+ Utility Tools

| Command | Description |
|---------|-------------|
| `/qr` | Generate QR Code |
| `/short` | Shorten URL |
| `/screenshot` | Website screenshot |
| `/password` | Generate secure password |
| `/calc` | Safe calculator |
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

### 👥 Group Management
- **Auto welcome & goodbye** — customizable messages
- **Spam filter** — auto-delete spam and promotional links
- **Bad words filter** — auto-delete inappropriate messages
- **Anti-flood** — prevent message flooding
- **Slow Mode** — set delay between messages
- **Quiet hours** — disable bot during specific hours
- **Admin panel from DM** — manage groups without Telegram admin
- **Auto-reply to mentions** — smart answers to questions
- **Auto-translate** — translate foreign messages automatically
- **Group quiz** — trivia competitions
- **Smart polls** — AI-powered polls
- **Group stats** — member count and activity tracking
- **Tag all** — message all members

### 👑 Admin Dashboard
- **User Management** — View, ban, unban users
- **Broadcast Messages** — Send messages to all users
- **Usage Analytics** — Track messages, costs, popular commands
- **Subscription Management** — Grant/revoke premium access
- **AI Model Control** — Test and monitor AI models
- **System Monitoring** — Health checks, uptime, metrics
- **Backup Control** — Database backup management

### 🎮 Entertainment
- **Quiz** — trivia with multiple choice options
- **Riddles** — engaging brain teasers
- **Jokes** — funny and clean humor
- **Hafez Fal** — Persian poetry fortune
- **Number guessing game** — fun interactive game
- **Daily challenge** — varied daily challenges

### 🛡️ Security & Reliability
- **Rate Limiting** — automatic abuse prevention (30 req/min)
- **Spam & bad words filtering**
- **Safe Math Calculator** — secure math without eval
- **Circuit Breaker** — prevent cascading failures
- **Automatic database backup**
- **Health Check & Readiness Probe** — port 8080
- **Prometheus Metrics** — port 9090

---

## 👑 Admin Dashboard

Full-featured admin panel accessible via Telegram DM:

| Feature | Description |
|---------|-------------|
| User Management | View, ban, unban users |
| Broadcast Messages | Send messages to all users |
| Usage Analytics | Track messages, costs, popular commands |
| Revenue Statistics | Monitor bot expenses |
| Subscription Management | Grant/revoke premium access |
| AI Model Control | Test and monitor AI models |
| System Monitoring | Health checks, uptime, metrics |
| Error Logs | Track and debug issues |
| Backup Control | Database backup management |

---

## 🔌 Integrations

| Service | Purpose |
|---------|---------|
| **OpenRouter** | Multi-model AI (GPT, DeepSeek, Llama, Qwen, Gemma) |
| **Groq Whisper** | High-accuracy voice transcription |
| **Telegram Bot API** | Bot communication and Mini App |
| **Redis** | Caching and session storage |
| **Prometheus** | Metrics and monitoring |
| **Sentry** | Error tracking (optional) |

---

## 🚀 Installation

### One-Line Install

```bash
bash <(curl -s https://raw.githubusercontent.com/ashkansuri-13/kaysan-bot/master/install.sh)
```

### Docker (Recommended)

```bash
git clone https://github.com/ashkansuri-13/kaysan-bot.git
cd kaysan-bot
cp .env.example .env
docker-compose up -d
```

### Manual Setup

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

## ⚙️ Configuration

Create a `.env` file with your credentials:

```env
BOT_TOKEN=your_bot_token
OPENROUTER_KEY=your_openrouter_key
OWNER_ID=your_telegram_id
DEFAULT_LANG=en
FREE_MESSAGE_LIMIT=100
DAILY_COST_LIMIT=5.0
CHANNEL_USERNAME=your_channel
GROQ_API_KEY=your_groq_key
REDIS_URL=redis://localhost:6379/0
SENTRY_DSN=your_sentry_dsn
```

---

## 🧪 Testing

```bash
# Run all 829 tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=bot --cov-report=html
```

---

## 📁 Project Structure

```
kaysan-bot/
├── run.py                  # Entry point
├── bot/
│   ├── config.py           # Configuration
│   ├── database.py         # SQLite (16 tables)
│   ├── router.py           # Language & intent detection
│   ├── openrouter.py       # OpenRouter API client
│   ├── keyboards.py        # Telegram keyboards
│   ├── texts.py            # Trilingual texts (ku/fa/en)
│   ├── middleware.py        # Rate limiting
│   ├── health.py           # Health check (port 8080)
│   ├── metrics.py          # Prometheus metrics (port 9090)
│   ├── circuit_breaker.py  # Circuit breaker
│   ├── backup.py           # Database backup
│   ├── handlers/           # 20+ command handlers
│   │   ├── core.py         # Core AI processing
│   │   ├── chat.py         # Text chat
│   │   ├── media.py        # Voice & images
│   │   ├── search.py       # Web search
│   │   ├── groups.py       # Group management
│   │   ├── panel.py        # Admin panel
│   │   ├── tools.py        # 20+ utility tools
│   │   ├── quiz.py         # Quiz & trivia
│   │   ├── translate.py    # Translation
│   │   ├── notes.py        # Notes & reminders
│   │   ├── remind.py       # Reminders
│   │   ├── extras.py       # Extra features
│   │   └── webapp.py       # Telegram Mini App
│   └── services/
│       ├── voice.py        # Voice transcription (Groq)
│       ├── image.py        # Image generation
│       └── tts.py          # Text to speech
├── tests/                  # 55 test files, 829 tests
├── web/                    # Web interface (Glassmorphism)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## 🔧 Environment Variables

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

## 🤖 AI Models

| Model | Provider | Use Case |
|-------|----------|----------|
| `mimo/mimo-auto` | Xiaomi MiMo | Primary (default) |
| `deepseek/deepseek-chat` | DeepSeek | Fallback |
| `openai/gpt-4o-mini` | OpenAI | Fallback |
| `anthropic/claude-haiku-4.5` | Anthropic | Fallback |

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Made with ❤️ by [@ashkan_surii](https://t.me/ashkan_surii)**

</div>
