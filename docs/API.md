# Kaysan Bot API Documentation

## Base URL
- Health: `http://localhost:8080`
- Metrics: `http://localhost:9090`

## Endpoints

### Health Check
```
GET /health
```
**Response:**
```json
{
  "status": "healthy",
  "uptime_seconds": 1090.7,
  "service": "kaysan-ai-bot",
  "version": "1.0.0"
}
```

### Readiness Probe
```
GET /ready
```
**Response:**
```json
{
  "ready": true
}
```

### Prometheus Metrics
```
GET /metrics
```
**Response:** Prometheus text format with:
- `kaysan_uptime_seconds` - Bot uptime
- `kaysan_messages_total` - Total messages
- `kaysan_callbacks_total` - Total callbacks
- `kaysan_errors_total` - Total errors
- `kaysan_api_calls_total` - Total API calls
- `kaysan_api_latency_seconds` - Average API latency
- `kaysan_active_users` - Active users

## Telegram Bot Commands

### Core
- `/start` - Start bot
- `/help` - Show help
- `/lang` - Change language
- `/clear` - Clear history

### AI Features
- `/image` - Generate image
- `/translate` - Translate text
- `/summarize` - Summarize text
- `/mega` - Mega prompt
- `/prompt` - Write prompt
- `/apiprompt` - Send to model

### Tools
- `/qr` - Generate QR code
- `/short` - Shorten URL
- `/calc` - Calculator
- `/exchange` - Currency exchange
- `/password` - Generate password
- `/stock` - Stock price
- `/weather` - Weather forecast
- `/news` - News summary

### Fun
- `/quiz` - Trivia quiz
- `/joke` - Tell a joke
- `/fal` - Fortune telling
- `/challenge` - Daily challenge
- `/guess` - Number guessing game

### Notes & Reminders
- `/note` - Save note
- `/notes` - List notes
- `/remind` - Set reminder

### Group Management
- `/grouphelp` - Group commands
- `/groupstats` - Group statistics
- `/aipoll` - AI poll
- `/groupquiz` - Group quiz

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad request |
| 429 | Rate limit exceeded |
| 500 | Internal server error |

## Rate Limits
- 30 requests per minute per user
- 10 requests per minute per model
- 50 messages per hour per user
