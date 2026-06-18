import base64
import logging

import httpx

from config import (
    AI_FALLBACK_PROVIDERS,
    AI_MAX_RETRIES,
    AI_MAX_TOKENS,
    AI_PROVIDER,
    DEEPSEEK_API_KEY,
    DEEPSEEK_MODEL,
    GROQ_API_KEY,
    GROQ_MODEL,
    GROQ_VISION_MODEL,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_VISION_MODEL,
    OPENROUTER_API_KEY,
    OPENROUTER_FALLBACK_MODELS,
    OPENROUTER_MODEL,
    OPENROUTER_VISION_MODEL,
    REQUEST_TIMEOUT,
)

logger = logging.getLogger(__name__)

PROMPTS = {
    "ru": {
        "system": """Ты — SmartSolve, умный помощник по учёбе. Ты помогаешь школьникам и студентам.

Твои задачи:
- Решать задачи по математике, физике, химии, информатике и другим предметам
- Объяснять теорию простым и понятным языком
- Распознавать текст и формулы на фотографиях задач
- Показывать пошаговое решение, а не только ответ

Форматирование (важно — ответ идёт в Telegram, LaTeX НЕ работает):
- НЕ используй LaTeX: без \\[, $$, \\frac, \\sqrt
- Дроби: (6 ± i√604) / 32
- Степени Unicode: x², x³, 10⁶
- Символы: √ ± × ÷ Δ π ≤ ≥ ≠ ≈ ∞
- Шаги: **Шаг 1.** или 📌 Шаг 1
- Ответ в конце: ✅ **Ответ:** ...
- Короткие абзацы, без лишних ---

Правила:
- Отвечай на русском языке
- Если задача неполная — уточни, что нужно
- Не выдумывай факты; если не уверен — скажи об этом
- Будь терпеливым и поддерживающим""",
        "solve": """Режим: РЕШЕНИЕ ЗАДАЧИ.
Разбери задачу по шагам:
1. Что дано и что нужно найти
2. Какие формулы/методы применимы
3. Пошаговое решение
4. Ответ (выдели его)
5. Краткая проверка, если возможно""",
        "explain": """Режим: ОБЪЯСНЕНИЕ ТЕМЫ.
Объясни тему так, чтобы понял ученик:
1. Простое определение
2. Ключевые идеи и аналогии из жизни
3. Основные формулы или правила (если есть)
4. 1–2 простых примера
5. Типичные ошибки, которых стоит избегать""",
        "vision": """На изображении может быть задача, формула, график или учебный материал.
1. Внимательно прочитай весь текст и формулы на фото
2. Если текст нечитаем — скажи об этом
3. Затем выполни запрос пользователя согласно выбранному режиму""",
        "vision_caption": "Дополнительный комментарий пользователя: {caption}",
        "no_vision": "Распознавание фото недоступно для текущего AI-провайдера. Опиши задачу текстом.",
        "fallback": "Не удалось получить ответ.",
    },
    "en": {
        "system": """You are SmartSolve, a smart study assistant for students.

Your tasks:
- Solve problems in math, physics, chemistry, computer science, and other subjects
- Explain theory in simple, clear language
- Read text and formulas from photos of homework and textbooks
- Show step-by-step solutions, not just the final answer

Formatting (important — replies go to Telegram, LaTeX does NOT render):
- Do NOT use LaTeX: no \\[, $$, \\frac, \\sqrt
- Fractions: (6 ± i√604) / 32
- Unicode powers: x², x³
- Symbols: √ ± × ÷ Δ π ≤ ≥ ≠ ≈ ∞
- Steps: **Step 1.** or 📌 Step 1
- Final answer: ✅ **Answer:** ...
- Short paragraphs

Rules:
- Reply in English
- If the problem is incomplete, ask what is missing
- Do not invent facts; say when you are unsure
- Be patient and supportive""",
        "solve": """Mode: PROBLEM SOLVING.
Break the problem down step by step:
1. Given data and what to find
2. Applicable formulas/methods
3. Step-by-step solution
4. Final answer (highlight it)
5. Quick check if possible""",
        "explain": """Mode: TOPIC EXPLANATION.
Explain the topic so a student can understand:
1. Simple definition
2. Key ideas and real-life analogies
3. Main formulas or rules (if any)
4. 1–2 simple examples
5. Common mistakes to avoid""",
        "vision": """The image may contain a problem, formula, graph, or study material.
1. Carefully read all text and formulas in the photo
2. If text is unreadable, say so
3. Then fulfill the user's request according to the selected mode""",
        "vision_caption": "Additional user comment: {caption}",
        "no_vision": "Photo recognition is not available for the current AI provider. Send the problem as text.",
        "fallback": "Could not get a response.",
    },
}

