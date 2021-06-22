import asyncio
import os
from random import choice

import aioschedule
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from func import get_compliments
from utils import emoji_check

API_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


async def start_complimenting(message: types.Message, days: list):
    """
    Function for scheduling compliments.
    """

    async def task():
        compliments = get_compliments()
        compliment_topics = list(compliments.keys())
        choosen_topic = choice(compliment_topics)
        choosen_compliment = choice(compliments[choosen_topic])

        await message.answer(f"*{choosen_topic}*\n{choosen_compliment}")

    day_schedulers = [
        aioschedule.every().monday,
        aioschedule.every().tuesday,
        aioschedule.every().wednesday,
        aioschedule.every().thursday,
        aioschedule.every().friday,
        aioschedule.every().saturday,
        aioschedule.every().sunday,
    ]

    aioschedule.clear(message.chat.id)

    for idx, day in enumerate(day_schedulers):
        if days[idx]:
            day.at("22:50").do(task).tag(message.chat.id)

    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


@dp.message_handler(commands=["stop"])
async def stop_complimenting(message: types.Message):
    """
    Message handler for stoping making compliments. Called by /stop command
    """
    aioschedule.clear(message.chat.id)
    await message.reply("From now on I stop making compliments! I hope see you soon ^^")


@dp.message_handler(commands=["get"])
async def get_schedules(message: types.Message):
    """
    Message handler for getting all scheduled compliments by currend user. Called by /stop command
    """
    await message.reply("\n".join(map(str, aioschedule.jobs)))


@dp.message_handler(commands=["set_days"])
async def set_days(message: types.Message):
    markup = InlineKeyboardMarkup()
    buttons = [
        InlineKeyboardButton("Mon - ✅", callback_data="btn-0-1"),
        InlineKeyboardButton("Tue - ✅", callback_data="btn-1-1"),
        InlineKeyboardButton("Wed - ✅", callback_data="btn-2-1"),
        InlineKeyboardButton("Thu - ✅", callback_data="btn-3-1"),
        InlineKeyboardButton("Fri - ✅", callback_data="btn-4-1"),
        InlineKeyboardButton("Sat - ✅", callback_data="btn-5-1"),
        InlineKeyboardButton("Sun - ✅", callback_data="btn-6-1"),
        InlineKeyboardButton("Submit", callback_data="btn-submit"),
    ]

    for btn in buttons:
        markup.row(btn)

    text = "Choose compliment days:"

    await message.reply(text, reply_markup=markup)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith("btn"))
async def btn_callback_handler(callback_query: types.CallbackQuery):
    cb_data = callback_query.data

    if cb_data.split("-")[1] == "submit":
        markup = callback_query.message.reply_markup
        btn_data = [
            btn[0].text.split(" - ")[1] == "✅" for btn in markup.inline_keyboard[:-1]
        ]

        await bot.answer_callback_query(callback_query.id, "Submitted!")
        await start_complimenting(callback_query.message, btn_data)
        return

    button_code = int(cb_data.split("-")[1])
    button_value = int(cb_data.split("-")[2])

    markup = callback_query.message.reply_markup
    btn = markup.inline_keyboard[button_code][0]
    btn.text = f"{btn.text.split(' - ')[0]} - {emoji_check(not button_value)}"
    btn.callback_data = f"btn-{button_code}-{int(not button_value)}"

    await callback_query.message.edit_reply_markup(markup)
    await bot.answer_callback_query(callback_query.id)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
