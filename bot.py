import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from brain import generate_post, generate_post_from_image

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# HTTPX includes the complete request URL in INFO logs. Telegram embeds the bot
# token in that URL, so keep HTTP client logs at WARNING or above.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


def _load_config() -> str:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    missing = []

    if not token:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not (
        os.environ.get("ANTHROPIC_AUTH_TOKEN", "").strip()
        or os.environ.get("ANTHROPIC_API_KEY", "").strip()
    ):
        missing.append("ANTHROPIC_AUTH_TOKEN (or ANTHROPIC_API_KEY)")

    if missing:
        env_path = BASE_DIR / ".env"
        raise SystemExit(
            f"Missing required configuration: {', '.join(missing)}. "
            f"Add it to {env_path} or export it as an environment variable."
        )

    return token


def _webhook_config() -> tuple[str, int, str, str]:
    public_url = os.environ.get("WEBHOOK_URL", "").strip().rstrip("/")
    secret_token = os.environ.get("WEBHOOK_SECRET_TOKEN", "").strip()
    port_value = os.environ.get("PORT", "8080").strip()

    missing = []
    if not public_url:
        missing.append("WEBHOOK_URL")
    if not secret_token:
        missing.append("WEBHOOK_SECRET_TOKEN")
    if missing:
        raise SystemExit(
            "Missing required webhook configuration: " + ", ".join(missing)
        )

    try:
        port = int(port_value)
    except ValueError as exc:
        raise SystemExit(f"PORT must be an integer, got: {port_value!r}") from exc

    url_path = "telegram"
    return f"{public_url}/{url_path}", port, url_path, secret_token


async def start(update: Update, context) -> None:
    await update.message.reply_text(
        "Chào bạn! 👋\n\n"
        "Có 2 cách dùng:\n"
        "1. Gửi ý tưởng bằng văn bản, mình sẽ viết thành bài Facebook.\n"
        "2. Gửi ảnh sản phẩm (có thể kèm caption), mình sẽ đọc thông tin trên ảnh rồi viết bài.\n\n"
        "Phong cách bài viết sẽ bám theo các bài mẫu bạn đã lưu."
    )


async def handle_message(update: Update, context) -> None:
    raw_content = update.message.text

    await update.message.chat.send_action(ChatAction.TYPING)

    try:
        post = await asyncio.to_thread(generate_post, raw_content)
        await update.message.reply_text(post)
    except Exception:
        logger.exception("Failed to generate post")
        await update.message.reply_text(
            "Có lỗi xảy ra khi tạo bài viết. Vui lòng thử lại sau."
        )


async def handle_photo(update: Update, context) -> None:
    photo = update.message.photo[-1]
    caption = update.message.caption or ""

    await update.message.chat.send_action(ChatAction.TYPING)

    try:
        file = await photo.get_file()
        image_bytes = bytes(await file.download_as_bytearray())

        post = await asyncio.to_thread(
            generate_post_from_image, image_bytes, caption, "image/jpeg"
        )
        await update.message.reply_text(post)
    except Exception:
        logger.exception("Failed to generate post from image")
        await update.message.reply_text(
            "Có lỗi xảy ra khi đọc ảnh và tạo bài viết. Vui lòng thử lại sau."
        )


def main() -> None:
    token = _load_config()
    webhook_url, port, url_path, secret_token = _webhook_config()

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot webhook is running on port %s", port)
    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=url_path,
        webhook_url=webhook_url,
        secret_token=secret_token,
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=False,
    )


if __name__ == "__main__":
    main()
