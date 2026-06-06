# Etagi Scraper Telegram Bot

Бот для поиска недвижимости на сайте etagi.com с расширенными фильтрами через Web App.

## Быстрый запуск

1.  Создайте файл `.env` на основе `.env.example` и укажите ваш `TELEGRAM_BOT_TOKEN`.
2.  Разместите папку `webapp` на хостинге с HTTPS (например, GitHub Pages) и укажите URL в `WEBAPP_URL` в `.env`.

### Запуск через Docker

```bash
docker build -t etagi-bot .
docker run --env-file .env etagi-bot
```

### Локальный запуск (через uv)

```bash
uv run src/bot.py
```

## Функционал
- **Web App Меню:** Полноценный интерфейс фильтров (Цена, Площадь, Год, Ремонт, Материал стен и др.).
- **Асинхронность:** Парсинг не блокирует работу бота.
- **Масштабируемость:** Бот готов к деплою в контейнере.