PROVIDER_CONFIG = {
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": OPENROUTER_API_KEY,
        "model": OPENROUTER_MODEL,
        "vision_model": OPENROUTER_VISION_MODEL,
        "key_url": "https://openrouter.ai/keys",
        "key_name": "OPENROUTER_API_KEY",
        "extra_headers": {
            "HTTP-Referer": "https://github.com/axtezzzi/SmartSolve",
            "X-Title": "SmartSolve Bot",
        },
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "api_key": DEEPSEEK_API_KEY,
        "model": DEEPSEEK_MODEL,
        "vision_model": None,
        "key_url": "https://platform.deepseek.com/api_keys",
        "key_name": "DEEPSEEK_API_KEY",
        "extra_headers": {},
    },
    "ollama": {
        "base_url": OLLAMA_BASE_URL.rstrip("/"),
        "api_key": "ollama",
        "model": OLLAMA_MODEL,
        "vision_model": OLLAMA_VISION_MODEL,
        "key_url": "https://ollama.com/download",
        "key_name": "OLLAMA (локально, ключ не нужен)",
        "extra_headers": {},
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "api_key": GROQ_API_KEY,
        "model": GROQ_MODEL,
        "vision_model": GROQ_VISION_MODEL,
        "key_url": "https://console.groq.com/keys",
        "key_name": "GROQ_API_KEY",
        "extra_headers": {},
    },
}

PROVIDER_FALLBACK_MARKERS = ("402", "403", "Insufficient Balance")


def _build_instruction(mode: str, lang: str, caption: str = "", with_vision: bool = False) -> str:
    prompts = PROMPTS.get(lang, PROMPTS["ru"])
    parts = [prompts["system"]]
    if with_vision:
        parts.append(prompts["vision"])
    mode_prompt = {"solve": prompts["solve"], "explain": prompts["explain"]}.get(mode, "")
    if mode_prompt:
        parts.append(mode_prompt)
    if caption.strip():
        parts.append(prompts["vision_caption"].format(caption=caption.strip()))
    return "\n\n".join(parts)


def _ollama_available() -> bool:
    base = OLLAMA_BASE_URL.rstrip("/").removesuffix("/v1")
    try:
        with httpx.Client(timeout=3.0, trust_env=False) as client:
            response = client.get(f"{base}/api/tags")
            return response.status_code == 200
    except Exception:
        return False


def _provider_available(name: str) -> bool:
    cfg = PROVIDER_CONFIG.get(name)
    if not cfg:
        return False
    if name == "ollama":
        return _ollama_available()
    return bool(cfg.get("api_key"))


