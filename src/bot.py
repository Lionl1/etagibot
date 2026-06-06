import asyncio
import html
import json
import logging
import os
import sys
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import WebAppInfo, ReplyKeyboardMarkup, KeyboardButton
from scraper import EtagiScraper
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
WEBAPP_URL = os.getenv('WEBAPP_URL', 'https://your-github-pages-url.com/webapp/')

if not API_TOKEN:
    print("Error: TELEGRAM_BOT_TOKEN environment variable is not set.")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
scraper = EtagiScraper()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # IMPORTANT: Use ReplyKeyboardMarkup for sendData to work
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏢 Настроить фильтры", web_app=WebAppInfo(url=WEBAPP_URL))]
        ],
        resize_keyboard=True
    )
    await message.answer(
        "👋 Добро пожаловать! Я бот для поиска недвижимости на Этажах.\n\n"
        "Нажмите на кнопку ниже, чтобы открыть фильтры и начать поиск.",
        reply_markup=kb
    )

@dp.message(F.web_app_data)
async def handle_web_app_data(message: types.Message):
    try:
        raw_data = message.web_app_data.data
        logging.info(f"RECEIVED WEB_APP_DATA: {raw_data}")
        data = json.loads(raw_data)
        
        # Mapping WebApp city IDs to names
        cities = {"1": "Тюмень", "23": "Екатеринбург", "42": "Москва", "98": "Санкт-Петербург", "15": "Сургут"}
        city_name = cities.get(str(data.get('city_id')), "Тюмень")
        
        # Clean up data for display
        display_data = {k: v for k, v in data.items() if v}
        
        escaped_city = html.escape(city_name)
        escaped_params = html.escape(json.dumps(display_data, ensure_ascii=False))
        await message.answer(
            f"🔎 <b>Ищем квартиры:</b> {escaped_city}\n"
            f"📊 <b>Параметры:</b> <code>{escaped_params}</code>",
            parse_mode="HTML"
        )
        
        results = await scraper.scrape(data, max_pages=3)
        logging.info(f"SCRAPER RESULT: {results}")
        
        if results == "BLOCKED":
            await message.answer("⚠️ Сайт временно ограничил доступ (защита от ботов). Пожалуйста, подождите пару минут и попробуйте снова.")
            return
            
        if not results:
            await message.answer("❌ Ничего не найдено по вашим параметрам. Попробуйте смягчить фильтры.")
            return

        text = f"🏠 <b>Найдено вариантов:</b> {len(results)}\n\n"
        for i, res in enumerate(results[:15], 1):
            price = str(res['Price']).replace(' ', '')
            addr = html.escape(res['Address'])
            link = html.escape(res['Link'])
            
            try:
                formatted_price = "{:,}".format(int(price)).replace(',', ' ')
            except:
                formatted_price = html.escape(price)

            rooms = html.escape(str(res['Rooms']))
            area = html.escape(str(res['Area']))
            floor = html.escape(str(res['Floor']))

            line = f"{i}. <b>{formatted_price} ₽</b> | {rooms}к | {area}м² | {floor}эт.\n"
            line += f"📍 {addr}\n"
            if res['Year'] != 'N/A' and res['Year'] != 0:
                year = html.escape(str(res['Year']))
                line += f"🏗 Год: {year}\n"
            line += f"🔗 <a href=\"{link}\">Открыть на Этажах</a>\n\n"
            
            if len(text + line) > 4000:
                await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)
                text = ""
            text += line
            
        if text:
            await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)
            
        if len(results) > 15:
            await message.answer(f"Показано первые 15 из {len(results)} найденных объявлений.")

    except Exception as e:
        logging.error(f"Error handling web app data: {e}")
        await message.answer(f"⚠️ Ошибка: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
