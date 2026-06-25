# 🧠 Kaysan AI Bot v2.05

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![aiogram](https://img.shields.io/badge/aiogram-3.29-green.svg)](https://docs.aiogram.dev)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](Dockerfile)
[![Kubernetes](https://img.shields.io/badge/K8s-Ready-blue.svg)](k8s/)

> **Multi-language AI Telegram Bot** — Kurdish Sorani, Persian, English  
> Powered by OpenRouter multi-model AI with 50+ features

---

## ✨ Features

### 🤖 AI-Powered Chat
- **Multi-model AI**: DeepSeek, GPT-4o-mini, Claude, Gemini
- **Streaming responses**: Real-time answer delivery
- **Smart prompt enhancement**: Optimizes your queries
- **Context awareness**: Remembers conversation history
- **3 languages**: Kurdish Sorani, Persian, English

### 🎨 Image Generation
- **17+ free APIs**: Pollinations, Together, HuggingFace, Prodia
- **12 art styles**: Realistic, Anime, Cartoon, Watercolor, Oil Painting, Pixel Art, 3D, Comic, Minimalist, Cyberpunk, Fantasy, Sketch
- **Prompt enhancement**: Auto-improves image descriptions

### 🔍 Smart Search
- **Web search**: DuckDuckGo integration
- **News search**: Real-time news aggregation
- **Image search**: Visual content discovery
- **Video search**: Video content discovery
- **Telegram search**: Channel content search
- **Smart caching**: SQLite + Redis fallback

### 🔧 20+ Utility Tools
- **QR Code Generator**
- **URL Shortener**
- **Calculator** (safe AST-based)
- **Currency Exchange**
- **Password Generator**
- **Stock Prices**
- **Weather Forecast**
- **Screenshot Tool**
- **Text to Image**
- **Meme Generator**
- **Invoice Generator**
- **Flash Cards**
- **Habit Tracker**
- **Expense Tracker**
- **Travel Planner**
- **Recipe Finder**
- **News Summary**
- **Daily Challenge**
- **Advanced Polls**
- **Number Guessing Game**

### 👥 Group Management
- **Welcome/Goodbye messages**
- **Spam filtering**
- **Bad word filtering**
- **Flood protection**
- **Slow mode**
- **Auto-reply keywords**
- **Bot mention responses**
- **Photo analysis**
- **File analysis**
- **Voice transcription**

### 🎮 Fun & Entertainment
- **Trivia Quiz**
- **Jokes**
- **Fortune Telling (Hafez)**
- **Daily Challenges**
- **Number Guessing Game**
- **Story Games**

### 📝 Productivity
- **Notes** (save/list/delete)
- **Reminders**
- **Translate** (3 languages)
- **Summarize**
- **Mega Prompt**
- **AI Poll**
- **Group Quiz**

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- ffmpeg (for voice processing)
- SQLite3

### Installation

```bash
# Clone repository
git clone https://github.com/ashkansuri-13/kaysan-bot.git
cd kaysan-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your tokens

# Run bot
python kaysan-bot/run.py
```

### Docker

```bash
# Build image
docker build -t kaysan-bot .

# Run container
docker run -d \
  --name kaysan-bot \
  -p 8080:8080 \
  -p 9090:9090 \
  -v ./.env:/app/.env \
  kaysan-bot
```

### Kubernetes

```bash
# Create secrets
kubectl create secret generic kaysan-secrets \
  --from-literal=bot-token=YOUR_TOKEN \
  --from-literal=openrouter-key=YOUR_KEY

# Deploy
kubectl apply -f k8s/
```

---

## 📊 Architecture

```
┌─────────────────────────────────────────────────┐
│                  Telegram API                    │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│               aiogram Dispatcher                 │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────┐ │
│  │  Rate Limit │  │   Validate  │  │ Sanitize │ │
│  └─────────────┘  └─────────────┘  └──────────┘ │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│              Router (Intent Detection)           │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐  │
│  │ Chat │ │Image │ │Search│ │Tools │ │ Fun  │  │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘  │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│            Core Processing Engine                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │ Context  │ │  Prompt  │ │ Quality  │        │
│  │ Builder  │ │Enhancer  │ │ Checker  │        │
│  └──────────┘ └──────────┘ └──────────┘        │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│              OpenRouter Client                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │ Streaming│ │  Retry   │ │  Cache   │        │
│  └──────────┘ └──────────┘ └──────────┘        │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│              SQLite Database                     │
│  ┌──────┐ ┌──────────┐ ┌──────────┐            │
│  │Users │ │Conversa- │ │  Cache   │            │
│  │      │ │  tions   │ │          │            │
│  └──────┘ └──────────┘ └──────────┘            │
└─────────────────────────────────────────────────┘
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `BOT_TOKEN` | Telegram Bot Token | Yes |
| `OPENROUTER_KEY` | OpenRouter API Key | Yes |
| `OWNER_ID` | Your Telegram User ID | Yes |
| `CHANNEL_USERNAME` | Channel username for membership check | No |
| `GROQ_API_KEY` | Groq API Key for voice transcription | No |
| `REDIS_URL` | Redis URL for caching | No |

### Models Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `PRIMARY_MODEL` | Primary AI model | deepseek/deepseek-chat |
| `CHAT_MODELS` | Chat models list | deepseek/deepseek-chat |
| `CODE_MODELS` | Code models list | deepseek/deepseek-chat |
| `VISION_MODELS` | Vision models list | openai/gpt-4o-mini |
| `IMAGE_MODEL` | Image generation model | - |

---

## 📈 Monitoring

### Health Check
```bash
curl http://localhost:8080/health
```

### Prometheus Metrics
```bash
curl http://localhost:9090/metrics
```

### Logs
```bash
# systemd
journalctl -u kaysan-bot -f

# Docker
docker logs -f kaysan-bot
```

---

## 🧪 Testing

```bash
# Run tests
cd kaysan-bot
python -m pytest test_all.py -v

# Run with coverage
python -m pytest test_all.py --cov=bot --cov-report=html
```

---

## 📚 Documentation

- [API Documentation](docs/API.md)
- [Architecture Guide](docs/ARCHITECTURE.md)
- [Deployment Guide](docs/DEPLOYMENT.md)

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [aiogram](https://docs.aiogram.dev/) - Async Telegram bot framework
- [OpenRouter](https://openrouter.ai/) - Multi-model AI API
- [Pollinations](https://pollinations.ai/) - Free image generation
- [DuckDuckGo](https://duckduckgo.com/) - Privacy-focused search

---

**Made with ❤️ by @ashkan_surii**
