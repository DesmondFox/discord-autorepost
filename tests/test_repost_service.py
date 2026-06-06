import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from bot.repost_service import RepostService


def make_message(channel_id: int, *, author_is_bot: bool = False):
    return SimpleNamespace(
        author=SimpleNamespace(bot=author_is_bot),
        channel=SimpleNamespace(id=channel_id),
        type=None,
        content="hello",
        attachments=[],
    )


def make_service(nsfw_sender, sfw_sender) -> RepostService:
    return RepostService(
        nsfw_sender=nsfw_sender,
        sfw_sender=sfw_sender,
        nsfw_channel_ids={123},
        sfw_channel_ids={456},
        temp_dir="temp",
    )


def test_nsfw_discord_message_sends_only_to_nsfw_telegram() -> None:
    nsfw_sender = SimpleNamespace(send_text=AsyncMock())
    sfw_sender = SimpleNamespace(send_text=AsyncMock())
    service = make_service(nsfw_sender, sfw_sender)

    asyncio.run(service.handle_message(make_message(123)))

    nsfw_sender.send_text.assert_awaited_once_with("hello")
    sfw_sender.send_text.assert_not_awaited()


def test_sfw_discord_message_sends_to_nsfw_and_sfw_telegram() -> None:
    nsfw_sender = SimpleNamespace(send_text=AsyncMock())
    sfw_sender = SimpleNamespace(send_text=AsyncMock())
    service = make_service(nsfw_sender, sfw_sender)

    asyncio.run(service.handle_message(make_message(456)))

    nsfw_sender.send_text.assert_awaited_once_with("hello")
    sfw_sender.send_text.assert_awaited_once_with("hello")


def test_unknown_discord_channel_is_ignored() -> None:
    nsfw_sender = SimpleNamespace(send_text=AsyncMock())
    sfw_sender = SimpleNamespace(send_text=AsyncMock())
    service = make_service(nsfw_sender, sfw_sender)

    asyncio.run(service.handle_message(make_message(789)))

    nsfw_sender.send_text.assert_not_awaited()
    sfw_sender.send_text.assert_not_awaited()


def test_bot_author_message_is_ignored() -> None:
    nsfw_sender = SimpleNamespace(send_text=AsyncMock())
    sfw_sender = SimpleNamespace(send_text=AsyncMock())
    service = make_service(nsfw_sender, sfw_sender)

    asyncio.run(service.handle_message(make_message(123, author_is_bot=True)))

    nsfw_sender.send_text.assert_not_awaited()
    sfw_sender.send_text.assert_not_awaited()
