# SmartSolve — Telegram study assistant bot

Telegram bot that helps solve math, physics, and other homework using Groq AI (free tier).

## Setup

1. Copy `.env.example` to `.env` and fill in your keys:
   - `TELEGRAM_BOT_TOKEN` — from [@BotFather](https://t.me/BotFather)
   - `GROQ_API_KEY` — free key from [console.groq.com](https://console.groq.com)

2. Install dependencies:
   ```bash
   python -m venv .venv
   .venv\Scripts\pip install -r requirements.txt
   ```

3. Run:
   ```bash
   .venv\Scripts\python bot.py
   ```

## Features

- Solve problems step by step (math, physics, chemistry, etc.)
- Explain topics in simple language
- Read problems from photos (Groq Vision)
- Russian and English UI
