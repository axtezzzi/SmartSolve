import asyncio
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
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
from config import MAX_HISTORY, MAX_IMAGE_BYTES, MAX_MESSAGE_LENGTH, TELEGRAM_BOT_TOKEN
from i18n import modes, t

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

SUPPORTED_LANGS = ("ru", "en")


def get_lang(context: ContextTypes.DEFAULT_TYPE) -> str:
    lang = context.user_data.get("lang", "ru")
    return lang if lang in SUPPORTED_LANGS else "ru"


def get_history(context: ContextTypes.DEFAULT_TYPE) -> list[dict[str, str]]:
    return context.user_data.setdefault("history", [])


def get_mode(context: ContextTypes.DEFAULT_TYPE) -> str:
    return context.user_data.get("mode", "general")


def append_history(context: ContextTypes.DEFAULT_TYPE, role: str, content: str) -> None:
    history = get_history(context)
    history.append({"role": role, "content": content})
    if len(history) > MAX_HISTORY * 2:
        del history[:2]


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
            f"{'✅ ' if code == current_lang else ''}{t(lang, 'lang_names')[code]}",
            callback_data=f"lang:{code}",
        )
        for code in SUPPORTED_LANGS
    ]
    return InlineKeyboardMarkup([mode_buttons, lang_buttons])


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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.clear()
    lang = get_lang(context)
    await update.message.reply_text(
        t(lang, "start"),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_keyboard(lang, get_mode(context), lang),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_lang(context)
    await update.message.reply_text(t(lang, "help"), parse_mode=ParseMode.MARKDOWN)


async def mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_lang(context)
    mode = get_mode(context)
    await update.message.reply_text(
        t(lang, "mode_current", mode=modes(lang)[mode]),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_keyboard(lang, mode, lang),
    )


async def lang_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_lang(context)
    await update.message.reply_text(
        t(lang, "lang_current", lang=t(lang, "lang_names")[lang]),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_keyboard(lang, get_mode(context), lang),
    )


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_lang(context)
    context.user_data["history"] = []
    await update.message.reply_text(t(lang, "clear_done"))


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


async def lang_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    new_lang = query.data.split(":", 1)[1]
    if new_lang not in SUPPORTED_LANGS:
        return
    context.user_data["lang"] = new_lang
    await query.edit_message_text(
        t(new_lang, "lang_selected", lang=t(new_lang, "lang_names")[new_lang]),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_keyboard(new_lang, get_mode(context), new_lang),
    )


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
    lang = get_lang(context)
    append_history(context, "user", user_history_text)
    append_history(context, "assistant", reply)
    for part in split_message(reply):
        await update.message.reply_text(part)


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
        await update.message.reply_text(
            t(lang, "ai_error", error=exc),
            parse_mode=ParseMode.MARKDOWN,
        )
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
        await update.message.reply_text(
            t(lang, "ai_error", error=exc),
            parse_mode=ParseMode.MARKDOWN,
        )
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
    await ask_ai(update, context, text.strip())


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await ask_ai_with_photo(update, context)


def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN not set. Create a .env file.")

    ai = AIService()
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.bot_data["ai"] = ai

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
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
