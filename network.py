import os

import httpx

COMMON_PROXY_PORTS = (10808, 7890, 7891, 1080, 10809, 8080, 9050)


def _telegram_reachable(client: httpx.Client) -> bool:
    try:
        response = client.get("https://api.telegram.org", timeout=10.0)
        return response.status_code < 500
    except Exception:
        return False


def resolve_telegram_proxy() -> str | None:
    """Pick a working Telegram route: explicit proxy, auto-detect, or direct."""
    raw = os.getenv("TELEGRAM_PROXY", "auto").strip()

    if raw.lower() in {"", "none", "off", "direct", "false", "0"}:
        return None

    if raw.lower() != "auto":
        return raw

    try:
        with httpx.Client(timeout=5.0, trust_env=False) as client:
            if _telegram_reachable(client):
                return None
    except Exception:
        pass

    for port in COMMON_PROXY_PORTS:
        proxy = f"socks5://127.0.0.1:{port}"
        try:
            with httpx.Client(proxy=proxy, timeout=3.0, trust_env=False) as client:
                if _telegram_reachable(client):
                    return proxy
        except Exception:
            continue

    return None


def build_telegram_request(connect_timeout: float, proxy: str | None):
    from telegram.request import HTTPXRequest

    return HTTPXRequest(
        connect_timeout=connect_timeout,
        read_timeout=connect_timeout,
        write_timeout=connect_timeout,
        pool_timeout=connect_timeout,
        proxy=proxy,
        httpx_kwargs={"trust_env": False},
    )