class ProviderBackend:
    def __init__(self, name: str) -> None:
        self.name = name
        self.cfg = PROVIDER_CONFIG[name]

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.cfg["api_key"]:
            headers["Authorization"] = f"Bearer {self.cfg['api_key']}"
        headers.update(self.cfg.get("extra_headers") or {})
        return headers

    def _models_to_try(self, model: str) -> list[str]:
        models = [model]
        if self.name == "openrouter":
            for fallback in OPENROUTER_FALLBACK_MODELS:
                if fallback not in models:
                    models.append(fallback)
        return models

    def _complete(self, model: str, messages: list[dict], temperature: float) -> str:
        url = f"{self.cfg['base_url']}/chat/completions"
        last_error: Exception | None = None

        for current_model in self._models_to_try(model):
            for attempt in range(AI_MAX_RETRIES):
                payload = {
                    "model": current_model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": AI_MAX_TOKENS,
                }
                try:
                    with httpx.Client(timeout=REQUEST_TIMEOUT, trust_env=False) as client:
                        response = client.post(url, headers=self._headers(), json=payload)

                    if response.status_code == 429:
                        last_error = RuntimeError(
                            f"HTTP 429: rate limit on {current_model}"
                        )
                        break

                    if response.status_code >= 400:
                        last_error = RuntimeError(
                            f"HTTP {response.status_code}: {response.text[:300]}"
                        )
                        break

                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                except httpx.HTTPError as exc:
                    last_error = RuntimeError(str(exc))
                    break

        if last_error:
            raise last_error
        raise RuntimeError("AI request failed")

    def _text_messages(
        self,
        user_message: str,
        history: list[dict[str, str]],
        mode: str,
        lang: str,
    ) -> list[dict]:
        instruction = _build_instruction(mode, lang)
        messages: list[dict] = [{"role": "system", "content": instruction}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})
        return messages

    def chat(
        self,
        user_message: str,
        history: list[dict[str, str]],
        mode: str = "general",
        lang: str = "ru",
    ) -> str:
        prompts = PROMPTS.get(lang, PROMPTS["ru"])
        return (
            self._complete(
                self.cfg["model"],
                self._text_messages(user_message, history, mode, lang),
                temperature=0.4,
            )
            or prompts["fallback"]
        )

    def chat_with_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        caption: str,
        history: list[dict[str, str]],
        mode: str = "general",
        lang: str = "ru",
    ) -> str:
        prompts = PROMPTS.get(lang, PROMPTS["ru"])
        vision_model = self.cfg["vision_model"]
        if not vision_model:
            return prompts["no_vision"]

        instruction = _build_instruction(mode, lang, caption, with_vision=True)
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        content: list[dict] = [
            {"type": "text", "text": instruction},
            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_b64}"}},
        ]
        messages: list[dict] = list(history)
        messages.append({"role": "user", "content": content})
        return self._complete(vision_model, messages, temperature=0.3) or prompts["fallback"]


class AIService:
    def __init__(self) -> None:
        self.backends = self._build_chain()
        if not self.backends:
            raise ValueError(
                "Нет доступных AI-провайдеров. "
                "Укажи OPENROUTER_API_KEY или установи Ollama."
            )
        logger.info("AI chain: %s", " -> ".join(b.name for b in self.backends))

    def _build_chain(self) -> list[ProviderBackend]:
        order = [AI_PROVIDER, *AI_FALLBACK_PROVIDERS]
        seen: set[str] = set()
        backends: list[ProviderBackend] = []
        for name in order:
            name = name.strip().lower()
            if not name or name in seen or name not in PROVIDER_CONFIG:
                continue
            seen.add(name)
            if _provider_available(name):
                backends.append(ProviderBackend(name))
        return backends

    def _should_fallback(self, exc: Exception) -> bool:
        text = str(exc)
        return any(marker in text for marker in PROVIDER_FALLBACK_MARKERS)

    def chat(
        self,
        user_message: str,
        history: list[dict[str, str]],
        mode: str = "general",
        lang: str = "ru",
    ) -> str:
        errors: list[str] = []
        for backend in self.backends:
            try:
                return backend.chat(user_message, history, mode, lang)
            except Exception as exc:
                errors.append(f"{backend.name}: {exc}")
                if self._should_fallback(exc):
                    logger.warning("Provider %s failed, trying next: %s", backend.name, exc)
                    continue
                raise RuntimeError(f"AI error ({backend.name}): {exc}") from exc
        raise RuntimeError("All AI providers failed:\n" + "\n".join(errors))

    def chat_with_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        caption: str,
        history: list[dict[str, str]],
        mode: str = "general",
        lang: str = "ru",
    ) -> str:
        errors: list[str] = []
        for backend in self.backends:
            try:
                return backend.chat_with_image(
                    image_bytes, mime_type, caption, history, mode, lang
                )
            except Exception as exc:
                errors.append(f"{backend.name}: {exc}")
                if self._should_fallback(exc):
                    logger.warning("Vision provider %s failed, trying next", backend.name)
                    continue
                raise RuntimeError(f"AI vision error ({backend.name}): {exc}") from exc
        raise RuntimeError("All AI providers failed:\n" + "\n".join(errors))
