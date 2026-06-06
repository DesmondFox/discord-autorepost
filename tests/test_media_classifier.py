from bot.media_classifier import (
    TELEGRAM_FILE_LIMIT_BYTES,
    TELEGRAM_PHOTO_LIMIT_BYTES,
    TelegramFileKind,
    classify_file,
    is_spoiler_filename,
)


def test_is_spoiler_filename() -> None:
    assert is_spoiler_filename("SPOILER_image.png")
    assert not is_spoiler_filename("image.png")


def test_classify_image_as_photo() -> None:
    result = classify_file("image.png", "image/png", TELEGRAM_PHOTO_LIMIT_BYTES)

    assert result.kind == TelegramFileKind.PHOTO


def test_classify_video_as_video() -> None:
    result = classify_file("clip.mp4", "video/mp4", TELEGRAM_FILE_LIMIT_BYTES)

    assert result.kind == TelegramFileKind.VIDEO


def test_classify_gif_as_animation() -> None:
    result = classify_file("loop.gif", "image/gif", TELEGRAM_PHOTO_LIMIT_BYTES)

    assert result.kind == TelegramFileKind.ANIMATION


def test_classify_webm_as_animation() -> None:
    result = classify_file("loop.webm", "video/webm", TELEGRAM_FILE_LIMIT_BYTES)

    assert result.kind == TelegramFileKind.ANIMATION


def test_classify_unknown_file_as_document() -> None:
    result = classify_file("archive.zip", "application/zip", TELEGRAM_FILE_LIMIT_BYTES)

    assert result.kind == TelegramFileKind.DOCUMENT


def test_classify_large_image_as_document() -> None:
    result = classify_file("large.png", "image/png", TELEGRAM_PHOTO_LIMIT_BYTES + 1)

    assert result.kind == TelegramFileKind.DOCUMENT


def test_classify_oversized_video_as_skip() -> None:
    result = classify_file("large.mp4", "video/mp4", TELEGRAM_FILE_LIMIT_BYTES + 1)

    assert result.kind == TelegramFileKind.SKIP


def test_classify_oversized_document_as_skip() -> None:
    result = classify_file("large.zip", "application/zip", TELEGRAM_FILE_LIMIT_BYTES + 1)

    assert result.kind == TelegramFileKind.SKIP
