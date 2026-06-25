<div align="center">

# 🧠 Kaysan AI Bot

**Telegram AI Bot — 80+ Features | Bot-MiniApp Integration**

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](docker-compose.yml)
[![Tests](https://img.shields.io/badge/Tests-829+-brightgreen?style=for-the-badge)](tests/)
[![Aiogram](https://img.shields.io/badge/Aiogram-3-0077B5?style=for-the-badge&logo=python&logoColor=white)](https://docs.aiogram.dev/)
[![CI/CD](https://img.shields.io/github/actions/workflow/status/ashkansuri-13/kaysan-bot/ci.yml?style=for-the-badge&label=CI/CD)](https://github.com/ashkansuri-13/kaysan-bot/actions)
[![Version](https://img.shields.io/badge/version-2.0.0-blue?style=for-the-badge)](https://github.com/ashkansuri-13/kaysan-bot/releases)
[![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen?style=for-the-badge)](tests/)
[![Security](https://img.shields.io/badge/security-bandit-yellow?style=for-the-badge)](SECURITY.md)
[![Stars](https://img.shields.io/github/stars/ashkansuri-13/kaysan-bot?style=for-the-badge)](https://github.com/ashkansuri-13/kaysan-bot/stargazers)

---

### Choose Your Language

[![Persian](https://img.shields.io/badge/🇮🇷-فارسی-009546?style=for-the-badge)](README_FA.md)
[![English](https://img.shields.io/badge/🇬🇧-English-012169?style=for-the-badge)](README_EN.md)
[![Kurdish](https://img.shields.io/badge/Kurdish-ED2024?style=for-the-badge)](README_KU.md)

<br>

<img src="assets/logo.png" width="120" />

<br>

**Kaysan AI** is a powerful Telegram bot powered by multiple AI models (GPT, DeepSeek, Llama, Qwen, Gemma, MiMo) via OpenRouter. It supports **3 languages** (Kurdish Sorani, Persian, English) with **80+ features** including AI chat, voice transcription, image generation, group management, and 20+ utility tools.

**v2.0** introduces **Bot-MiniApp Integration** — shared authentication, conversations, and settings between Telegram bot and web mini app.

<br>

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🤖 **AI Chat** | Multi-model ensemble (MiMo, DeepSeek, GPT, Llama) |
| 🎨 **Image Generation** | 10+ free APIs (Pollinations, HuggingFace, Prodia) |
| 🎤 **Voice Transcription** | Groq Whisper for voice messages |
| 👥 **Group Management** | Anti-spam, auto-reply, moderation (20+ tools) |
| 🔧 **Utility Tools** | QR code, calculator, weather, news, translate |
| 🧠 **Smart Features** | Quiz, jokes, fortune, flashcards, habits |
| 📱 **Mini App** | Glassmorphism UI with personality system |
| 🔐 **Auth Integration** | Shared auth between bot and mini app |
| 🔄 **Real-time Sync** | Conversations synced across platforms |
| 🌐 **Multi-language** | Kurdish, Persian, English |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Telegram Bot                          │
│                    (Aiogram 3.x)                         │
└─────────────┬───────────────────────────┬───────────────┘
              │                           │
              ▼                           ▼
┌─────────────────────┐     ┌─────────────────────────────┐
│   Bot Handlers      │     │    Web Server (aiohttp)     │
│   - 80+ commands    │     │    - 16 API endpoints       │
│   - Group mgmt      │     │    - Auth middleware        │
│   - Voice/Image     │     │    - Streaming chat         │
└─────────┬───────────┘     └─────────────┬───────────────┘
          │                               │
          ▼                               ▼
┌─────────────────────────────────────────────────────────┐
│              Shared SQLite Database (WAL)                │
│  ┌──────────┐ ┌──────────────┐ ┌──────────────────────┐ │
│  │  users   │ │ conversations│ │    user_sessions     │ │
│  └──────────┘ └──────────────┘ └──────────────────────┘ │
│  ┌──────────────┐ ┌────────────┐ ┌────────────────────┐ │
│  │ user_settings│ │ sync_log   │ │    group_settings  │ │
│  └──────────────┘ └────────────┘ └────────────────────┘ │
└─────────────────────────────────────────────────────────┘
          │                               │
          ▼                               ▼
┌─────────────────────┐     ┌─────────────────────────────┐
│   AI Providers      │     │      External APIs          │
│   - OpenRouter      │     │   - Pollinations (free)     │
│   - MiMo v2.5       │     │   - Groq Whisper            │
│   - DeepSeek        │     │   - Web Search              │
│   - Free Models     │     │   - Weather/News            │
└─────────────────────┘     └─────────────────────────────┘
```

---

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
git clone https://github.com/ashkansuri-13/kaysan-bot.git
cd kaysan-bot
cp .env.example .env
# Edit .env with your tokens
docker-compose up -d
```

### Option 2: Manual Installation

```bash
git clone https://github.com/ashkansuri-13/kaysan-bot.git
cd kaysan-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your tokens
python kaysan-bot/run.py
```

### Option 3: One-Click Install

```bash
curl -sSL https://raw.githubusercontent.com/ashkansuri-13/kaysan-bot/master/install.sh | bash
```

---

## 📋 Prerequisites

- Python 3.12+
- Telegram Bot Token (from @BotFather)
- OpenRouter API Key
- Redis (optional, for caching)

---

## 🔧 Configuration

Copy `.env.example` to `.env` and configure:

```env
# Required
BOT_TOKEN=your_telegram_bot_token
OPENROUTER_KEY=your_openrouter_api_key

# Optional
DEFAULT_LANG=ku
FREE_MESSAGE_LIMIT=100
CHANNEL_USERNAME=your_channel
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=bot --cov-report=html

# Run specific test
pytest tests/test_core.py -v
```

---

## 📚 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/chat` | POST | Single-shot chat |
| `/api/chat/stream` | POST | Streaming chat (SSE) |
| `/api/auth/telegram` | POST | Telegram login |
| `/api/auth/session` | GET | Session validation |
| `/api/conversations` | GET/POST | Manage conversations |
| `/api/settings` | GET/PUT | User settings |
| `/api/sync/poll` | GET | Real-time sync |

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone the repo
git clone https://github.com/ashkansuri-13/kaysan-bot.git
cd kaysan-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov ruff

# Run tests
pytest tests/ -v

# Run linter
ruff check bot/
ruff format bot/
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Credits

Built with ❤️ by [@ashkan_surii](https://t.me/ashkan_surii)

### Technologies Used

- [Aiogram](https://docs.aiogram.dev/) - Telegram Bot Framework
- [OpenRouter](https://openrouter.ai/) - AI Model Gateway
- [Pollinations AI](https://pollinations.ai/) - Free Image/Text Generation
- [Groq](https://groq.com/) - Fast AI Inference
- [Edge TTS](https://github.com/rany2/edge-tts) - Text-to-Speech

---

## 📊 Stats

- **80+** Bot Commands
- **3** Languages Supported
- **10+** AI Models
- **20+** Utility Tools
- **829+** Tests
- **16** API Endpoints
- **20** Database Tables

---

<div align="center">

**If you find this project helpful, please give it a ⭐ star!**

[![Star History Chart](https://api.star-history.com/svg?repos=ashkansuri-13/kaysan-bot&type=Date)](https://star-history.com/#ashkansuri-13/kaysan-bot&Date)

</div>
