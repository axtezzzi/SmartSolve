import asyncio
import logging
import time

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from ai_service import AIService
from config import (
    AI_MIN_REQUEST_INTERVAL,
    AI_PROVIDER,
    MAX_HISTORY,
    MAX_IMAGE_BYTES,
    MAX_MESSAGE_LENGTH,
    REQUEST_TIMEOUT,
    TELEGRAM_BOT_TOKEN,
)
from network import build_telegram_request, resolve_telegram_proxy
from formatting import format_for_telegram
from i18n import modes, t

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

SUPPORTED_LANGS = ("ru", "en")
LANG_REPLY_BUTTONS = {"🇷🇺 Русский": "ru", "🇬🇧 English": "en"}


def get_lang(context: ContextTypes.DEFAULT_TYPE) -> str:
    lang = context.user_data.get("lang", "ru")
    return lang if lang in SUPPORTED_LANGS else "ru"


def get_history(context: ContextTypes.DEFAULT_TYPE) -> list[dict[str, str]]:
    return context.user_data.setdefault("history", [])


def get_mode(context: ContextTypes.DEFAULT_TYPE) -> str:
    return context.user_data.get("mode", "general")


def reset_session(context: ContextTypes.DEFAULT_TYPE, *, keep_lang: bool = True) -> None:
    saved_lang = context.user_data.get("lang") if keep_lang else None
    context.user_data.clear()
    if saved_lang in SUPPORTED_LANGS:
        context.user_data["lang"] = saved_lang


def lang_label(code: str) -> str:
    return t("ru", "lang_names")[code]


def language_inline_keyboard(current: str | None = None) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    f"{'✅ ' if code == current else ''}{lang_label(code)}",
                    callback_data=f"lang:{code}",
                )
                for code in SUPPORTED_LANGS
            ]
        ]
    )


def reply_language_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[KeyboardButton(text) for text in LANG_REPLY_BUTTONS]],
        resize_keyboard=True,
        is_persistent=True,
    )


def main_keyboard(lang: str, current_mode: str, current_lang: str) -> InlineKeyboardMarkup:
    mode_buttons = [
        InlineKeyboardButton(
            f"{'✅ ' if key == current_mode else ''}{label}",
            callback_data=f"mode:{key}",
        )
        for key, label in modes(lang).items()
    ]
    lang_buttons = [
        InlineKeyboardButton(
            f"{'✅ ' if code == current_lang else ''}{lang_label(code)}",
            callback_data=f"lang:{code}",
        )
        for code in SUPPORTED_LANGS
    ]
    return InlineKeyboardMarkup([mode_buttons, lang_buttons])


def append_history(context: ContextTypes.DEFAULT_TYPE, role: str, content: str) -> None:
    history = get_history(context)
    history.append({"role": role, "content": content})
    if len(history) > MAX_HISTORY * 2:
        del history[:2]


def split_message(text: str, limit: int = MAX_MESSAGE_LENGTH) -> list[str]:
    if len(text) <= limit:
        return [text]

    parts: list[str] = []
    while text:
        if len(text) <= limit:
            parts.append(text)
            break
        split_at = text.rfind("\n", 0, limit)
        if split_at == -1:
            split_at = limit
        parts.append(text[:split_at])
        text = text[split_at:].lstrip()
    return parts


