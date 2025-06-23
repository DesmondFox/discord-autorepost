from quart import Quart, request
import os
from telegram import Bot, InputMediaPhoto, InputMediaVideo
import logging
import asyncio

logging.basicConfig(level=logging.DEBUG)
app = Quart(__name__)
bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

@app.route("/webhook", methods=["POST"])
async def webhook():
    data = await request.get_json()
    app.logger.debug(f"Received data: {data}")
    content = data.get("content", "")
    attachments = data.get("attachments", [])
 
    media = []
    for i, att in enumerate(attachments):
        url = att.get("url")
        mime = att.get("content_type", "")

        if not url:
            continue

        if "image" in mime:
            media.append(InputMediaPhoto(media=url, caption=content if i == 0 else None))
        elif "video" in mime:
            media.append(InputMediaVideo(media=url, caption=content if i == 0 else None))

    if media:
        await bot.send_media_group(chat_id=CHAT_ID, media=media)
    elif content:
        await bot.send_message(chat_id=CHAT_ID, text=content)

    return {"status": "ok"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003)