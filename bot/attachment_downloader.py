import logging
import os

import aiohttp

from .local_file import LocalFile
from .media_classifier import is_spoiler_filename


logger = logging.getLogger(__name__)


async def download_attachments_to_temp_dir(attachments, temp_dir: str) -> list[LocalFile]:
    logger.info("Downloading %d attachments to temp directory: %s/", len(attachments), temp_dir)
    os.makedirs(temp_dir, exist_ok=True)
    local_files: list[LocalFile] = []

    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for index, attachment in enumerate(attachments):
            try:
                logger.info(
                    "Downloading attachment %d/%d: %s (size: %d bytes, content_type: %s)",
                    index + 1,
                    len(attachments),
                    attachment.filename,
                    attachment.size,
                    attachment.content_type,
                )

                async with session.get(attachment.url) as response:
                    if response.status != 200:
                        logger.error(
                            "Failed to download attachment %s: HTTP %d",
                            attachment.filename,
                            response.status,
                        )
                        continue

                    content = await response.read()
                    file_path = os.path.join(temp_dir, attachment.filename)
                    with open(file_path, "wb") as file:
                        file.write(content)

                if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                    logger.error(
                        "Failed to save attachment %s: file is empty or doesn't exist",
                        attachment.filename,
                    )
                    continue

                local_files.append(
                    LocalFile(
                        path=file_path,
                        filename=attachment.filename,
                        content_type=attachment.content_type,
                        has_spoiler=is_spoiler_filename(attachment.filename),
                    )
                )
                logger.info(
                    "Successfully downloaded attachment %s (%d bytes)",
                    attachment.filename,
                    os.path.getsize(file_path),
                )
            except Exception as error:
                logger.exception("Error downloading attachment %s: %s", attachment.filename, error)

    logger.info("Successfully downloaded %d/%d attachments", len(local_files), len(attachments))
    return local_files


async def remove_downloaded_files(local_files: list[LocalFile], temp_dir: str) -> None:
    logger.info("Removing %d downloaded files from temp directory: %s/", len(local_files), temp_dir)
    removed_count = 0
    for local_file in local_files:
        try:
            os.remove(local_file.path)
            removed_count += 1
        except Exception as error:
            logger.error("Error removing downloaded file %s: %s", local_file.path, error)

    logger.info("Removed %d/%d downloaded files from temp directory: %s/", removed_count, len(local_files), temp_dir)
