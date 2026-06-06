import pytest

from bot.config import ConfigError, load_config, parse_allowed_channel_ids


def test_parse_allowed_channel_ids() -> None:
    assert parse_allowed_channel_ids("123,456") == {123, 456}


def test_parse_allowed_channel_ids_empty() -> None:
    assert parse_allowed_channel_ids("") == set()
    assert parse_allowed_channel_ids(None) == set()


def test_parse_allowed_channel_ids_invalid_value() -> None:
    with pytest.raises(ValueError):
        parse_allowed_channel_ids("123,not-a-channel")


def test_load_config_requires_tokens() -> None:
    with pytest.raises(ConfigError):
        load_config({})


def test_load_config() -> None:
    config = load_config(
        {
            "TELEGRAM_BOT_TOKEN": "telegram-token",
            "TELEGRAM_NSFW_CHAT_ID": "telegram-nsfw-chat",
            "TELEGRAM_SFW_CHAT_ID": "telegram-sfw-chat",
            "DISCORD_BOT_TOKEN": "discord-token",
            "DISCORD_NSFW_CHANNEL_IDS": "123",
            "DISCORD_SFW_CHANNEL_IDS": "456",
        }
    )

    assert config.telegram_bot_token == "telegram-token"
    assert config.telegram_nsfw_chat_id == "telegram-nsfw-chat"
    assert config.telegram_sfw_chat_id == "telegram-sfw-chat"
    assert config.discord_bot_token == "discord-token"
    assert config.discord_nsfw_channel_ids == {123}
    assert config.discord_sfw_channel_ids == {456}


def test_load_config_allows_empty_discord_channel_lists() -> None:
    config = load_config(
        {
            "TELEGRAM_BOT_TOKEN": "telegram-token",
            "TELEGRAM_NSFW_CHAT_ID": "telegram-nsfw-chat",
            "TELEGRAM_SFW_CHAT_ID": "telegram-sfw-chat",
            "DISCORD_BOT_TOKEN": "discord-token",
            "DISCORD_NSFW_CHANNEL_IDS": "",
            "DISCORD_SFW_CHANNEL_IDS": "",
        }
    )

    assert config.discord_nsfw_channel_ids == set()
    assert config.discord_sfw_channel_ids == set()


def test_load_config_rejects_invalid_discord_channel_id() -> None:
    with pytest.raises(ValueError):
        load_config(
            {
                "TELEGRAM_BOT_TOKEN": "telegram-token",
                "TELEGRAM_NSFW_CHAT_ID": "telegram-nsfw-chat",
                "TELEGRAM_SFW_CHAT_ID": "telegram-sfw-chat",
                "DISCORD_BOT_TOKEN": "discord-token",
                "DISCORD_NSFW_CHANNEL_IDS": "123",
                "DISCORD_SFW_CHANNEL_IDS": "not-a-channel",
            }
        )
