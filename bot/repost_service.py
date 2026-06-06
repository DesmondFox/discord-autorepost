import logging
import os

import discord
from telegram import InputMediaAnimation, InputMediaPhoto, InputMediaVideo

from .attachment_downloader import download_attachments_to_temp_dir, remove_downloaded_files
from .local_file import LocalFile
from .media_classifier import TelegramFileKind, classify_file
from .telegram_sender import TelegramSender


class RepostService:
    def __init__(
        self,
        telegram_sender: TelegramSender,
        allowed_channel_ids: set[int],
        temp_dir: str,
    ):
        self.telegram_sender = telegram_sender
        self.allowed_channel_ids = allowed_channel_ids
        self.temp_dir = temp_dir

    async def handle_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        if message.channel.id not in self.allowed_channel_ids:
            return

        if message.type == discord.MessageType.thread_starter_message:
            logging.info("Ignoring thread creation message")
            return

        content = message.content or ""
        if not message.attachments:
            await self.telegram_sender.send_text(content)
            return

        local_files = await download_attachments_to_temp_dir(message.attachments, self.temp_dir)
        if not local_files and message.attachments:
            await self.telegram_sender.send_attachment_urls(message.attachments, content)
            return

        media, documents, file_objects = self._prepare_files(local_files, content)
        await self.telegram_sender.send_media_and_documents(media, documents, content, file_objects)
        await remove_downloaded_files(local_files, self.temp_dir)

    def _prepare_files(self, local_files: list[LocalFile], content: str) -> tuple[list, list[tuple], list]:
        media = []
        documents = []
        file_objects = []

        for index, local_file in enumerate(local_files):
            logging.info(
                "Processing file %d: %s (content_type: %s, has_spoiler: %s)",
                index + 1,
                local_file.filename,
                local_file.content_type,
                local_file.has_spoiler,
            )

            if not os.path.exists(local_file.path):
                logging.error("File not found: %s", local_file.path)
                continue

            file_size = os.path.getsize(local_file.path)
            logging.info("File size: %d bytes", file_size)
            classification = classify_file(local_file.filename, local_file.content_type, file_size)

            if classification.kind == TelegramFileKind.SKIP:
                logging.error("%s: %s", classification.reason, local_file.filename)
                continue

            file_object = open(local_file.path, "rb")
            file_objects.append(file_object)
            caption = content if index == 0 else None

            if classification.kind == TelegramFileKind.ANIMATION:
                logging.info("Adding as animation: %s", local_file.filename)
                media.append(
                    InputMediaAnimation(
                        media=file_object,
                        caption=caption,
                        has_spoiler=local_file.has_spoiler,
                    )
                )
            elif classification.kind == TelegramFileKind.PHOTO:
                logging.info("Adding as photo: %s", local_file.filename)
                media.append(
                    InputMediaPhoto(
                        media=file_object,
                        caption=caption,
                        has_spoiler=local_file.has_spoiler,
                    )
                )
            elif classification.kind == TelegramFileKind.VIDEO:
                logging.info("Adding as video: %s", local_file.filename)
                media.append(
                    InputMediaVideo(
                        media=file_object,
                        caption=caption,
                        has_spoiler=local_file.has_spoiler,
                    )
                )
            else:
                if classification.reason:
                    logging.warning("%s: %s", classification.reason, local_file.filename)
                logging.info("Adding as document: %s", local_file.filename)
                documents.append((file_object, local_file.filename))

        return media, documents, file_objects
