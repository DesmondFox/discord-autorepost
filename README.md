# Discord Repost Bot

A small Python bot that reposts messages from selected Discord channels to a Telegram chat.

The bot listens for new Discord messages, checks that the message came from an allowed channel, then forwards the text and attachments to Telegram. It supports photos, videos, GIF/WebM animations, and other files as Telegram documents.

## Features

- Reposts Discord text messages to Telegram.
- Reposts Discord attachments to Telegram.
- Sends images as Telegram photos.
- Sends videos as Telegram videos.
- Sends GIF and WebM files as Telegram animations.
- Sends unsupported or large image files as Telegram documents.
- Preserves Discord spoiler attachments when the filename starts with `SPOILER_`.
- Restricts reposting to configured Discord channel IDs.
- Cleans downloaded temporary files after sending.
- Can run locally with Python or in Docker Compose.

## Project Structure

```text
.
+-- main.py              # Bot entrypoint
+-- bot/                 # Application code
|   +-- config.py        # Environment loading and validation
|   +-- repost_service.py
|   +-- attachment_downloader.py
|   +-- telegram_sender.py
|   +-- media_classifier.py
|   `-- local_file.py
+-- tests/               # Unit tests for pure logic
+-- requirements.txt     # Python dependencies
+-- Dockerfile           # Container image definition
+-- docker-compose.yml   # Docker Compose service
`-- .env.example         # Example environment configuration
```

## How It Works

1. `main.py` loads configuration and starts the Discord client.
2. `bot/config.py` reads environment variables from `.env` and validates required values.
3. The Discord client starts with `message_content` intent enabled.
4. When a non-bot message arrives, `bot/repost_service.py` checks whether the Discord channel ID is in `ALLOWED_CHANNEL_IDS`.
5. If the message has no attachments, the bot sends the text to Telegram.
6. If the message has attachments, `bot/attachment_downloader.py` downloads them into the local `temp/` directory.
7. `bot/media_classifier.py` classifies each downloaded file by content type, extension, and size:
   - images become Telegram photos;
   - videos become Telegram videos;
   - `gif` and `webm` files become Telegram animations;
   - other files become Telegram documents.
8. Telegram size limits are checked before sending:
   - photos: 10 MB;
   - videos: 50 MB;
   - documents: 50 MB.
9. `bot/telegram_sender.py` sends the text, media, and documents to Telegram.
10. After sending, downloaded files are removed from `temp/`.

If an attachment cannot be downloaded, the bot tries to send the original Discord attachment URL directly to Telegram as a fallback.

## Requirements

- Python 3.11 or newer.
- A Discord bot token.
- A Telegram bot token.
- A Telegram chat ID.
- Discord Message Content Intent enabled for the bot in the Discord Developer Portal.

## Configuration

Create a `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Set these values:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
DISCORD_BOT_TOKEN=your_discord_bot_token
ALLOWED_CHANNEL_IDS=123456789012345678,987654321098765432
```

### Environment Variables

| Variable | Required | Description |
| --- | --- | --- |
| `TELEGRAM_BOT_TOKEN` | Yes | Token for the Telegram bot that sends messages. |
| `TELEGRAM_CHAT_ID` | Yes | Target Telegram chat, group, channel, or topic-compatible chat ID. |
| `DISCORD_BOT_TOKEN` | Yes | Token for the Discord bot that reads messages. |
| `ALLOWED_CHANNEL_IDS` | No | Comma-separated list of Discord channel IDs to repost from. If empty, no channels are reposted. |

Do not commit real `.env` files or tokens.

## Run Locally

Install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Start the bot:

```bash
python main.py
```

## Run with Docker Compose

Build and start:

```bash
docker compose up -d --build
```

View logs:

```bash
docker compose logs -f bot
```

Stop:

```bash
docker compose down
```

## Operational Notes

- The bot uses the local `temp/` directory for downloaded Discord attachments.
- File names are reused as downloaded. If Discord sends duplicate attachment names at the same time, later files may overwrite earlier files in `temp/`.
- Telegram media groups can contain at most 10 items. If more than 10 media files are found, the bot sends them one by one.
- Captions are attached to the first media item in a media group. Documents are sent separately and currently receive the same caption.
- Logging is set to `DEBUG` at startup.

## Troubleshooting

### The bot exits on startup

Check that all required variables are set in `.env`:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `DISCORD_BOT_TOKEN`

### Discord messages are not reposted

Check these points:

- The Discord bot is invited to the server.
- The bot has access to the target channel.
- Message Content Intent is enabled in the Discord Developer Portal.
- The channel ID is present in `ALLOWED_CHANNEL_IDS`.
- The message was not sent by another bot.

### Attachments are missing in Telegram

Check the logs for:

- failed Discord attachment downloads;
- files larger than Telegram limits;
- unsupported media types;
- Telegram API errors.

## Development

Run automated tests:

```bash
python -m pytest
```

Compile-check the project:

```bash
python -m compileall .
```

Before changing the repost logic, manually test:

- text-only Discord messages;
- one image;
- several images;
- GIF or WebM animation;
- video;
- non-media document;
- spoiler attachment;
- file above Telegram size limits.
