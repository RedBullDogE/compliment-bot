import asyncio
import os
from random import choice

import aioschedule
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.storage import FSMContext
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from func import get_compliments
from utils import check_mark, format_schedule, validate_time

API_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())


class SetupStates(StatesGroup):
    time = State()


@dp.message_handler(commands=["start"])
async def bot_start(message: types.Message):
    """
    Message handler for /start command. Initialize bot menu.
    """

    sch_setup_btn = KeyboardButton("Schedule setup")
    list_btn = KeyboardButton("List")
    clear_btn = KeyboardButton("Clear schedule")
    help_btn = KeyboardButton("Help")
    contacts_btn = KeyboardButton("Contacts")

    menu = ReplyKeyboardMarkup(resize_keyboard=True).add(
        sch_setup_btn, list_btn, clear_btn, help_btn, contacts_btn
    )

    await message.reply("Choose your option from bot menu", reply_markup=menu)


@dp.message_handler(lambda message: message.text == "Schedule setup")
@dp.message_handler(commands=["set_days"])
async def set_days(message: types.Message):
    """
    Message handler for setting compliment days. Allows the user to choose days
    for compliments and then continue to select a time (set_time handler).
    """

    markup = InlineKeyboardMarkup()
    buttons = [
        InlineKeyboardButton("Mon - ✅", callback_data="day-0-1"),
        InlineKeyboardButton("Tue - ✅", callback_data="day-1-1"),
        InlineKeyboardButton("Wed - ✅", callback_data="day-2-1"),
        InlineKeyboardButton("Thu - ✅", callback_data="day-3-1"),
        InlineKeyboardButton("Fri - ✅", callback_data="day-4-1"),
        InlineKeyboardButton("Sat - ✅", callback_data="day-5-1"),
        InlineKeyboardButton("Sun - ✅", callback_data="day-6-1"),
        InlineKeyboardButton("Next", callback_data="day-next"),
    ]

    for btn in buttons:
        markup.row(btn)

    text = "Choose compliment days:"

    await message.reply(text, reply_markup=markup)


@dp.message_handler(state=SetupStates.time)
async def set_time(message: types.Message, state: FSMContext):
    """
    Message handler for setting time for compliments. It follows set_days handler if
    the user has selected days.
    """

    time = message.text
    state_data = await state.get_data()
    days = state_data["days"]
    message = state_data["message"]

    if not validate_time(time):
        await message.answer(
            "Invalid time! It should be in format: hh:mm or h:mm. Please, enter time again"
        )
        await SetupStates.time.set()
        return

    await state.finish()
    await message.answer("Compliment days are successfully set!")
    await start_complimenting(message.chat.id, days, time)


async def start_complimenting(chat_id: str, days: list, time: str = "9:00"):
    """
    Function for scheduling compliments.
    """

    async def task():
        compliments = get_compliments()
        compliment_topics = list(compliments.keys())
        choosen_topic = choice(compliment_topics)
        choosen_compliment = choice(compliments[choosen_topic])

        await bot.send_message(chat_id, f"*{choosen_topic}*\n{choosen_compliment}")

    day_schedulers = [
        aioschedule.every().monday,
        aioschedule.every().tuesday,
        aioschedule.every().wednesday,
        aioschedule.every().thursday,
        aioschedule.every().friday,
        aioschedule.every().saturday,
        aioschedule.every().sunday,
    ]

    aioschedule.clear(chat_id)

    for idx, day in enumerate(day_schedulers):
        if days[idx]:
            day.at(time).do(task).tag(chat_id)

    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


@dp.message_handler(lambda message: message.text == "Clear schedule")
@dp.message_handler(commands=["stop"])
async def stop_complimenting(message: types.Message):
    """
    Message handler for stoping making compliments. Called by /stop command
    """

    aioschedule.clear(message.chat.id)
    await message.reply("From now on I stop making compliments! I hope see you soon ^^")


@dp.message_handler(lambda message: message.text == "List")
@dp.message_handler(commands=["get"])
async def get_schedules(message: types.Message):
    """
    Message handler for getting all scheduled compliments by currend user.
    Called by /stop command or 'List' message text.
    """

    tasks = [task for task in aioschedule.jobs if message.chat.id in task.tags]

    if not tasks:
        await message.reply(
            "You still don't have scheduled compliments! Set it with /set_days"
        )

    result = "\n".join([f" - {t.start_day}" for t in tasks])

    await message.reply(
        f"Scheduled compliments:\n{result}\nAt {tasks[-1].at_time.strftime('%H:%M')}"
    )


@dp.callback_query_handler(lambda c: c.data and c.data.startswith("day"))
async def day_callback_handler(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Callback handler for day-selecting buttons.
    """

    cb_data = callback_query.data

    if cb_data.split("-")[1] == "next":
        markup = callback_query.message.reply_markup
        compliment_days_data = [
            btn[0].text.split(" - ")[1] == "✅" for btn in markup.inline_keyboard[:-1]
        ]

        time_markup = InlineKeyboardMarkup().add(
            *[
                InlineKeyboardButton(f"{i}:00", callback_data=f"time-{i}")
                for i in range(24)
            ]
        )

        await callback_query.message.edit_text(
            "Choose time for compliments:", reply_markup=time_markup
        )

        await state.update_data(days=compliment_days_data)
        await state.update_data(message=callback_query.message)
        await SetupStates.time.set()
        await callback_query.answer()

        return

    button_code = int(cb_data.split("-")[1])
    button_value = int(cb_data.split("-")[2])

    markup = callback_query.message.reply_markup
    btn = markup.inline_keyboard[button_code][0]
    btn.text = f"{btn.text.split(' - ')[0]} - {check_mark(not button_value)}"
    btn.callback_data = f"day-{button_code}-{int(not button_value)}"

    await callback_query.message.edit_reply_markup(markup)
    await callback_query.answer()


@dp.callback_query_handler(
    lambda c: c.data and c.data.startswith("time"), state=SetupStates.time
)
async def time_callback_handler(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Callback handler for time-selecting buttons.
    """

    cb_data = callback_query.data
    time = f"{cb_data.split('-')[1]}:00"
    state_data = await state.get_data()
    days = state_data["days"]

    await state.finish()
    await callback_query.answer("Done!")
    await callback_query.message.edit_text(format_schedule(days, time))
    await start_complimenting(callback_query.message.chat.id, days, time)

    await callback_query.answer()


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
