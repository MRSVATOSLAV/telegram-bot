import requests
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# ====== ТОКЕНЫ ======
BOT_TOKEN = "8593046524:AAETkY_WZyxkpQv5HJqt6o_ukDoJW903UzQ"
WEATHER_TOKEN = "f0bb8f0c0c2caba92318e95c340df5f7"
# ====================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

subscribers = set()

# ====== КНОПКИ ======
menu = ReplyKeyboardMarkup(resize_keyboard=True)
menu.add(
    KeyboardButton("❄️ Дудинка"),
    KeyboardButton("🧊 Норильск"),
)
menu.add(
    KeyboardButton("📅 Актировка завтра")
)

# ====== ПОГОДА ======
def get_weather(city):
    url = (
        "https://api.openweathermap.org/data/2.5/weather"
        f"?q={city}&appid={WEATHER_TOKEN}&units=metric&lang=ru"
    )
    data = requests.get(url).json()

    temp = data["main"]["temp"]
    feels = data["main"]["feels_like"]
    humidity = data["main"]["humidity"]
    wind = data["wind"]["speed"]
    desc = data["weather"][0]["description"]

    warning = ""
    if wind >= 20:
        warning = "🚨 ОПАСНО! Ураганный ветер!"
    elif wind >= 15:
        warning = "⚠️ Внимание: сильный ветер"

    return temp, feels, humidity, wind, desc, warning

# ====== АКТИРОВКИ ======
def get_aktировка(feels, wind):
    bonus = 5 if wind >= 15 else 0
    result = []

    if feels <= -35 + bonus:
        result.append("❄️ 1–4 классы — не учатся")
    if feels <= -40 + bonus:
        result.append("❄️ 5–8 классы — не учатся")
    if feels <= -45 + bonus:
        result.append("❄️ 9–11 классы — не учатся")

    if not result:
        return "📚 Актировки нет — учёба по расписанию"

    return "📚 АКТИРОВКА:\n" + "\n".join(result)

# ====== СТАРТ ======
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    subscribers.add(message.chat.id)
    await message.answer(
        "❄️ Северный погодный бот\n\nВыбери город 👇",
        reply_markup=menu
    )

# ====== ГОРОДА ======
async def send_city_weather(message, city, title):
    temp, feels, hum, wind, desc, warn = get_weather(city)
    akt = get_aktировка(feels, wind)

    text = (
        f"{title}\n\n"
        f"🌡 Температура: {temp:.1f}°C\n"
        f"🥶 Ощущается: {feels:.1f}°C\n"
        f"💧 Влажность: {hum}%\n"
        f"🌬 Ветер: {wind} м/с\n"
        f"☁️ {desc.capitalize()}\n\n"
        f"{akt}"
    )

    if warn:
        text += f"\n\n{warn}"

    if "не учатся" in akt:
        text = "🚨 АКТИРОВКА ОБЪЯВЛЕНА!\n\n" + text

    await message.answer(text)

@dp.message_handler(lambda m: m.text == "❄️ Дудинка")
async def dudinka(message: types.Message):
    await send_city_weather(message, "Dudinka", "❄️ Дудинка 🧊")

@dp.message_handler(lambda m: m.text == "🧊 Норильск")
async def norilsk(message: types.Message):
    await send_city_weather(message, "Norilsk", "🧊 Норильск ❄️")

# ====== АКТИРОВКА НА ЗАВТРА ======
@dp.message_handler(lambda m: m.text == "📅 Актировка завтра")
async def tomorrow(message: types.Message):
    url = (
        "https://api.openweathermap.org/data/2.5/forecast"
        f"?q=Norilsk&appid={WEATHER_TOKEN}&units=metric&lang=ru"
    )
    data = requests.get(url).json()
    tomorrow_data = data["list"][8]

    feels = tomorrow_data["main"]["feels_like"]
    wind = tomorrow_data["wind"]["speed"]

    akt = get_aktировка(feels, wind)

    await message.answer(
        "📅 Актировка на завтра:\n\n"
        f"🥶 Ощущается: {feels:.1f}°C\n"
        f"🌬 Ветер: {wind} м/с\n\n"
        f"{akt}"
    )

# ====== УТРЕННЯЯ РАССЫЛКА ======
async def morning_loop():
    while True:
        now = datetime.now()
        if now.hour == 8 and now.minute == 0:
            for chat_id in subscribers:
                try:
                    temp, feels, hum, wind, desc, warn = get_weather("Norilsk")
                    akt = get_aktировка(feels, wind)

                    text = (
                        "🌅 Доброе утро!\n\n"
                        f"🌡 {temp:.1f}°C (ощущается {feels:.1f}°C)\n"
                        f"🌬 Ветер: {wind} м/с\n\n"
                        f"{akt}"
                    )

                    if "не учатся" in akt:
                        text = "🚨 АКТИРОВКА ОБЪЯВЛЕНА!\n\n" + text

                    await bot.send_message(chat_id, text)
                except:
                    pass
            await asyncio.sleep(60)
        await asyncio.sleep(20)

async def on_startup(dp):
    asyncio.create_task(morning_loop())

# ====== ЗАПУСК ======
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
