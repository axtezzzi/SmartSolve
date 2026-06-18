import base64

from groq import Groq

from config import GROQ_API_KEY, GROQ_MODEL, GROQ_VISION_MODEL

PROMPTS = {
    "ru": {
        "system": """Ты — SmartSolve, умный помощник по учёбе. Ты помогаешь школьникам и студентам.

Твои задачи:
- Решать задачи по математике, физике, химии, информатике и другим предметам
- Объяснять теорию простым и понятным языком
- Распознавать текст и формулы на фотографиях задач
- Показывать пошаговое решение, а не только ответ
- Использовать формулы в LaTeX там, где это уместно (например: $E = mc^2$)

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
        "fallback": "Не удалось получить ответ.",
    },
    "en": {
        "system": """You are SmartSolve, a smart study assistant for students.

Your tasks:
- Solve problems in math, physics, chemistry, computer science, and other subjects
- Explain theory in simple, clear language
- Read text and formulas from photos of homework and textbooks
- Show step-by-step solutions, not just the final answer
- Use LaTeX for formulas when appropriate (e.g. $E = mc^2$)

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
        "fallback": "Could not get a response.",
    },
}


class AIService:
    def __init__(self) -> None:
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not set. Get a free key at https://console.groq.com")
        self.client = Groq(api_key=GROQ_API_KEY)

    def _prompts(self, lang: str) -> dict[str, str]:
        return PROMPTS.get(lang, PROMPTS["ru"])

    def _build_text_messages(
        self,
        user_message: str,
        history: list[dict[str, str]],
        mode: str,
        lang: str,
    ) -> list[dict[str, str]]:
        prompts = self._prompts(lang)
        mode_prompt = {"solve": prompts["solve"], "explain": prompts["explain"]}.get(mode, "")

        messages: list[dict[str, str]] = [{"role": "system", "content": prompts["system"]}]
        if mode_prompt:
            messages.append({"role": "system", "content": mode_prompt})
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
        prompts = self._prompts(lang)
        messages = self._build_text_messages(user_message, history, mode, lang)

        response = self.client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.4,
            max_tokens=4096,
        )
        return response.choices[0].message.content or prompts["fallback"]

    def chat_with_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        caption: str,
        history: list[dict[str, str]],
        mode: str = "general",
        lang: str = "ru",
    ) -> str:
        prompts = self._prompts(lang)
        mode_prompt = {"solve": prompts["solve"], "explain": prompts["explain"]}.get(mode, "")

        instruction_parts = [prompts["system"], prompts["vision"]]
        if mode_prompt:
            instruction_parts.append(mode_prompt)
        if caption.strip():
            instruction_parts.append(prompts["vision_caption"].format(caption=caption.strip()))

        instruction = "\n\n".join(instruction_parts)
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        # Vision models on Groq work best without separate system messages.
        content: list[dict] = [
            {"type": "text", "text": instruction},
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{image_b64}"},
            },
        ]

        messages: list[dict] = []
        messages.extend(history)
        messages.append({"role": "user", "content": content})

        response = self.client.chat.completions.create(
            model=GROQ_VISION_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=4096,
        )
        return response.choices[0].message.content or prompts["fallback"]
