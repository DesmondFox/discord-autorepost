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
            "TELEGRAM_CHAT_ID": "telegram-chat",
            "DISCORD_BOT_TOKEN": "discord-token",
            "ALLOWED_CHANNEL_IDS": "123,456",
        }
    )

    assert config.telegram_bot_token == "telegram-token"
    assert config.telegram_chat_id == "telegram-chat"
    assert config.discord_bot_token == "discord-token"
    assert config.allowed_channel_ids == {123, 456}
