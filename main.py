import sys
import os
import logging
import aiohttp
from telegram import Bot, InputMediaAnimation, InputMediaPhoto, InputMediaVideo
import discord
import dotenv

from local_file import LocalFile

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
    logging.info("Downloading %d attachments to temp directory: %s/", len(attachments), TEMP_DIR)
    os.makedirs(TEMP_DIR, exist_ok=True)
    local_files = []
    for i, attachment in enumerate(attachments):
        try:
            logging.info("Downloading attachment %d/%d: %s (size: %d bytes, content_type: %s)", 
                         i+1, len(attachments), attachment.filename, attachment.size, attachment.content_type)
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.get(attachment.url) as response:
                    if response.status != 200:
                        logging.error("Failed to download attachment %s: HTTP %d", attachment.filename, response.status)
                        continue
                        
                    content = await response.read()
                    file_path = os.path.join(TEMP_DIR, attachment.filename)
                    with open(file_path, "wb") as f:
                        f.write(content)
                        
                    # Verify file was written correctly
                    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                        logging.error("Failed to save attachment %s: file is empty or doesn't exist", attachment.filename)
                        continue
                        
                has_spoiler = attachment.filename.startswith("SPOILER_")
                filename = attachment.filename
                local_files.append(
                    LocalFile(os.path.join(TEMP_DIR, filename), 
                              has_spoiler=has_spoiler,
                              filename=filename,
                              content_type=attachment.content_type))
            logging.info("Successfully downloaded attachment %s (%d bytes)", 
                         attachment.filename, os.path.getsize(os.path.join(TEMP_DIR, attachment.filename)))
        except Exception as e:
            logging.error("Error downloading attachment %s: %s", attachment.filename, e)
            logging.error("Exception details:", exc_info=True)
            continue
        
    logging.info("Successfully downloaded %d/%d attachments", len(local_files), len(attachments))
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

async def send_media_to_telegram(media: list, documents: list, content: str, file_objects: list):
    """
    Sends media files and documents to Telegram.
    
    Args:
        media: List of InputMedia objects (photos, videos, animations)
        documents: List of tuples (file_object, filename)
        content: Text content to send as caption
        file_objects: List of opened file objects for cleanup
    """
    try:
        logging.info("Preparing to send %d media files and %d documents to Telegram", len(media), len(documents))
        
        if media:
            if len(media) == 1:
                await _send_single_media(media[0], content)
            else:
                await _send_media_group(media, content)
        elif content:
            logging.info("Sending text message")
            await tg_bot.send_message(chat_id=str(TG_CHAT_ID), text=content)
            logging.info("Successfully sent text message")
        
        for file_obj, filename in documents:
            logging.info("Sending document: %s", filename)
            await tg_bot.send_document(chat_id=str(TG_CHAT_ID), document=file_obj, filename=filename, caption=content)
            logging.info("Successfully sent document: %s", filename)
        
    except Exception as e:
        logging.error("Sending to Telegram failed: %s", e)
        logging.error("Exception details:", exc_info=True)
    finally:
        try:
            for file_obj in file_objects:
                file_obj.close()
        except Exception as e:
            logging.error("Closing files failed: %s", e)

async def _send_single_media(media_item, content: str):
    """Helper function to send a single media item."""
    logging.info("Sending single media file of type: %s", type(media_item).__name__)
    
    if isinstance(media_item, InputMediaAnimation):
        await tg_bot.send_animation(
            chat_id=str(TG_CHAT_ID), 
            animation=media_item.media, 
            caption=content, 
            has_spoiler=media_item.has_spoiler
        )
    elif isinstance(media_item, InputMediaPhoto):
        await tg_bot.send_photo(
            chat_id=str(TG_CHAT_ID), 
            photo=media_item.media, 
            caption=content, 
            has_spoiler=media_item.has_spoiler
        )
    elif isinstance(media_item, InputMediaVideo):
        await tg_bot.send_video(
            chat_id=str(TG_CHAT_ID), 
            video=media_item.media, 
            caption=content, 
            has_spoiler=media_item.has_spoiler
        )
    else:
        await tg_bot.send_document(
            chat_id=str(TG_CHAT_ID), 
            document=media_item.media, 
            filename=getattr(media_item, 'filename', 'document'), 
            caption=content
        )
    
    logging.info("Successfully sent single media file")

