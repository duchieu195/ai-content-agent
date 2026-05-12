import asyncio
import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from brain import generate_post, generate_post_from_image

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


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
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set in .env")

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
