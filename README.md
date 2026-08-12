# AI Content Telegram Bot

## Chạy bot

Yêu cầu Python 3.11 trở lên. Python 3.11 (giống Dockerfile) là phiên bản được khuyến nghị.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
```

Điền `TELEGRAM_BOT_TOKEN`, một trong hai biến `ANTHROPIC_AUTH_TOKEN` hoặc
`ANTHROPIC_API_KEY`, `WEBHOOK_URL` và `WEBHOOK_SECRET_TOKEN` vào `.env`, sau đó chạy:

```bash
.venv/bin/python bot.py
```

Nếu cấu hình hợp lệ, bot mở HTTP server trên `PORT` và đăng ký webhook Telegram tại
`WEBHOOK_URL/telegram`.
