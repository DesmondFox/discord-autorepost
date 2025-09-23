from cgitb import text
import sys
import os
import logging
import aiohttp
from telegram import Bot, InputMediaAnimation, InputMediaPhoto, InputMediaVideo
import discord
import dotenv

from local_file import LocalFile
import local_file

dotenv.load_dotenv()
logging.basicConfig(level=logging.DEBUG)

# Get environment variables with proper error handling
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
TEMP_DIR = "temp"

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

async def download_attachments_to_temp_dir(attachments: list[discord.Attachment]) -> list[LocalFile]:
    """
    Downloads attachments to the temp directory and returns a list of LocalFile objects.
    """
    logging.info("Downloading attachments to temp directory: %s/", TEMP_DIR)
    os.makedirs(TEMP_DIR, exist_ok=True)
    local_files = []
    for attachment in attachments:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as response:
                    content = await response.read()
                    with open(os.path.join(TEMP_DIR, attachment.filename), "wb") as f:
                        f.write(content)
                has_spoiler = attachment.filename.startswith("SPOILER_")
                filename = attachment.filename
                local_files.append(
                    LocalFile(os.path.join(TEMP_DIR, filename), 
                              has_spoiler=has_spoiler,
                              filename=filename,
                              content_type=attachment.content_type))
            logging.info("Downloaded attachment %s to %s", 
                         attachment.filename, 
                         os.path.join(TEMP_DIR, attachment.filename))
        except Exception as e:
            logging.error("Error downloading attachment %s: %s", attachment.filename, e)
            continue
        
    return local_files

async def remove_downloaded_files(local_files: list[LocalFile]):
    """
    Removes downloaded files from the temp directory.
    """
    logging.info("Removing downloaded files from temp directory: %s/", TEMP_DIR)
    try:
        for f in local_files:
            os.remove(f.get_path())
    except Exception as e:
        logging.error("Error removing downloaded files: %s", e)
    logging.info("Removed downloaded files from temp directory: %s/", TEMP_DIR)

@client.event
async def on_ready() -> None: 
    logging.info("Logged in to Discord as %s", client.user)
    logging.info("Allowed channels: %s", allowed_channels)
 
@client.event
async def on_message(message: discord.Message) -> None:
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
    has_media = message.attachments
    if not has_media:
        caption = content
        await tg_bot.send_message(chat_id=str(TG_CHAT_ID), text=caption)
        
        return
    
    local_files = await download_attachments_to_temp_dir(message.attachments)
    file_objects = []

    for i, local_file in enumerate(local_files):
        has_spoiler = local_file.get_has_spoiler()
        filename = local_file.get_filename()
        path = local_file.get_path()
        content_type = local_file.get_content_type()
        ext = filename.split(".")[-1].lower()
        
        file_object = open(path, "rb")
        file_objects.append(file_object)
        if ext in ["gif", "webm"]:
            media.append(InputMediaAnimation(media=file_object, caption=content if i == 0 else None, has_spoiler=has_spoiler))
        elif content_type and "image" in content_type:
            media.append(InputMediaPhoto(media=file_object, caption=content if i == 0 else None, has_spoiler=has_spoiler))
        elif content_type and "video" in content_type:
            media.append(InputMediaVideo(media=file_object, caption=content if i == 0 else None, has_spoiler=has_spoiler))
        else:
            documents.append((file_object, filename))       
            
    try:
        if media:
            if len(media) == 1:
                one_media = media[0]
                if isinstance(one_media, InputMediaAnimation):
                    await tg_bot.send_animation(chat_id=str(TG_CHAT_ID), animation=one_media.media, caption=content, has_spoiler=has_spoiler)
                elif isinstance(one_media, InputMediaPhoto):
                    await tg_bot.send_photo(chat_id=str(TG_CHAT_ID), photo=one_media.media, caption=content, has_spoiler=has_spoiler)
                elif isinstance(one_media, InputMediaVideo):
                    await tg_bot.send_video(chat_id=str(TG_CHAT_ID), video=one_media.media, caption=content, has_spoiler=has_spoiler)
                else:
                    await tg_bot.send_document(chat_id=str(TG_CHAT_ID), document=one_media.media, filename=one_media.filename, caption=content)
            else:
                await tg_bot.send_media_group(chat_id=str(TG_CHAT_ID), media=media)
        elif content:
            await tg_bot.send_message(chat_id=str(TG_CHAT_ID), text=content)
        
        for url, filename in documents:
            await tg_bot.send_document(chat_id=str(TG_CHAT_ID), document=url, filename=filename, caption=content)
        
    except Exception as e:
        logging.error("Sending to Telegram failed: %s", e)
    finally:
        try:
            for file_obj in file_objects:
                file_obj.close()
        except Exception as e:
            logging.error("Closing files failed: %s", e)
        await remove_downloaded_files(local_files)

client.run(DISCORD_BOT_TOKEN)