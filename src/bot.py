import asyncio
import logging
import os
from datetime import datetime
from random import choice

# import aioschedule
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.combining import OrTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
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
from emoji.core import emojize

from func import get_compliments
from storage import Storage
from utils import btn_captions, check_mark, format_schedule, msg

API_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

db = Storage()
logging.basicConfig(level=logging.INFO)

scheduler = AsyncIOScheduler()
scheduler.start()


class SetupStates(StatesGroup):
    time = State()


@dp.message_handler(commands=["start"])
async def bot_start(message: types.Message):
    """
    Message handler for /start command. Initialize bot menu.
    """

    logging.info(f"{message.from_user.id} ({message.from_user.username}) - starts bot")

    sch_setup_btn = KeyboardButton(msg.sch_setup)
    list_btn = KeyboardButton(msg.sch_list)
    clear_btn = KeyboardButton(msg.sch_clear)
    help_btn = KeyboardButton(msg.help_str)
    contacts_btn = KeyboardButton(msg.contacts)

    menu = ReplyKeyboardMarkup(resize_keyboard=True).add(
        sch_setup_btn, list_btn, clear_btn, help_btn, contacts_btn
    )

    await message.reply(msg.menu_message, reply_markup=menu)


@dp.message_handler(lambda message: message.text == msg.sch_setup)
@dp.message_handler(commands=["setup"])
async def set_days(message: types.Message):
    """
    Message handler for setting compliment days. Allows the user to choose days
    for compliments and then continue to select a time (set_time handler).
    """

    markup = InlineKeyboardMarkup()
    buttons = [
        InlineKeyboardButton(btn_captions.mon_on, callback_data="day-0-1"),
        InlineKeyboardButton(btn_captions.tue_on, callback_data="day-1-1"),
        InlineKeyboardButton(btn_captions.wed_on, callback_data="day-2-1"),
        InlineKeyboardButton(btn_captions.thu_on, callback_data="day-3-1"),
        InlineKeyboardButton(btn_captions.fri_on, callback_data="day-4-1"),
        InlineKeyboardButton(btn_captions.sat_on, callback_data="day-5-1"),
        InlineKeyboardButton(btn_captions.sun_on, callback_data="day-6-1"),
        InlineKeyboardButton(btn_captions.next, callback_data="day-next"),
    ]

    for btn in buttons:
        markup.row(btn)

    await message.reply(msg.days_message, reply_markup=markup)


async def start_complimenting(chat_id: str, days: list, time: str = "9:00"):
    """
    Function for scheduling compliments.
    """

    async def task():
        now_time = datetime.now().time()
        hour = now_time.hour

        if hour < 4 or hour > 22:
            greeting = msg.night_greeting
        elif hour < 12:
            greeting = msg.morning_greeting
        elif hour < 17:
            greeting = msg.day_greeting
        else:
            greeting = msg.evening_greeting

        compliments = get_compliments()
        compliment_topics = list(compliments.keys())
        choosen_topic = choice(compliment_topics)
        choosen_compliment = choice(compliments[choosen_topic])

        await bot.send_message(
            chat_id,
            msg.compliment_message.format(
                greeting=greeting, compliment=choosen_compliment
            ),
        )

    hour = int(time.split(":")[0])
    minute = int(time.split(":")[1])

    if scheduler.get_job(str(chat_id)):
        scheduler.remove_job(str(chat_id))

    trigger_list = []

    for idx, day in enumerate(days):
        if day:
            trigger_list.append(CronTrigger(day_of_week=idx, hour=hour, minute=minute))

    trigger = OrTrigger(trigger_list)

    scheduler.add_job(task, trigger, id=str(chat_id))


@dp.message_handler(lambda message: message.text == msg.sch_clear)
@dp.message_handler(commands=["stop"])
async def stop_complimenting(message: types.Message):
    """
    Message handler for stoping making compliments. Called by /stop command
    """
    logging.info(f"{message.from_user.id} ({message.from_user.username}) - stops bot")
    db.delete(message.chat.id)
    if scheduler.get_job(str(message.chat.id)):
        scheduler.remove_job(str(message.chat.id))
    await message.reply(msg.stop_message)


@dp.message_handler(lambda message: message.text == msg.sch_list)
@dp.message_handler(commands=["list"])
async def get_list(message: types.Message):
    """
    Message handler for getting all scheduled compliments by currend user.
    Called by /list command or 'List' message text.
    """

    data = db.get(message.chat.id)

    if data:
        days = data["days"]
        time = data["time"]

        result = format_schedule(days, time, msg.list_message)

        return await message.reply(result)
    else:
        return await message.reply(msg.empty_list_message)


@dp.message_handler(lambda message: message.text == msg.help_str)
@dp.message_handler(commands=["help"])
async def help_command(message: types.Message):
    """
    Message handler for help command. Returns help info.
    """
    await message.reply(msg.help_message)


@dp.message_handler(lambda message: message.text == msg.contacts)
@dp.message_handler(commands=["contacts"])
async def contacts_command(message: types.Message):
    """
    Message handler for contacts command.
    """
    await message.reply(msg.contacts_message)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith("day"))
async def day_callback_handler(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Callback handler for day-selecting buttons.
    """

    cb_data = callback_query.data

    if cb_data.split("-")[1] == "next":
        markup = callback_query.message.reply_markup
        compliment_days_data = [
            btn[0].text.split(" - ")[1] == emojize(":check_mark_button:")
            for btn in markup.inline_keyboard[:-1]
        ]

        time_markup = InlineKeyboardMarkup().add(
            *[
                InlineKeyboardButton(f"{i}:00", callback_data=f"time-{i}")
                for i in range(24)
            ]
        )

        await callback_query.message.edit_text(
            msg.time_message, reply_markup=time_markup
        )

        await callback_query.answer()
        await state.update_data(days=compliment_days_data)
        await state.update_data(message=callback_query.message)
        await SetupStates.time.set()

        return

    button_code = int(cb_data.split("-")[1])
    button_value = int(cb_data.split("-")[2])

    markup = callback_query.message.reply_markup
    btn = markup.inline_keyboard[button_code][0]
    btn.text = f"{btn.text.split(' - ')[0]} - {check_mark(not button_value)}"
    btn.callback_data = f"day-{button_code}-{int(not button_value)}"

    await callback_query.answer()
    await callback_query.message.edit_reply_markup(markup)


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

    logging.info(
        f"{callback_query.from_user.id} ({callback_query.from_user.username})"
        + " - has scheduled compliments:\n"
        + f"{days} at {time}"
    )

    await state.finish()
    await callback_query.answer("Done!")
    await callback_query.message.edit_text(
        format_schedule(days, time, msg.success_message)
    )

    db.add(callback_query.message.chat.id, days, time)
    await start_complimenting(callback_query.message.chat.id, days, time)


if __name__ == "__main__":
    saved_data = db.get_all()
    logging.info("Restore all scheduled compliments")
    for rec in saved_data:
        asyncio.ensure_future(start_complimenting(**rec))

    logging.info("Bot starting...")
    executor.start_polling(dp, skip_updates=True)
