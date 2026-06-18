# SmartSolve — Telegram study assistant bot

Telegram bot that helps solve math, physics, and other homework using Groq AI (free tier).

## Setup

1. Copy `.env.example` to `.env` and fill in your keys:
   - `TELEGRAM_BOT_TOKEN` — from [@BotFather](https://t.me/BotFather)
   - `OPENROUTER_API_KEY` — free key from [openrouter.ai/keys](https://openrouter.ai/keys)

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
- Read problems from photos (OpenRouter vision models)
- Russian and English UI

## AI providers

| Provider | Key | Free? |
|----------|-----|-------|
| **OpenRouter** (default) | [openrouter.ai/keys](https://openrouter.ai/keys) | Yes (`:free` models) |
| DeepSeek | [platform.deepseek.com](https://platform.deepseek.com/api_keys) | Free credits |
| Ollama | Local install, no key | Yes |
| Groq | [console.groq.com](https://console.groq.com/keys) | Yes |
