import asyncio
import os
from random import choice

import aioschedule
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.storage import FSMContext
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, ReplyKeyboardMarkup)

from func import get_compliments
from utils import check_mark, validate_time

API_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())


class SetupStates(StatesGroup):
    days = State()
    time = State()


@dp.message_handler(commands=["start"])
async def bot_start(message: types.Message):
    """
    Message handler for stoping making compliments. Called by /stop command
    """
    day_setup_btn = KeyboardButton("Day Setup (default: everyday)")
    time_setup_btn = KeyboardButton("Time Setup (default: at 8 a.m.)")
    help_btn = KeyboardButton("Help")
    contacts_btn = KeyboardButton("Contacts")

    menu = ReplyKeyboardMarkup(resize_keyboard=True).add(
        day_setup_btn, time_setup_btn, help_btn, contacts_btn
    )

    await message.reply("Choose your option from bot menu", reply_markup=menu)


@dp.message_handler(state=SetupStates.time)
async def set_time(message: types.Message, state: FSMContext):
    time = message.text
    days = (await state.get_data())["days"]

    if not validate_time(time):
        await message.answer(
            "Invalid time! It should be in format: hh:mm or h:mm. Please, enter time again"
        )
        await SetupStates.time.set()
        return

    await state.finish()
    await message.answer("Compliment days are successfully set!")
    await start_complimenting(message, days, time)


async def start_complimenting(message: types.Message, days: list, time: str = "9:00"):
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
            day.at(time).do(task).tag(message.chat.id)

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


@dp.message_handler(lambda message: message.text == "Day Setup (default: everyday)")
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
async def btn_callback_handler(callback_query: types.CallbackQuery, state: FSMContext):
    cb_data = callback_query.data

    if cb_data.split("-")[1] == "submit":
        markup = callback_query.message.reply_markup
        compliment_days_data = [
            btn[0].text.split(" - ")[1] == "✅" for btn in markup.inline_keyboard[:-1]
        ]

        # await bot.answer_callback_query(callback_query.id, "Submitted!")
        await state.update_data(days=compliment_days_data)
        await callback_query.message.answer("Enter the time")
        await SetupStates.time.set()
        # await start_complimenting(callback_query.message, compliment_days_data)
        return

    button_code = int(cb_data.split("-")[1])
    button_value = int(cb_data.split("-")[2])

    markup = callback_query.message.reply_markup
    btn = markup.inline_keyboard[button_code][0]
    btn.text = f"{btn.text.split(' - ')[0]} - {check_mark(not button_value)}"
    btn.callback_data = f"btn-{button_code}-{int(not button_value)}"

    await callback_query.message.edit_reply_markup(markup)
    await bot.answer_callback_query(callback_query.id)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
