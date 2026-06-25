# 🔒 Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability within Kaysan AI, please send an email to **@ashkan_surii** on Telegram. All security vulnerabilities will be promptly addressed.

### What to include:
1. Description of the vulnerability
2. Steps to reproduce
3. Potential impact
4. Suggested fix (if any)

### Response Timeline:
- **Acknowledgment**: Within 24 hours
- **Initial assessment**: Within 48 hours
- **Fix implementation**: Within 7 days
- **Public disclosure**: After fix is deployed

## Security Measures

### Authentication
- Telegram WebApp initData validated using HMAC-SHA256
- Session tokens are signed and have 7-day expiry
- Bot token never exposed to frontend

### API Security
- Rate limiting: 30 requests per minute per IP
- CORS restricted to allowed origins
- Security headers (HSTS, CSP, X-Frame-Options)
- Input validation on all endpoints

### Data Protection
- SQLite database with WAL mode
- No secrets in code (all in .env)
- Automated backups
- Error logging without sensitive data

### Infrastructure
- Systemd services with restart policies
- Non-root execution where possible
- Regular dependency updates

## Best Practices for Contributors

1. Never commit `.env` files or secrets
2. Use environment variables for configuration
3. Validate all user input
4. Follow OWASP guidelines
5. Run security scans before merging

## Contact

For security concerns, contact **@ashkan_surii** on Telegram.
