import asyncio
import re
from random import choice
import os   

import aioschedule
import requests
from aiogram import Bot, Dispatcher, executor, types
from bs4 import BeautifulSoup
from pymemcache.client import base
from data import true_false

from aiogram.types import KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton

URL = "https://www.verywellmind.com/positivity-boosting-compliments-1717559"
API_TOKEN = os.getenv("BOT_TOKEN")

memcached_client = base.Client(("localhost", 11211))
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


def get_compliments():
    """
    Function gets a dict of compliment grouped by its types. 
    """
    cached_compliments = memcached_client.get("compliments_dict")

    if cached_compliments is not None:
        return eval(cached_compliments)

    try:
        response = requests.get(URL)
    except requests.exceptions.RequestException as e:
        return None

    html = response.text
    soup = BeautifulSoup(html, "html.parser")

    headers = list(
        map(
            lambda el: el.extract().text.strip(),
            soup.findAll("span", {"class": re.compile(r"mntl-sc-block-heading__text")}),
        )
    )
    raw_groups = soup.findAll(
        "ol", {"id": re.compile(r"mntl-sc-block_1-0-(7|12|17|22|27|32|37)")}
    )

    parsed_groups = [
        [comp.text for comp in group.findAll("li")] for group in raw_groups
    ]

    res = {title: comp_list for title, comp_list in zip(headers, parsed_groups)}
    memcached_client.set("compliments_dict", str(res).encode('utf-8'))
    
    return res


# @dp.message_handler(commands=["start"])
# async def start_complimenting(message: types.Message):
#     """
#     Message handler for scheduling compliments.
#     """
#     async def task():
#         compliments = get_compliments()
#         compliment_topics = list(compliments.keys())
#         choosen_topic = choice(compliment_topics)
#         choosen_compliment = choice(compliments[choosen_topic])


#         await message.reply(f"*{choosen_topic}*\n{choosen_compliment}")

#     # aioschedule.every().second.do(send)
#     while True:
#         await aioschedule.run_pending()
#         await asyncio.sleep(1)

async def start_complimenting(message: types.Message, days: list):
    """
    Function for scheduling compliments.
    """
    async def task():
        compliments = get_compliments()
        compliment_topics = list(compliments.keys())
        choosen_topic = choice(compliment_topics)
        choosen_compliment = choice(compliments[choosen_topic])


        # await message.reply(f"*{choosen_topic}*\n{choosen_compliment}")
        await message.answer(f"*{choosen_topic}*\n{choosen_compliment}")
        # await bot.send_message(chat_id, f"*{choosen_topic}*\n{choosen_compliment}")

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


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('btn'))
async def btn_callback_handler(callback_query: types.CallbackQuery):
    cb_data = callback_query.data

    if cb_data.split("-")[1] == "submit":
        markup = callback_query.message.reply_markup
        btn_data = [btn[0].text.split(" - ")[1] == "✅" for btn in markup.inline_keyboard[:-1]]

        await bot.answer_callback_query(callback_query.id, "Submitted!")
        await start_complimenting(callback_query.message, btn_data)
        return

    button_code = int(cb_data.split("-")[1])
    button_value = int(cb_data.split("-")[2])

    markup = callback_query.message.reply_markup
    btn = markup.inline_keyboard[button_code][0]
    btn.text = f"{btn.text.split(' - ')[0]} - {true_false[not button_value]}"
    btn.callback_data = f"btn-{button_code}-{int(not button_value)}"

    await callback_query.message.edit_reply_markup(markup)
    await bot.answer_callback_query(callback_query.id)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
