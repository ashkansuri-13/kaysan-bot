# Kaysan Bot Deployment Guide

## Prerequisites
- Python 3.12+
- ffmpeg (for voice processing)
- SQLite3

## Local Development

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

## Docker Deployment

```bash
# Build image
docker build -t kaysan-bot .

# Run container
docker run -d \
  --name kaysan-bot \
  -p 8080:8080 \
  -p 9090:9090 \
  -v /path/to/.env:/app/.env \
  kaysan-bot

# Check health
curl http://localhost:8080/health
```

## Docker Compose

```yaml
version: '3.8'
services:
  kaysan-bot:
    build: .
    ports:
      - "8080:8080"
      - "9090:9090"
    volumes:
      - ./.env:/app/.env
      - ./kaysan.db:/app/kaysan-bot/kaysan.db
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## systemd Deployment

```bash
# Copy service file
sudo cp kaysan-bot.service /etc/systemd/system/

# Enable and start
sudo systemctl enable kaysan-bot
sudo systemctl start kaysan-bot

# Check status
sudo systemctl status kaysan-bot
```

## Kubernetes Deployment

```bash
# Create secrets
kubectl create secret generic kaysan-secrets \
  --from-literal=bot-token=YOUR_TOKEN \
  --from-literal=openrouter-key=YOUR_KEY

# Apply configs
kubectl apply -f k8s/

# Check status
kubectl get pods
kubectl logs -f deployment/kaysan-bot
```

## Monitoring

### Health Check
```bash
curl http://localhost:8080/health
```

### Metrics
```bash
curl http://localhost:9090/metrics
```

### Logs
```bash
# systemd
journalctl -u kaysan-bot -f

# Docker
docker logs -f kaysan-bot

# Kubernetes
kubectl logs -f deployment/kaysan-bot
```

## Backup

### Automatic
- Database backup every 6 hours
- Config backup included
- Max 10 backups retained

### Manual
```bash
# Backup database
cp /root/kaysan-bot/kaysan-bot/kaysan.db /backup/kaysan_$(date +%Y%m%d).db

# Backup config
cp /root/kaysan-bot/.env /backup/env_$(date +%Y%m%d)
```

## Troubleshooting

### Bot not responding
```bash
# Check service status
systemctl status kaysan-bot

# Check logs
journalctl -u kaysan-bot -n 50

# Restart
systemctl restart kaysan-bot
```

### High memory usage
```bash
# Check memory
free -h

# Restart to clear memory
systemctl restart kaysan-bot
```

### Database locked
```bash
# Check WAL mode
sqlite3 /root/kaysan-bot/kaysan-bot/kaysan.db "PRAGMA journal_mode;"

# Force checkpoint
sqlite3 /root/kaysan-bot/kaysan-bot/kaysan.db "PRAGMA wal_checkpoint(TRUNCATE);"
```