async def _send_media_group(media: list, content: str):
    """Helper function to send media group or individual files if group is too large."""
    logging.info("Sending media group with %d files", len(media))
    
    if len(media) > 10:
        logging.error("Too many media files for media group (max 10): %d", len(media))
        # Send files individually instead
        for j, single_media in enumerate(media):
            try:
                current_caption = content if j == 0 else None
                await _send_single_media(single_media, current_caption)
                logging.info("Successfully sent individual media file %d/%d", j+1, len(media))
            except Exception as e:
                logging.error("Failed to send individual media file %d: %s", j+1, e)
    else:
        await tg_bot.send_media_group(chat_id=str(TG_CHAT_ID), media=media)
        logging.info("Successfully sent media group")

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
    
    # If no files were downloaded successfully, try to send URLs directly as fallback
    if not local_files and message.attachments:
        logging.warning("No files downloaded successfully, attempting to send URLs directly")
        for i, attachment in enumerate(message.attachments):
            try:
                # Only add caption to the first attachment to avoid repetition
                current_caption = content if i == 0 else None
                
                if attachment.content_type and "image" in attachment.content_type:
                    await tg_bot.send_photo(chat_id=str(TG_CHAT_ID), photo=attachment.url, caption=current_caption)
                elif attachment.content_type and "video" in attachment.content_type:
                    await tg_bot.send_video(chat_id=str(TG_CHAT_ID), video=attachment.url, caption=current_caption)
                else:
                    await tg_bot.send_document(chat_id=str(TG_CHAT_ID), document=attachment.url, filename=attachment.filename, caption=current_caption)
                logging.info("Successfully sent URL directly: %s", attachment.filename)
            except Exception as e:
                logging.error("Failed to send URL directly for %s: %s", attachment.filename, e)
                logging.error("Exception details:", exc_info=True)
        return
    
    file_objects = []

    for i, local_file_obj in enumerate(local_files):
        has_spoiler = local_file_obj.get_has_spoiler()
        filename = local_file_obj.get_filename()
        path = local_file_obj.get_path()
        content_type = local_file_obj.get_content_type()
        ext = filename.split(".")[-1].lower()
        
        logging.info("Processing file %d: %s (content_type: %s, ext: %s, has_spoiler: %s)", 
                     i+1, filename, content_type, ext, has_spoiler)
        
        # Check if file exists and get its size
        if not os.path.exists(path):
            logging.error("File not found: %s", path)
            continue
            
        file_size = os.path.getsize(path)
        logging.info("File size: %d bytes", file_size)
        
        # Telegram limits: photos 10MB, videos 50MB, documents 50MB
        if content_type and "image" in content_type and file_size > 10 * 1024 * 1024:
            logging.warning("Image file too large for Telegram photo (>10MB): %s", filename)
            # Send as document instead
            file_object = open(path, "rb")
            file_objects.append(file_object)
            documents.append((file_object, filename))
            continue
        elif content_type and "video" in content_type and file_size > 50 * 1024 * 1024:
            logging.error("Video file too large for Telegram (>50MB): %s", filename)
            continue
        elif file_size > 50 * 1024 * 1024:
            logging.error("File too large for Telegram (>50MB): %s", filename)
            continue
        
        file_object = open(path, "rb")
        file_objects.append(file_object)
        
        if ext in ["gif", "webm"]:
            logging.info("Adding as animation: %s", filename)
            media.append(InputMediaAnimation(media=file_object, caption=content if i == 0 else None, has_spoiler=has_spoiler))
        elif content_type and "image" in content_type:
            logging.info("Adding as photo: %s", filename)
            media.append(InputMediaPhoto(media=file_object, caption=content if i == 0 else None, has_spoiler=has_spoiler))
        elif content_type and "video" in content_type:
            logging.info("Adding as video: %s", filename)
            media.append(InputMediaVideo(media=file_object, caption=content if i == 0 else None, has_spoiler=has_spoiler))
        else:
            logging.info("Adding as document: %s", filename)
            documents.append((file_object, filename))       
            
    # Send to Telegram using the dedicated method
    await send_media_to_telegram(media, documents, content, file_objects)
    
    # Clean up downloaded files
    await remove_downloaded_files(local_files)

client.run(DISCORD_BOT_TOKEN)