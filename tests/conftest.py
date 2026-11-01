import os

# bot.py exits at import without a token; aiogram checks only its format.
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "123456:TEST")
