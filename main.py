import logging
import sys

import discord
from telegram import Bot

from bot.config import ConfigError, load_config
from bot.repost_service import RepostService
from bot.telegram_sender import TelegramSender


def create_discord_client() -> discord.Client:
    intents = discord.Intents.default()
    intents.message_content = True
    return discord.Client(intents=intents)


def main() -> None:
    logging.basicConfig(level=logging.DEBUG)

    try:
        config = load_config()
    except ConfigError as error:
        logging.error("%s", error)
        sys.exit(1)

    client = create_discord_client()
    nsfw_telegram_sender = TelegramSender(
        bot=Bot(token=config.telegram_bot_token),
        chat_id=config.telegram_nsfw_chat_id,
    )
    sfw_telegram_sender = TelegramSender(
        bot=Bot(token=config.telegram_bot_token),
        chat_id=config.telegram_sfw_chat_id,
    )
    repost_service = RepostService(
        nsfw_sender=nsfw_telegram_sender,
        sfw_sender=sfw_telegram_sender,
        nsfw_channel_ids=config.discord_nsfw_channel_ids,
        sfw_channel_ids=config.discord_sfw_channel_ids,
        temp_dir=config.temp_dir,
    )

    @client.event
    async def on_ready() -> None:
        logging.info("Logged in to Discord as %s", client.user)
        logging.info("NSFW Discord channels: %s", config.discord_nsfw_channel_ids)
        logging.info("SFW Discord channels: %s", config.discord_sfw_channel_ids)

    @client.event
    async def on_message(message: discord.Message) -> None:
        await repost_service.handle_message(message)

    client.run(config.discord_bot_token)


if __name__ == "__main__":
    main()
