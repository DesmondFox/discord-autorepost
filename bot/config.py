import os
from dataclasses import dataclass
from typing import Mapping

import dotenv


TEMP_DIR = "temp"
DEFAULT_LOG_LEVEL = "INFO"


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class BotConfig:
    telegram_bot_token: str
    telegram_nsfw_chat_id: str
    telegram_sfw_chat_id: str
    discord_bot_token: str
    discord_nsfw_channel_ids: set[int]
    discord_sfw_channel_ids: set[int]
    temp_dir: str = TEMP_DIR
    log_level: str = DEFAULT_LOG_LEVEL


def parse_allowed_channel_ids(raw_value: str | None) -> set[int]:
    if not raw_value or not raw_value.strip():
        return set()

    return {int(channel_id.strip()) for channel_id in raw_value.split(",")}


def require_env(env: Mapping[str, str | None], key: str) -> str:
    value = env.get(key)
    if not value:
        raise ConfigError(f"{key} environment variable is required")
    return value


def parse_log_level(raw_value: str | None) -> str:
    if not raw_value or not raw_value.strip():
        return DEFAULT_LOG_LEVEL

    log_level = raw_value.strip().upper()
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if log_level not in valid_levels:
        raise ConfigError(f"LOG_LEVEL must be one of: {', '.join(sorted(valid_levels))}")

    return log_level


def load_config(env: Mapping[str, str | None] | None = None) -> BotConfig:
    dotenv.load_dotenv()
    source = env if env is not None else os.environ

    return BotConfig(
        telegram_bot_token=require_env(source, "TELEGRAM_BOT_TOKEN"),
        telegram_nsfw_chat_id=require_env(source, "TELEGRAM_NSFW_CHAT_ID"),
        telegram_sfw_chat_id=require_env(source, "TELEGRAM_SFW_CHAT_ID"),
        discord_bot_token=require_env(source, "DISCORD_BOT_TOKEN"),
        discord_nsfw_channel_ids=parse_allowed_channel_ids(source.get("DISCORD_NSFW_CHANNEL_IDS")),
        discord_sfw_channel_ids=parse_allowed_channel_ids(source.get("DISCORD_SFW_CHANNEL_IDS")),
        log_level=parse_log_level(source.get("LOG_LEVEL")),
    )
