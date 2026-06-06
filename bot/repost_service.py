import logging
import os

import discord
from telegram import InputMediaAnimation, InputMediaPhoto, InputMediaVideo

from .attachment_downloader import download_attachments_to_temp_dir, remove_downloaded_files
from .local_file import LocalFile
from .media_classifier import TelegramFileKind, classify_file
from .telegram_sender import TelegramSender


logger = logging.getLogger(__name__)


class RepostService:
    def __init__(
        self,
        nsfw_sender: TelegramSender,
        sfw_sender: TelegramSender,
        nsfw_channel_ids: set[int],
        sfw_channel_ids: set[int],
        temp_dir: str,
    ):
        self.nsfw_sender = nsfw_sender
        self.sfw_sender = sfw_sender
        self.nsfw_channel_ids = nsfw_channel_ids
        self.sfw_channel_ids = sfw_channel_ids
        self.temp_dir = temp_dir

    async def handle_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        channel_id = message.channel.id
        message_id = getattr(message, "id", "unknown")
        author_id = getattr(message.author, "id", "unknown")
        attachment_count = len(message.attachments)

        target_senders = self._target_senders_for_channel(channel_id)
        if not target_senders:
            return

        if message.type == discord.MessageType.thread_starter_message:
            logger.info("Ignoring thread creation message id=%s channel_id=%s", message_id, channel_id)
            return

        logger.info(
            "Handling Discord message id=%s channel_id=%s author_id=%s attachments=%d targets=%d",
            message_id,
            channel_id,
            author_id,
            attachment_count,
            len(target_senders),
        )

        content = message.content or ""
        if not message.attachments:
            for sender in target_senders:
                await sender.send_text(content)
            return

        local_files = await download_attachments_to_temp_dir(message.attachments, self.temp_dir)
        if not local_files and message.attachments:
            for sender in target_senders:
                await sender.send_attachment_urls(message.attachments, content)
            return

        try:
            for sender in target_senders:
                media, documents, file_objects = self._prepare_files(local_files, content)
                await sender.send_media_and_documents(media, documents, content, file_objects)
        finally:
            await remove_downloaded_files(local_files, self.temp_dir)

    def _target_senders_for_channel(self, channel_id: int) -> list[TelegramSender]:
        target_senders = []

        if channel_id in self.nsfw_channel_ids:
            target_senders.append(self.nsfw_sender)

        if channel_id in self.sfw_channel_ids:
            target_senders.extend([self.nsfw_sender, self.sfw_sender])

        return self._unique_senders(target_senders)

    def _unique_senders(self, senders: list[TelegramSender]) -> list[TelegramSender]:
        unique_senders = []
        seen_ids = set()

        for sender in senders:
            sender_id = id(sender)
            if sender_id in seen_ids:
                continue

            seen_ids.add(sender_id)
            unique_senders.append(sender)

        return unique_senders

    def _prepare_files(self, local_files: list[LocalFile], content: str) -> tuple[list, list[tuple], list]:
        media = []
        documents = []
        file_objects = []

        for index, local_file in enumerate(local_files):
            logger.info(
                "Processing file %d: %s (content_type: %s, has_spoiler: %s)",
                index + 1,
                local_file.filename,
                local_file.content_type,
                local_file.has_spoiler,
            )

            if not os.path.exists(local_file.path):
                logger.error("File not found: %s", local_file.path)
                continue

            file_size = os.path.getsize(local_file.path)
            logger.info("File size: %d bytes", file_size)
            classification = classify_file(local_file.filename, local_file.content_type, file_size)

            if classification.kind == TelegramFileKind.SKIP:
                logger.error("%s: %s", classification.reason, local_file.filename)
                continue

            file_object = open(local_file.path, "rb")
            file_objects.append(file_object)
            caption = content if index == 0 else None

            if classification.kind == TelegramFileKind.ANIMATION:
                logger.info("Adding as animation: %s", local_file.filename)
                media.append(
                    InputMediaAnimation(
                        media=file_object,
                        caption=caption,
                        has_spoiler=local_file.has_spoiler,
                    )
                )
            elif classification.kind == TelegramFileKind.PHOTO:
                logger.info("Adding as photo: %s", local_file.filename)
                media.append(
                    InputMediaPhoto(
                        media=file_object,
                        caption=caption,
                        has_spoiler=local_file.has_spoiler,
                    )
                )
            elif classification.kind == TelegramFileKind.VIDEO:
                logger.info("Adding as video: %s", local_file.filename)
                media.append(
                    InputMediaVideo(
                        media=file_object,
                        caption=caption,
                        has_spoiler=local_file.has_spoiler,
                    )
                )
            else:
                if classification.reason:
                    logger.warning("%s: %s", classification.reason, local_file.filename)
                logger.info("Adding as document: %s", local_file.filename)
                documents.append((file_object, local_file.filename))

        return media, documents, file_objects