async def send_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_lang(context)
    await update.message.reply_text(
        t(lang, "start"),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_language_keyboard(),
    )
    await update.message.reply_text(
        t(lang, "keyboard_lang"),
        reply_markup=main_keyboard(lang, get_mode(context), lang),
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    reset_session(context, keep_lang=True)
    if "lang" not in context.user_data:
        context.user_data["awaiting_lang"] = True
        await update.message.reply_text(
            t("ru", "choose_lang"),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=language_inline_keyboard(),
        )
        return
    await send_welcome(update, context)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_lang(context)
    await update.message.reply_text(
        t(lang, "help"),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_language_keyboard(),
    )


async def mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_lang(context)
    mode = get_mode(context)
    await update.message.reply_text(
        t(lang, "mode_current", mode=modes(lang)[mode]),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_keyboard(lang, mode, lang),
    )
    await update.message.reply_text(
        t(lang, "keyboard_lang"),
        reply_markup=reply_language_keyboard(),
    )


async def lang_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_lang(context)
    await update.message.reply_text(
        t(lang, "lang_current", lang=lang_label(lang)),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=language_inline_keyboard(lang),
    )


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_lang(context)
    reset_session(context, keep_lang=True)
    await update.message.reply_text(
        t(lang, "clear_done"),
        reply_markup=reply_language_keyboard(),
    )


async def mode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    lang = get_lang(context)
    mode = query.data.split(":", 1)[1]
    context.user_data["mode"] = mode
    await query.edit_message_text(
        t(lang, "mode_selected", mode=modes(lang)[mode]),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_keyboard(lang, mode, lang),
    )


async def apply_language(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    new_lang: str,
    *,
    via_callback: bool = False,
) -> None:
    if new_lang not in SUPPORTED_LANGS:
        return

    context.user_data["lang"] = new_lang
    first_setup = context.user_data.pop("awaiting_lang", False)
    mode = get_mode(context)
    inline_markup = main_keyboard(new_lang, mode, new_lang)

    if first_setup:
        text = t(new_lang, "start")
    else:
        text = t(new_lang, "lang_selected", lang=lang_label(new_lang))

    if via_callback:
        query = update.callback_query
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=inline_markup,
        )
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=t(new_lang, "keyboard_lang"),
            reply_markup=reply_language_keyboard(),
        )
        return

    await update.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_language_keyboard(),
    )
    await update.message.reply_text(
        t(new_lang, "keyboard_lang"),
        reply_markup=inline_markup,
    )


async def lang_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    new_lang = query.data.split(":", 1)[1]
    await apply_language(update, context, new_lang, via_callback=True)


