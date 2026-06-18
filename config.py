import os
from dotenv import load_dotenv

load_dotenv()


def _pick_default_provider() -> str:
    if os.getenv("OPENROUTER_API_KEY"):
        return "openrouter"
    if os.getenv("DEEPSEEK_API_KEY"):
        return "deepseek"
    if os.getenv("OLLAMA_BASE_URL"):
        return "ollama"
    if os.getenv("GROQ_API_KEY"):
        return "groq"
    return "openrouter"


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-20b:free")
OPENROUTER_VISION_MODEL = os.getenv(
    "OPENROUTER_VISION_MODEL",
    "nvidia/nemotron-nano-12b-v2-vl:free",
)
OPENROUTER_FALLBACK_MODELS = [
    m.strip()
    for m in os.getenv("OPENROUTER_FALLBACK_MODELS", "").split(",")
    if m.strip()
]

AI_MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS", "2048"))
AI_MAX_RETRIES = int(os.getenv("AI_MAX_RETRIES", "1"))
AI_MIN_REQUEST_INTERVAL = float(os.getenv("AI_MIN_REQUEST_INTERVAL", "3"))

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_VISION_MODEL = os.getenv("OLLAMA_VISION_MODEL", "llava")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_VISION_MODEL = os.getenv(
    "GROQ_VISION_MODEL",
    "meta-llama/llama-4-scout-17b-16e-instruct",
)

AI_PROVIDER = os.getenv("AI_PROVIDER", _pick_default_provider()).lower()
AI_FALLBACK_PROVIDERS = [
    p.strip().lower()
    for p in os.getenv("AI_FALLBACK_PROVIDERS", "openrouter,ollama").split(",")
    if p.strip()
]

REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "60"))
MAX_HISTORY = 10
MAX_MESSAGE_LENGTH = 4096
MAX_IMAGE_BYTES = 2_800_000
