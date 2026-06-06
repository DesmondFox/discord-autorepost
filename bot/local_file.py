from dataclasses import dataclass


@dataclass(frozen=True)
class LocalFile:
    path: str
    filename: str
    content_type: str | None = None
    has_spoiler: bool = False
