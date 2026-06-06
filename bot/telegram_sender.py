import logging

from telegram import Bot, InputMediaAnimation, InputMediaPhoto, InputMediaVideo


class TelegramSender:
    def __init__(self, bot: Bot, chat_id: str):
        self.bot = bot
        self.chat_id = str(chat_id)

    async def send_text(self, content: str) -> None:
        logging.info("Sending text message")
        await self.bot.send_message(chat_id=self.chat_id, text=content)
        logging.info("Successfully sent text message")

    async def send_media_and_documents(
        self,
        media: list,
        documents: list[tuple],
        content: str,
        file_objects: list,
    ) -> None:
        try:
            logging.info(
                "Preparing to send %d media files and %d documents to Telegram",
                len(media),
                len(documents),
            )

            if media:
                if len(media) == 1:
                    await self._send_single_media(media[0], content)
                else:
                    await self._send_media_group(media, content)
            elif content:
                await self.send_text(content)

            for file_obj, filename in documents:
                logging.info("Sending document: %s", filename)
                await self.bot.send_document(
                    chat_id=self.chat_id,
                    document=file_obj,
                    filename=filename,
                    caption=content,
                )
                logging.info("Successfully sent document: %s", filename)
        except Exception as error:
            logging.error("Sending to Telegram failed: %s", error)
            logging.error("Exception details:", exc_info=True)
        finally:
            try:
                for file_obj in file_objects:
                    file_obj.close()
            except Exception as error:
                logging.error("Closing files failed: %s", error)

    async def send_attachment_urls(self, attachments, content: str) -> None:
        logging.warning("No files downloaded successfully, attempting to send URLs directly")
        for index, attachment in enumerate(attachments):
            try:
                current_caption = content if index == 0 else None

                if attachment.content_type and "image" in attachment.content_type:
                    await self.bot.send_photo(
                        chat_id=self.chat_id,
                        photo=attachment.url,
                        caption=current_caption,
                    )
                elif attachment.content_type and "video" in attachment.content_type:
                    await self.bot.send_video(
                        chat_id=self.chat_id,
                        video=attachment.url,
                        caption=current_caption,
                    )
                else:
                    await self.bot.send_document(
                        chat_id=self.chat_id,
                        document=attachment.url,
                        filename=attachment.filename,
                        caption=current_caption,
                    )
                logging.info("Successfully sent URL directly: %s", attachment.filename)
            except Exception as error:
                logging.error("Failed to send URL directly for %s: %s", attachment.filename, error)
                logging.error("Exception details:", exc_info=True)

    async def _send_single_media(self, media_item, content: str | None) -> None:
        logging.info("Sending single media file of type: %s", type(media_item).__name__)

        if isinstance(media_item, InputMediaAnimation):
            await self.bot.send_animation(
                chat_id=self.chat_id,
                animation=media_item.media,
                caption=content,
                has_spoiler=media_item.has_spoiler,
            )
        elif isinstance(media_item, InputMediaPhoto):
            await self.bot.send_photo(
                chat_id=self.chat_id,
                photo=media_item.media,
                caption=content,
                has_spoiler=media_item.has_spoiler,
            )
        elif isinstance(media_item, InputMediaVideo):
            await self.bot.send_video(
                chat_id=self.chat_id,
                video=media_item.media,
                caption=content,
                has_spoiler=media_item.has_spoiler,
            )
        else:
            await self.bot.send_document(
                chat_id=self.chat_id,
                document=media_item.media,
                filename=getattr(media_item, "filename", "document"),
                caption=content,
            )

        logging.info("Successfully sent single media file")

    async def _send_media_group(self, media: list, content: str) -> None:
        logging.info("Sending media group with %d files", len(media))

        if len(media) > 10:
            logging.error("Too many media files for media group (max 10): %d", len(media))
            for index, single_media in enumerate(media):
                try:
                    current_caption = content if index == 0 else None
                    await self._send_single_media(single_media, current_caption)
                    logging.info("Successfully sent individual media file %d/%d", index + 1, len(media))
                except Exception as error:
                    logging.error("Failed to send individual media file %d: %s", index + 1, error)
        else:
            await self.bot.send_media_group(chat_id=self.chat_id, media=media)
            logging.info("Successfully sent media group")
