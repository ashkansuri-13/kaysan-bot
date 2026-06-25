# Kaysan AI Bot API Documentation

## Overview

Kaysan AI is a Telegram bot with 80+ features including AI chat, image generation, voice transcription, group management, and more.

## Endpoints

### Health Check

```
GET /health
```

Returns bot health status.

**Response:**
```json
{
  "status": "healthy",
  "uptime_seconds": 123.4,
  "service": "kaysan-ai-bot"
}
```

### Readiness Probe

```
GET /ready
```

Returns readiness status.

**Response (200):**
```json
{
  "ready": true
}
```

**Response (503):**
```json
{
  "ready": false
}
```

### Metrics (Prometheus)

```
GET /metrics
```

Returns Prometheus metrics.

**Response:**
```
# HELP kaysan_uptime_seconds Bot uptime in seconds
# TYPE kaysan_uptime_seconds gauge
kaysan_uptime_seconds 123.4

# HELP kaysan_messages_total Total messages processed
# TYPE kaysan_messages_total counter
kaysan_messages_total 1000

# HELP kaysan_callbacks_total Total callbacks processed
# TYPE kaysan_callbacks_total counter
kaysan_callbacks_total 500

# HELP kaysan_errors_total Total errors
# TYPE kaysan_errors_total counter
kaysan_errors_total 10

# HELP kaysan_api_calls_total Total API calls
# TYPE kaysan_api_calls_total counter
kaysan_api_calls_total 200

# HELP kaysan_api_latency_seconds Average API latency
# TYPE kaysan_api_latency_seconds gauge
kaysan_api_latency_seconds 0.500

# HELP kaysan_active_users Number of unique active users
# TYPE kaysan_active_users gauge
kaysan_active_users 50
```

## Telegram Commands

### General Commands

| Command | Description |
|---------|-------------|
| `/start` | Start the bot |
| `/help` | Show help |
| `/lang` | Change language |
| `/clear` | Clear conversation history |

### AI Commands

| Command | Description |
|---------|-------------|
| `/image <prompt>` | Generate image |
| `/translate <text>` | Translate to 3 languages |
| `/summarize <text>` | Summarize text |
| `/quiz` | Start a quiz |
| `/joke` | Tell a joke |
| `/riddle` | Give a riddle |

### Tool Commands

| Command | Description |
|---------|-------------|
| `/qr <text>` | Generate QR code |
| `/short <url>` | Shorten URL |
| `/password [length]` | Generate password |
| `/calc <expression>` | Calculator |
| `/exchange <amount> <from> <to>` | Currency exchange |
| `/stock <symbol>` | Stock price |
| `/meme <top> \| <bottom>` | Create meme |
| `/invoice` | Create invoice |
| `/flashcard add <q> \| <a>` | Add flashcard |
| `/habit add <name>` | Add habit |
| `/expense <amount> <desc>` | Log expense |
| `/travel <destination>` | Plan trip |
| `/recipe <ingredients>` | Get recipe |
| `/news [topic]` | Get news |
| `/challenge` | Daily challenge |
| `/guess` | Number guessing game |

### Group Commands

| Command | Description |
|---------|-------------|
| `/manage` | Manage groups |
| `/groupstats` | Group statistics |
| `/aipoll <topic>` | AI poll |
| `/groupquiz` | Group quiz |
| `/gtranslate <text>` | Group translate |
| `/grouphelp` | Group help |
| `/slowmode [seconds]` | Set slow mode |
| `/silent [start] [end]` | Set quiet hours |
| `/setrules <rules>` | Set group rules |
| `/rules` | Show rules |
| `/tagall [message]` | Tag all members |
| `/report` | Report message |

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BOT_TOKEN` | Yes | - | Telegram bot token |
| `OPENROUTER_KEY` | Yes | - | OpenRouter API key |
| `OWNER_ID` | Yes | - | Owner Telegram ID |
| `DEFAULT_LANG` | No | `ku` | Default language |
| `FREE_MESSAGE_LIMIT` | No | `100` | Free message limit |
| `DAILY_COST_LIMIT` | No | `5.0` | Daily cost limit |
| `CHANNEL_USERNAME` | No | - | Required channel |
| `GROQ_API_KEY` | No | - | Groq API key |
| `REDIS_URL` | No | - | Redis URL |
| `SENTRY_DSN` | No | - | Sentry DSN |
| `DB_BACKEND` | No | `sqlite` | Database backend |
| `DATABASE_URL` | No | - | PostgreSQL URL |

## Architecture

```
kaysan-bot/
├── run.py              # Entry point
├── bot/
│   ├── config.py       # Configuration
│   ├── database.py     # Database (SQLite/PostgreSQL)
│   ├── pool.py         # Connection pooling
│   ├── middleware.py    # Rate limiting, input validation
│   ├── health.py       # Health check
│   ├── metrics.py      # Prometheus metrics
│   ├── sentry_config.py # Error tracking
│   ├── backup.py       # Backup automation
│   ├── circuit_breaker.py # Circuit breaker
│   ├── migration.py    # Database migration
│   ├── logging_config.py # Structured logging
│   ├── handlers/       # Command handlers
│   └── services/       # External services
├── tests/              # Test suite
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```
