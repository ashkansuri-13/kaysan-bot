<div align="center">

# 🧠 Kaysan AI Bot

**Telegram AI Bot — 80+ Features**

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](docker-compose.yml)

[فارسی](README_FA.md) | **English** | [کوردی](README_KU.md)

</div>

---

## 📋 Introduction

Kaysan AI is a feature-rich Telegram bot powered by multiple AI models (GPT, DeepSeek, Llama, Qwen, Gemma) via OpenRouter. It supports **3 languages** (Kurdish Sorani, Persian, English) and includes **80+ features** spanning AI chat, media processing, group management, utility tools, and entertainment.

## ✨ Key Features

### 🤖 AI Chat & Intelligence
- **Multi-model chat** — GPT, DeepSeek, Llama, Qwen, Gemma via OpenRouter
- **Intent detection** — automatically selects the best model for each request
- **3-language support** — Kurdish Sorani, Persian, English with auto-detection
- **Multiple modes** — Teacher, Programmer, Friend
- **Conversation memory** — remembers context across messages
- **Long context support** — analyze large documents and files
- **Streaming responses** — real-time AI output

### 🎨 Media & Images
- **Voice-to-text** — high accuracy transcription (Groq Whisper)
- **Image analysis** — AI vision models describe and analyze images
- **AI image generation** — create images from text prompts
- **Text-to-image** — convert text to beautiful visuals
- **Meme generator** — create custom memes with AI
- **File analysis** — supports PDF, DOCX, TXT, and text files

### 🔧 20+ Utility Tools

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

### 👥 Group Management
- **Auto welcome & goodbye** — customizable messages for new/leaving members
- **Spam filter** — auto-delete spam and promotional links
- **Bad words filter** — auto-delete inappropriate messages
- **Anti-flood** — prevent message flooding
- **Slow Mode** — set delay between messages
- **Quiet hours** — disable bot during specific hours
- **Admin panel from DM** — manage groups without Telegram admin privileges
- **Auto-reply to mentions** — smart answers to questions
- **Auto-translate** — translate foreign messages automatically
- **Auto-pin** — pin important messages
- **Group quiz** — trivia competitions
- **Smart polls** — AI-powered polls
- **Group stats** — member count and activity tracking
- **Group rules** — set and display rules
- **Message report** — send reports to admins
- **Tag all** — message all members

### 🎮 Entertainment
- **Quiz** — trivia with multiple choice options
- **Riddles** — engaging brain teasers
- **Jokes** — funny and clean humor
- **Hafez Fal** — Persian poetry fortune telling
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
- **Network Monitor** — auto-restart on failures

## 🚀 Installation

### Option 1: Docker (Recommended)

```bash
git clone https://github.com/ashkansuri-13/kaysan-bot.git
cd kaysan-bot
cp .env.example .env
# Edit .env with your credentials
docker-compose up -d
```

### Option 2: One-Line Install

```bash
bash <(curl -s https://raw.githubusercontent.com/ashkansuri-13/kaysan-bot/master/install.sh)
```

### Option 3: Manual Setup

```bash
git clone https://github.com/ashkansuri-13/kaysan-bot.git
cd kaysan-bot
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
python run.py
```

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

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=bot --cov-report=html

# Run specific test file
pytest tests/test_chat.py -v
```

## 📁 Project Structure

```
kaysan-bot/
├── run.py                  # Entry point
├── bot/
│   ├── config.py           # Configuration
│   ├── database.py         # SQLite database (16 tables)
│   ├── router.py           # Language & intent detection
│   ├── openrouter.py       # OpenRouter API client
│   ├── keyboards.py        # Telegram keyboards
│   ├── texts.py            # Trilingual texts (ku/fa/en)
│   ├── middleware.py        # Rate limiting
│   ├── health.py           # Health check (port 8080)
│   ├── metrics.py          # Prometheus metrics (port 9090)
│   ├── circuit_breaker.py  # Circuit breaker pattern
│   ├── backup.py           # Database backup
│   ├── handlers/           # Command handlers
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
├── tests/                  # 50+ test files
├── web/                    # Web interface (Glassmorphism)
│   ├── index.html          # SPA frontend
│   ├── style.css           # Pink-Purple Neon theme
│   ├── app.js              # GSAP animations
│   └── server.py           # aiohttp backend
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## 🔧 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BOT_TOKEN` | ✅ | - | Telegram bot token |
| `OPENROUTER_KEY` | ✅ | - | OpenRouter API key |
| `OWNER_ID` | ✅ | - | Owner Telegram ID |
| `DEFAULT_LANG` | ❌ | `ku` | Default language (ku/fa/en) |
| `FREE_MESSAGE_LIMIT` | ❌ | `100` | Free message limit |
| `DAILY_COST_LIMIT` | ❌ | `5.0` | Daily cost limit ($) |
| `CHANNEL_USERNAME` | ❌ | - | Required channel username |
| `GROQ_API_KEY` | ❌ | - | Groq API key (voice transcription) |
| `REDIS_URL` | ❌ | - | Redis URL (caching) |
| `SENTRY_DSN` | ❌ | - | Sentry DSN (error tracking) |

## 🤖 AI Models

| Model | Provider | Use Case |
|-------|----------|----------|
| `mimo/mimo-auto` | Xiaomi MiMo | Primary (default) |
| `deepseek/deepseek-chat` | DeepSeek | Fallback |
| `openai/gpt-4o-mini` | OpenAI | Fallback |
| `anthropic/claude-haiku-4.5` | Anthropic | Fallback |

**Per-intent settings:**
- Chat: temperature=0.8, max_tokens=3000
- Code: temperature=0.2, max_tokens=8000
- Reasoning: temperature=0.3, max_tokens=4000
- Creative: temperature=0.9, max_tokens=8000

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Made with ❤️ by [@ashkan_surii](https://t.me/ashkan_surii)**

</div>
