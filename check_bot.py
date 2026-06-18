"""Проверка настроек бота перед запуском."""
import os
import sys

import httpx
from dotenv import load_dotenv

from ai_service import PROVIDER_CONFIG
from config import AI_PROVIDER
from network import resolve_telegram_proxy

load_dotenv()


def check(name: str, ok: bool, detail: str = "") -> None:
    status = "OK" if ok else "FAIL"
    line = f"[{status}] {name}"
    if detail:
        line += f" — {detail}"
    print(line)


def _valid_key(value: str | None) -> bool:
    if not value:
        return False
    return value not in {"...", "your_openrouter_api_key", "your_gemini_api_key", "your_groq_api_key"}


def main() -> int:
    print("=== SmartSolve diagnostics ===\n")

    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    proxy_setting = os.getenv("TELEGRAM_PROXY", "auto")
    cfg = PROVIDER_CONFIG.get(AI_PROVIDER, {})

    check("TELEGRAM_BOT_TOKEN", bool(token))
    check("AI_PROVIDER", AI_PROVIDER in PROVIDER_CONFIG, AI_PROVIDER)
    if AI_PROVIDER != "ollama":
        check(cfg.get("key_name", "API key"), _valid_key(cfg.get("api_key")), cfg.get("key_url", ""))

    print("\n--- Telegram ---")
    proxy = resolve_telegram_proxy()
    print(f"Route: {proxy or 'direct'}")
    try:
        client_kwargs: dict = {"timeout": 20.0, "trust_env": False}
        if proxy:
            client_kwargs["proxy"] = proxy
        with httpx.Client(**client_kwargs) as client:
            r = client.get(f"https://api.telegram.org/bot{token}/getMe")
            data = r.json()
            if data.get("ok"):
                check("Telegram API", True, f"@{data['result']['username']}")
            else:
                check("Telegram API", False, str(data))
    except Exception as exc:
        check("Telegram API", False, str(exc))

    print("\n--- AI ---")
    try:
        from ai_service import AIService

        ai = AIService()
        reply = ai.chat("Сколько будет 2+2?", [], "general", "ru")
        check(f"AI ({AI_PROVIDER})", bool(reply), reply[:80].replace("\n", " "))
    except Exception as exc:
        check(f"AI ({AI_PROVIDER})", False, str(exc))
        print(f"  -> Получи ключ: {cfg.get('key_url', '')}")
        print(f"  -> В .env: {cfg.get('key_name', '')}=...")

    return 0


if __name__ == "__main__":
    sys.exit(main())
