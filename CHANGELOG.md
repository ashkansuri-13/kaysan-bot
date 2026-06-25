# Changelog

## v2.05 (2026-06-25)

### 🎨 UI Redesign
- Complete main menu redesign: 28 buttons → 6 category buttons
- Sub-menus for Chat, Search, Tools, Fun, Settings, Image
- Back to main menu button on EVERY response
- Custom thinking messages per feature (chat, code, search, image, etc.)
- All buttons are colorful with consistent color scheme

### 🤖 Chat Improvements
- Fixed streaming response delivery
- Added context summarization for long conversations
- Added language enforcement in system prompts
- Added message splitting for long responses
- Added follow-up question suggestions
- Added feedback system (like/dislike)
- Added response regeneration
- Added text-to-image conversion
- Added text-to-speech for responses
- Added response alternatives display

### 🔧 Critical Bug Fixes
- Fixed UnicodeEncodeError (surrogate characters from Telegram users)
- Fixed frozen instance error in aiogram 3.x
- Fixed error handler signature mismatch
- Fixed missing  callback handler
- Fixed missing  callback handlers
- Removed overly aggressive middleware patterns
- Added monkey-patch for Unicode safety

### 🏗️ Infrastructure
- Added Docker with health check
- Added Kubernetes configs (deployment, service, secret)
- Added security headers (HSTS, CSP, X-Frame-Options)
- Added Prometheus metrics endpoint
- Added graceful shutdown with signal handling
- Added persistent rate limiting
- Added per-model rate limiting
- Added database connection pool
- Added log rotation config
- Added CI/CD pipeline (GitHub Actions)
- Added pre-commit hooks (ruff, trailing-whitespace)
- Added monitoring alerts (Prometheus rules)

### 📚 Documentation
- Full API documentation
- Architecture guide with diagrams
- Deployment guide (Docker, K8s, systemd)
- README in 3 languages (English, Persian, Kurdish)
- MkDocs configuration for auto-generated docs

### 🧪 Testing
- Expanded test suite: 13 tests (12 passing)
- Added test coverage configuration
- Added pytest-asyncio support
- Added tests for: auth, config, router, TTL dict, texts, prompt enhancer, upgrade chat, backup, health, image styles, middleware

### 🔒 Security
- Input validation middleware (SQL injection, XSS protection)
- Rate limiting (30 req/min per user)
- Per-model rate limiting (10 req/min)
- Unicode sanitization
- Security headers on all endpoints
- Safe AST-based calculator (no eval)

### 📊 Performance
- SQLite WAL mode
- Response caching (SQLite + Redis fallback)
- Connection pooling
- TTL-based memory management
- Smart context summarization

## v2.00 (2026-06-20)
- Initial release with 50+ features
- Multi-language support (Kurdish, Persian, English)
- Multi-model AI (DeepSeek, GPT-4o-mini, Claude)
- Image generation (17+ APIs)
- Voice transcription (Groq Whisper)
- Web search (DuckDuckGo)
- Group management
- Utility tools
- Fun & entertainment
