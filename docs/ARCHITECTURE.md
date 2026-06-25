# Kaysan Bot Architecture

## Overview
Kaysan Bot is a multi-language Telegram AI bot built with Python 3.12 and aiogram 3.x.

## Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│                  Telegram API                    │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│               aiogram Dispatcher                 │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────┐ │
│  │  Middleware  │  │  Middleware  │  │ Middleware│ │
│  │  (Rate)     │  │  (Validate) │  │ (Sanitize)│ │
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

## Key Components

### 1. Middleware Layer
- **RateLimitMiddleware**: 30 req/min per user
- **InputValidationMiddleware**: SQL injection, XSS protection
- **SanitizeMiddleware**: Unicode surrogate handling

### 2. Router Layer
- **Intent Detection**: Chat, Image, Code, Reason, Creative
- **Language Detection**: Kurdish, Persian, English
- **Model Selection**: Based on intent and language

### 3. Core Engine
- **Context Builder**: Last 10 messages + summarization
- **Prompt Enhancer**: Optimizes user queries
- **Quality Checker**: Validates responses

### 4. OpenRouter Client
- **Streaming**: Real-time response delivery
- **Multi-model**: Fallback chain
- **Rate Limiting**: Per-model limits
- **Caching**: SQLite + Redis fallback

### 5. Database
- **Users**: Profile, language, preferences
- **Conversations**: Message history
- **Cache**: Response cache
- **Usage**: Cost tracking

## Data Flow

1. User sends message
2. Middleware validates & sanitizes
3. Router detects intent & language
4. Core builds context & enhances prompt
5. OpenRouter calls AI model
6. Response validated & formatted
7. Sent to user with back button

## Security Layers

1. **Input Validation**: SQL injection, XSS
2. **Rate Limiting**: Per-user, per-model
3. **Unicode Sanitization**: Surrogate handling
4. **Security Headers**: HSTS, CSP, X-Frame
5. **Authentication**: Token-based

## Performance Optimizations

1. **Connection Pooling**: SQLite WAL mode
2. **Response Caching**: MD5 hash keys
3. **Streaming**: Real-time delivery
4. **Async I/O**: Non-blocking operations
5. **TTL Dict**: Memory management

## Monitoring

1. **Health Check**: `/health` endpoint
2. **Metrics**: Prometheus format
3. **Logging**: Structured JSON
4. **Error Tracking**: Sentry integration
5. **Cost Monitoring**: Daily limits
