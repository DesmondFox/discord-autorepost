# AGENTS.md

## Language

- If the user asks in English, respond in Simplified English.
- If the user asks in another language, respond in that language unless they request otherwise.

## Project Summary

This repository contains a Python Discord-to-Telegram repost bot.

- `main.py` is the application entrypoint.
- `local_file.py` stores metadata for downloaded Discord attachments.
- The bot loads configuration from `.env` through `python-dotenv`.
- Attachments are downloaded to `temp/`, sent to Telegram, then removed.
- Docker support is provided through `Dockerfile` and `docker-compose.yml`.

## Important Runtime Configuration

Required environment variables:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `DISCORD_BOT_TOKEN`

Optional environment variable:

- `ALLOWED_CHANNEL_IDS` as a comma-separated list of Discord channel IDs.

Do not print, commit, or expose real values from `.env` or `.env2`.

## Common Commands

Install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

Run locally:

```powershell
python main.py
```

Run with Docker Compose:

```powershell
docker compose up -d --build
```

View Docker logs:

```powershell
docker compose logs -f bot
```

## Development Notes

- Prefer small, focused changes. This is a compact script-style project.
- Keep secrets out of documentation and logs.
- Preserve Discord spoiler support for filenames that start with `SPOILER_`.
- Preserve Telegram size checks unless intentionally changing file handling.
- `ALLOWED_CHANNEL_IDS` is parsed as integers. Invalid values will raise at startup.
- There is currently no automated test suite. For behavior changes, document manual test coverage in the final response.
