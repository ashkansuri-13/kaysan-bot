# 🧚‍♂️ What's Changed

## v2.0.0 (2026-06-25) — Bot-MiniApp Integration

### 🚀 New Features
- **Bot-MiniApp Integration**: Shared authentication, conversations, and settings between Telegram bot and mini app
- **Multi-Provider AI Ensemble**: Pollinations AI (free) + OpenRouter free models + Xiaomi MiMo v2.5
- **Production Authentication**: HMAC-SHA256 Telegram initData validation with session tokens
- **11 New API Endpoints**: Auth, conversations, settings, sync
- **Real-time Sync**: Polling-based synchronization every 10 seconds

### 🐛 Bug Fixes
- Fixed `mimo/mimo-auto` invalid model ID → replaced with `xiaomi/mimo-v2.5`
- Fixed session `expires_at` bug (was using creation time instead of expiry)
- Fixed Pollinations model list (removed deprecated models)
- Fixed asyncio import in web server handlers
- Fixed auth middleware not being applied

### 🗄️ Database
- 3 new tables: `user_sessions`, `user_settings`, `sync_log`
- Enhanced `users` table with profile fields
- Enhanced `conversations` table with platform tracking
- Non-destructive migration (v2)

### 🏗️ Infrastructure
- Web server as systemd service (`kaysan-web.service`)
- CORS configured for production domains
- Rate limiting on API endpoints
- Security headers (HSTS, CSP, etc.)

### 📦 New Files
- `bot/auth_utils.py` — Authentication utilities
- `bot/providers.py` — Multi-provider AI client
- `kaysan-web.service` — Systemd service file

---

## v1.0.0 (2026-06-23) — Initial Release

### 🚀 Features
- 60+ bot commands
- 3 languages (Kurdish Sorani, Persian, English)
- AI chat with multiple models
- Voice transcription (Groq Whisper)
- Image generation (10+ APIs)
- Group management (20+ features)
- Web mini app with personality system
- 20+ utility tools

### 🏗️ Infrastructure
- Docker support
- CI/CD pipeline (GitHub Actions)
- Automated testing (829+ tests)
- Health check & metrics servers
- Automated backups

---

**Full Changelog**: https://github.com/ashkansuri-13/kaysan-bot/commits/v2.0.0
