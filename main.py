import os
from telegram import Bot, InputMediaPhoto, InputMediaVideo
import logging
import discord
import sys


logging.basicConfig(level=logging.DEBUG)

# Get environment variables with proper error handling
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Validate required environment variables
if not TELEGRAM_BOT_TOKEN:
    logging.error("TELEGRAM_BOT_TOKEN environment variable is required")
    sys.exit(1)
if not TG_CHAT_ID:
    logging.error("TELEGRAM_CHAT_ID environment variable is required")
    sys.exit(1)
if not DISCORD_BOT_TOKEN:
    logging.error("DISCORD_BOT_TOKEN environment variable is required")
    sys.exit(1)

tg_bot = Bot(token=TELEGRAM_BOT_TOKEN)
allowed_ids = os.getenv("ALLOWED_CHANNEL_IDS", "")
allowed_channels = set(map(int, allowed_ids.split(","))) if allowed_ids.strip() else set()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready(): 
    logging.info("Logged in to Discord as %s", client.user)
    logging.info("Allowed channels: %s", allowed_channels)
 
@client.event
async def on_message(message):
    if message.author.bot:
        return
    if message.channel.id not in allowed_channels:
        return
    
    # Ignore thread creation messages
    if message.type == discord.MessageType.thread_starter_message:
        logging.info("Ignoring thread creation message")
        return
    
    content = message.content or ""
    media = []
    documents = []

    for i, att in enumerate(message.attachments):
        url = att.url
        filename = att.filename
        has_spoiler = filename.startswith("SPOILER_")
        
        if att.content_type and "image" in att.content_type:
            media.append(InputMediaPhoto(media=url, caption=content if i == 0 else None, has_spoiler=has_spoiler))
        elif att.content_type and "video" in att.content_type:
            media.append(InputMediaVideo(media=url, caption=content if i == 0 else None, has_spoiler=has_spoiler))
        else:
            documents.append((url, filename))
    try:
        if media:
            await tg_bot.send_media_group(chat_id=str(TG_CHAT_ID), media=media)
        elif content:
            await tg_bot.send_message(chat_id=str(TG_CHAT_ID), text=content)
        
        for url, filename in documents:
            await tg_bot.send_document(chat_id=str(TG_CHAT_ID), document=url, filename=filename)
        
    except Exception as e:
        print(f"TG error: {e}")

client.run(DISCORD_BOT_TOKEN)