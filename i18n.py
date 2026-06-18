from typing import Any

TEXTS: dict[str, dict[str, Any]] = {
    "ru": {
        "modes": {
            "general": "💬 Общий",
            "solve": "📝 Решить задачу",
            "explain": "📚 Объяснить тему",
        },
        "start": (
            "👋 Привет! Я **SmartSolve** — помощник по учёбе.\n\n"
            "Могу помочь с:\n"
            "• 📝 Решением задач (математика, физика, химия и др.)\n"
            "• 📚 Объяснением тем и теории\n"
            "• 📷 Распознаванием задач с фото\n\n"
            "Выбери режим и язык кнопками ниже, затем напиши вопрос или отправь фото.\n\n"
            "Команды:\n"
            "/mode — сменить режим\n"
            "/lang — сменить язык\n"
            "/clear — очистить историю\n"
            "/help — справка"
        ),
        "help": (
            "**Как пользоваться:**\n\n"
            "1. Выбери режим: общий, решение задачи или объяснение темы\n"
            "2. Отправь текст или **фото задачи** (можно с подписью)\n"
            "3. Бот распознает текст на фото и решит или объяснит\n\n"
            "**Советы:**\n"
            "• Снимай задачу чётко, без бликов\n"
            "• Добавь подпись, если нужны уточнения\n"
            "• /clear сбрасывает контекст\n"
            "• /lang переключает русский и английский"
        ),
        "mode_current": "Текущий режим: **{mode}**",
        "mode_selected": "Режим: **{mode}**\n\nНапиши вопрос или отправь фото.",
        "lang_current": "Текущий язык: **{lang}**",
        "lang_selected": "Язык: **{lang}**\n\nИнтерфейс и ответы будут на этом языке.",
        "lang_names": {"ru": "🇷🇺 Русский", "en": "🇬🇧 English"},
        "clear_done": "🗑 История диалога очищена.",
        "send_text": "Отправь текст задачи или вопрос.",
        "send_text_or_photo": "Отправь текст или фото с задачей.",
        "processing_photo": "📷 Распознаю фото…",
        "photo_too_large": "❌ Фото слишком большое. Отправь более чёткий снимок или уменьши размер.",
        "busy": "⏳ Уже обрабатываю предыдущий запрос. Подожди немного.",
        "please_wait": "⏳ Подожди {seconds} сек. перед следующим запросом.",
        "ai_error": (
            "❌ Ошибка при обращении к нейросети:\n`{error}`\n\n"
            "Проверь API-ключ или попробуй позже."
        ),
        "ai_rate_limit": (
            "⏳ **Слишком много запросов** (лимит бесплатной модели).\n\n"
            "Подожди 1–2 минуты и попробуй снова.\n"
            "Или установи **Ollama** — бесплатно и без лимитов."
        ),
        "ai_not_found": (
            "❌ **Модель не найдена** (HTTP 404).\n\n"
            "Обнови модель в `.env`:\n"
            "`OPENROUTER_MODEL=openai/gpt-oss-20b:free`"
        ),
        "ai_payment_required": (
            "💳 **Закончился баланс** на DeepSeek/OpenRouter.\n\n"
            "Варианты:\n"
            "1. В `.env` поставь `AI_PROVIDER=openrouter` (бесплатные модели)\n"
            "2. Установи **Ollama** — [ollama.com](https://ollama.com) → `AI_PROVIDER=ollama`\n"
            "3. Пополни баланс DeepSeek на platform.deepseek.com"
        ),
        "photo_history": "[Фото{suffix}]",
    },
    "en": {
        "modes": {
            "general": "💬 General",
            "solve": "📝 Solve problem",
            "explain": "📚 Explain topic",
        },
        "start": (
            "👋 Hi! I'm **SmartSolve** — your study assistant.\n\n"
            "I can help with:\n"
            "• 📝 Solving problems (math, physics, chemistry, etc.)\n"
            "• 📚 Explaining topics and theory\n"
            "• 📷 Reading problems from photos\n\n"
            "Pick a mode and language below, then send a question or a photo.\n\n"
            "Commands:\n"
            "/mode — change mode\n"
            "/lang — change language\n"
            "/clear — clear chat history\n"
            "/help — help"
        ),
        "help": (
            "**How to use:**\n\n"
            "1. Choose a mode: general, solve problem, or explain topic\n"
            "2. Send text or a **photo of the problem** (caption optional)\n"
            "3. The bot reads the image and solves or explains\n\n"
            "**Tips:**\n"
            "• Take a clear photo without glare\n"
            "• Add a caption if you need extra context\n"
            "• /clear resets the conversation\n"
            "• /lang switches between Russian and English"
        ),
        "mode_current": "Current mode: **{mode}**",
        "mode_selected": "Mode: **{mode}**\n\nSend a question or a photo.",
        "lang_current": "Current language: **{lang}**",
        "lang_selected": "Language: **{lang}**\n\nUI and replies will use this language.",
        "lang_names": {"ru": "🇷🇺 Русский", "en": "🇬🇧 English"},
        "clear_done": "🗑 Chat history cleared.",
        "send_text": "Send a problem or question as text.",
        "send_text_or_photo": "Send text or a photo of the problem.",
        "processing_photo": "📷 Reading the photo…",
        "photo_too_large": "❌ Photo is too large. Send a clearer shot or a smaller image.",
        "busy": "⏳ Already processing your previous request. Please wait.",
        "please_wait": "⏳ Wait {seconds}s before sending another request.",
        "ai_error": (
            "❌ AI request failed:\n`{error}`\n\n"
            "Check your API key or try again later."
        ),
        "ai_rate_limit": (
            "⏳ **Too many requests** (free model rate limit).\n\n"
            "Wait 1–2 minutes and try again.\n"
            "Or install **Ollama** — free with no limits."
        ),
        "ai_not_found": (
            "❌ **Model not found** (HTTP 404).\n\n"
            "Update model in `.env`:\n"
            "`OPENROUTER_MODEL=openai/gpt-oss-20b:free`"
        ),
        "ai_payment_required": (
            "💳 **Balance exhausted** on DeepSeek/OpenRouter.\n\n"
            "Options:\n"
            "1. Set `AI_PROVIDER=openrouter` in `.env` (free models)\n"
            "2. Install **Ollama** — [ollama.com](https://ollama.com) → `AI_PROVIDER=ollama`\n"
            "3. Top up DeepSeek at platform.deepseek.com"
        ),
        "photo_history": "[Photo{suffix}]",
    },
}


def t(lang: str, key: str, **kwargs: Any) -> str:
    bundle = TEXTS.get(lang, TEXTS["ru"])
    value = bundle.get(key, TEXTS["ru"][key])
    if isinstance(value, str) and kwargs:
        return value.format(**kwargs)
    return value


def modes(lang: str) -> dict[str, str]:
    return TEXTS.get(lang, TEXTS["ru"])["modes"]
