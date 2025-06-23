import os
from telegram import Bot, InputMediaPhoto, InputMediaVideo
import logging
import discord


logging.basicConfig(level=logging.DEBUG)
tg_bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
allowed_ids = os.getenv("ALLOWED_CHANNEL_IDS", "")
allowed_channels = set(map(int, allowed_ids.split(",")))

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author.bot:
        return
    if message.channel.id not in allowed_channels:
        return
    content = message.content or ""
    media = []
    documents = []

    for i, att in enumerate(message.attachments):
        url = att.url
        filename = att.filename
        
        if att.content_type and "image" in att.content_type:
            media.append(InputMediaPhoto(media=url, caption=content if i == 0 else None))
        elif att.content_type and "video" in att.content_type:
            media.append(InputMediaVideo(media=url, caption=content if i == 0 else None))
        else:
            documents.append((url, filename))
    try:
        if media:
            await tg_bot.send_media_group(chat_id=TG_CHAT_ID, media=media)
        elif content:
            await tg_bot.send_message(chat_id=TG_CHAT_ID, text=content)
        
        for url, filename in documents:
            await tg_bot.send_document(chat_id=TG_CHAT_ID, document=url, filename=filename)
        
    except Exception as e:
        print(f"TG error: {e}")

client.run(DISCORD_BOT_TOKEN)