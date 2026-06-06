from dataclasses import dataclass
from enum import Enum


MB = 1024 * 1024
TELEGRAM_PHOTO_LIMIT_BYTES = 10 * MB
TELEGRAM_FILE_LIMIT_BYTES = 50 * MB


class TelegramFileKind(str, Enum):
    ANIMATION = "animation"
    PHOTO = "photo"
    VIDEO = "video"
    DOCUMENT = "document"
    SKIP = "skip"


@dataclass(frozen=True)
class ClassifiedFile:
    kind: TelegramFileKind
    reason: str | None = None


def is_spoiler_filename(filename: str) -> bool:
    return filename.startswith("SPOILER_")


def classify_file(filename: str, content_type: str | None, file_size: int) -> ClassifiedFile:
    normalized_content_type = content_type or ""
    extension = filename.rsplit(".", maxsplit=1)[-1].lower() if "." in filename else ""

    if "image" in normalized_content_type and file_size > TELEGRAM_PHOTO_LIMIT_BYTES:
        if file_size <= TELEGRAM_FILE_LIMIT_BYTES:
            return ClassifiedFile(TelegramFileKind.DOCUMENT, "image too large for Telegram photo")
        return ClassifiedFile(TelegramFileKind.SKIP, "image too large for Telegram document")

    if "video" in normalized_content_type and file_size > TELEGRAM_FILE_LIMIT_BYTES:
        return ClassifiedFile(TelegramFileKind.SKIP, "video too large for Telegram")

    if file_size > TELEGRAM_FILE_LIMIT_BYTES:
        return ClassifiedFile(TelegramFileKind.SKIP, "file too large for Telegram")

    if extension in {"gif", "webm"}:
        return ClassifiedFile(TelegramFileKind.ANIMATION)

    if "image" in normalized_content_type:
        return ClassifiedFile(TelegramFileKind.PHOTO)

    if "video" in normalized_content_type:
        return ClassifiedFile(TelegramFileKind.VIDEO)

    return ClassifiedFile(TelegramFileKind.DOCUMENT)