async def download_photo_bytes(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> tuple[bytes, str] | None:
    photos = update.message.photo
    for photo in reversed(photos):
        file = await context.bot.get_file(photo.file_id)
        data = bytes(await file.download_as_bytearray())
        if len(data) <= MAX_IMAGE_BYTES:
            return data, "image/jpeg"
    return None


async def send_ai_reply(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    reply: str,
    user_history_text: str,
) -> None:
    append_history(context, "user", user_history_text)
    append_history(context, "assistant", reply)
    formatted = format_for_telegram(reply)
    for part in split_message(formatted):
        try:
            await update.message.reply_text(part, parse_mode=ParseMode.HTML)
        except Exception:
            await update.message.reply_text(part)


async def reply_ai_error(update: Update, lang: str, exc: Exception) -> None:
    error_text = str(exc)
    if "402" in error_text or "Insufficient Balance" in error_text:
        await update.message.reply_text(
            t(lang, "ai_payment_required"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return
    if "404" in error_text or "No endpoints found" in error_text:
        await update.message.reply_text(
            t(lang, "ai_not_found"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return
    if "429" in error_text or "rate limit" in error_text.lower():
        await update.message.reply_text(
            t(lang, "ai_rate_limit"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return
    await update.message.reply_text(
        t(lang, "ai_error", error=error_text),
        parse_mode=ParseMode.MARKDOWN,
    )


def get_user_lock(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> asyncio.Lock:
    locks: dict[int, asyncio.Lock] = context.application.bot_data.setdefault("user_locks", {})
    if user_id not in locks:
        locks[user_id] = asyncio.Lock()
    return locks[user_id]


def is_duplicate_message(context: ContextTypes.DEFAULT_TYPE, message_id: int) -> bool:
    last_id = context.user_data.get("last_processed_msg_id")
    if last_id == message_id:
        return True
    context.user_data["last_processed_msg_id"] = message_id
    return False


async def wait_cooldown(context: ContextTypes.DEFAULT_TYPE, lang: str, update: Update) -> bool:
    last_at = context.user_data.get("last_request_at", 0.0)
    elapsed = time.monotonic() - last_at
    if elapsed < AI_MIN_REQUEST_INTERVAL:
        wait_sec = int(AI_MIN_REQUEST_INTERVAL - elapsed) + 1
        await update.message.reply_text(t(lang, "please_wait", seconds=wait_sec))
        return False
    context.user_data["last_request_at"] = time.monotonic()
    return True


async def process_with_lock(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    handler,
    *args,
) -> None:
    user_id = update.effective_user.id
    lang = get_lang(context)
    lock = get_user_lock(context, user_id)

    if lock.locked():
        await update.message.reply_text(t(lang, "busy"))
        return

    async with lock:
        if not await wait_cooldown(context, lang, update):
            return
        await handler(update, context, *args)


async def ask_ai(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    ai: AIService = context.application.bot_data["ai"]
    chat_id = update.effective_chat.id
    lang = get_lang(context)
    mode = get_mode(context)

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    try:
        reply = await asyncio.to_thread(ai.chat, text, get_history(context), mode, lang)
    except Exception as exc:
        logger.exception("AI request failed")
        await reply_ai_error(update, lang, exc)
        return

    await send_ai_reply(update, context, reply, text)


async def ask_ai_with_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ai: AIService = context.application.bot_data["ai"]
    chat_id = update.effective_chat.id
    lang = get_lang(context)
    mode = get_mode(context)
    caption = update.message.caption or ""

    await update.message.reply_text(t(lang, "processing_photo"))
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_PHOTO)

    photo_data = await download_photo_bytes(update, context)
    if photo_data is None:
        await update.message.reply_text(t(lang, "photo_too_large"))
        return

    image_bytes, mime_type = photo_data
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    try:
        reply = await asyncio.to_thread(
            ai.chat_with_image,
            image_bytes,
            mime_type,
            caption,
            get_history(context),
            mode,
            lang,
        )
    except Exception as exc:
        logger.exception("Vision AI request failed")
        await reply_ai_error(update, lang, exc)
        return

    suffix = f": {caption.strip()}" if caption.strip() else ""
    history_label = t(lang, "photo_history", suffix=suffix)
    await send_ai_reply(update, context, reply, history_label)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_lang(context)
    text = update.message.text
    if not text or not text.strip():
        await update.message.reply_text(t(lang, "send_text"))
        return

    stripped = text.strip()
    if stripped in LANG_REPLY_BUTTONS:
        await apply_language(update, context, LANG_REPLY_BUTTONS[stripped])
        return

    if "lang" not in context.user_data:
        context.user_data["awaiting_lang"] = True
        await update.message.reply_text(
            t("ru", "choose_lang"),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=language_inline_keyboard(),
        )
        return

    if is_duplicate_message(context, update.message.message_id):
        return
    await process_with_lock(update, context, ask_ai, stripped)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if is_duplicate_message(context, update.message.message_id):
        return
    await process_with_lock(update, context, ask_ai_with_photo)


def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN not set. Create a .env file.")

    ai = AIService()
    telegram_proxy = resolve_telegram_proxy()
    request = build_telegram_request(REQUEST_TIMEOUT, telegram_proxy)

    app = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .request(request)
        .get_updates_request(request)
        .build()
    )
    app.bot_data["ai"] = ai
    if telegram_proxy:
        logger.info("Telegram route: proxy %s", telegram_proxy)
    else:
        logger.info("Telegram route: direct (trust_env=False)")
    logger.info("AI provider: %s", AI_PROVIDER)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("mode", mode_command))
    app.add_handler(CommandHandler("lang", lang_command))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(CallbackQueryHandler(mode_callback, pattern=r"^mode:"))
    app.add_handler(CallbackQueryHandler(lang_callback, pattern=r"^lang:"))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("SmartSolve bot started")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
