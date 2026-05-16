import asyncio
import logging
import os
from os import listdir
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import SchedulerDatabase

logging.basicConfig(level=logging.INFO)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

bot = Bot(token=TELEGRAM_BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
db_manager = SchedulerDatabase()
post_scheduler = AsyncIOScheduler()

class SetEvent(StatesGroup):
    waiting_for_eventnum = State()
    waiting_for_event_name = State()
    waiting_for_event_time = State()
    waiting_for_event_weekday = State()
    waiting_for_event_location = State()
    waiting_for_event_extra = State()
    finishing_up = State()

async def display_main_menu(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="Display my events", callback_data="display"),
            types.InlineKeyboardButton(text="Add an event", callback_data="add_custom")
        ]
    ])
    await message.edit_text(text="Please choose an option:", reply_markup=keyboard)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if not os.path.exists("users"):
        os.makedirs("users")

    for file in listdir("users"):
        await message.answer("You already have an account", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text="➕ إضافة منشور مجدول", callback_data="add_custom"),
                types.InlineKeyboardButton(text="📋 عرض منشوراتي", callback_data="display")
            ]
        ]))
        return

    else:
        user_id_str = str(message.from_user.id)
        data = {
            "user_id": message.from_user.id,
            "records": 0,
            "events": []
        }
        try:
            from utility import dump_data
            dump_data(user_id_str, data)
        except TypeError:
            from utility import dump_data
            dump_data(data)

        print("New user: " + message.from_user.username)

        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text="Create recommended schedule", callback_data="add_recommended"),
                types.InlineKeyboardButton(text="Create custom Schedule", callback_data="add_custom")
            ]
        ])
        await message.answer(text="Please choose an option...", reply_markup=keyboard)

@dp.callback_query(lambda call: call.data == "add_recommended")
async def add_recommended(call: types.CallbackQuery):
    await call.message.answer(text="Recommended events have been added to your schedule!")
    await display_main_menu(call.message)
    await call.answer()

@dp.callback_query(lambda call: call.data == "add_custom")
async def add_custom(call: types.CallbackQuery):
    from utility import load_data
    user_data = load_data(call.from_user.id)
    if user_data["records"] >= 8:
        print(call.from_user.username + " is trying to overcome the limit")
        await call.message.answer(text="You can't create more records!")
        await asyncio.sleep(0.5)
        await display_main_menu(call.message)
    else:
        print(call.from_user.username + " is creating new event")
        await SetEvent.waiting_for_event_name.set()
        await call.message.answer(text="Please input the name of the event:")
    await call.answer()

@dp.message(SetEvent.waiting_for_event_name)
async def get_event_name(message: types.Message, state: FSMContext):
    await state.update_data(event_name=message.text)
    await message.answer(text="Please input the time when event occurs in following format:\nHH:MM (24-hour standart):")
    await SetEvent.waiting_for_event_time.set()

@dp.message(SetEvent.waiting_for_event_time)
async def get_event_time(message: types.Message, state: FSMContext):
    await state.update_data(event_time=message.text)
    await message.answer(text="Please input the weekday when event occurs (1-7 for Monday-Sunday):")
    await SetEvent.waiting_for_event_weekday.set()

@dp.message(SetEvent.waiting_for_event_weekday)
async def get_event_weekday(message: types.Message, state: FSMContext):
    await state.update_data(event_weekday=message.text)
    await message.answer(text="Please input the location of the event:")
    await SetEvent.waiting_for_event_location.set()

@dp.message(SetEvent.waiting_for_event_location)
async def get_event_location(message: types.Message, state: FSMContext):
    await state.update_data(event_location=message.text)
    await message.answer(text="Please input extra information or '-' if there is none:")
    await SetEvent.waiting_for_event_extra.set()

@dp.message(SetEvent.waiting_for_event_extra)
async def get_event_extra(message: types.Message, state: FSMContext):
    from utility import generate_event_text
    await state.update_data(event_extra=message.text)
    user_data = await state.get_data()
    text = generate_event_text(user_data["event_name"], user_data["event_time"], user_data["event_weekday"], user_data["event_location"], user_data["event_extra"])
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="Create an event", callback_data="create_event"),
            types.InlineKeyboardButton(text="Forget", callback_data="forget")
        ]
    ])
    await message.answer(text="Review your event:\n\n" + text, reply_markup=keyboard)
    await SetEvent.finishing_up.set()

@dp.callback_query(lambda call: call.data == "create_event")
async def create_event(call: types.CallbackQuery, state: FSMContext):
    from utility import load_data, dump_data
    user_data = load_data(call.from_user.id)
    event_data = await state.get_data()
    
    event_id = user_data["records"]
    new_event = {
        "id": event_id,
        "name": event_data["event_name"],
        "time": event_data["event_time"],
        "weekday": event_data["event_weekday"],
        "location": event_data["event_location"],
        "extra": event_data["event_extra"]
    }
    
    user_data["events"].append(new_event)
    user_data["records"] += 1
    
    try: dump_data(str(call.from_user.id), user_data)
    except TypeError: dump_data(user_data)
    
    await call.message.answer(text="Event has been successfully created!")
    await state.clear()
    await display_main_menu(call.message)
    await call.answer()

@dp.callback_query(lambda call: call.data == "forget")
async def forget(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer(text="Event creation has been canceled.")
    await display_main_menu(call.message)
    await call.answer()

@dp.callback_query(lambda call: call.data == "display")
async def display_events(call: types.CallbackQuery):
    from utility import load_data
    user_data = load_data(call.from_user.id)
    buttons = []
    n_records = user_data["records"]
    for i in range(n_records):
        event = user_data["events"][i]
        buttons.append([types.InlineKeyboardButton(text=event["name"], callback_data=f"disp_{i}")])
    
    buttons.append([types.InlineKeyboardButton(text="<< Back", callback_data="main_menu")])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await call.message.edit_text(text="Please choose an event to view:", reply_markup=keyboard)
    await call.answer()

@dp.callback_query(lambda call: call.data.startswith("disp_"))
async def show_event(call: types.CallbackQuery):
    from utility import load_data, generate_event_text
    event_num = int(call.data.split("_")[1])
    user_data = load_data(call.from_user.id)
    event = user_data["events"][event_num]
    event_output = generate_event_text(event["name"], event["time"], event["weekday"], event["location"], event["extra"])
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="<< Back", callback_data="display"),
            types.InlineKeyboardButton(text="Delete", callback_data=f"del_{event_num}")
        ]
    ])
    await call.message.edit_text(text=event_output, reply_markup=keyboard)
    await call.answer()

@dp.callback_query(lambda call: call.data == "main_menu")
async def show_main_menu(call: types.CallbackQuery):
    await display_main_menu(call.message)
    await call.answer()

@dp.callback_query(lambda call: call.data.startswith("del_"))
async def delete_event(call: types.CallbackQuery):
    from utility import load_data, dump_data
    event_num = int(call.data.split("_")[1])
    user_data = load_data(call.from_user.id)
    user_data["events"].pop(event_num)
    user_data["records"] -= 1
    
    try: dump_data(str(call.from_user.id), user_data)
    except TypeError: dump_data(user_data)
    
    await call.message.answer(text="You have deleted the event.")
    await display_main_menu(call.message)
    await call.answer()

async def check_and_publish_pending_posts():
    pending_posts_list = db_manager.get_pending_posts()
    for post in pending_posts_list:
        db_post_id, target_channel, text_to_publish = post
        try:
            await bot.send_message(chat_id=target_channel, text=text_to_publish)
            db_manager.mark_post_as_published(db_post_id)
        except Exception:
            pass

async def main():
    post_scheduler.add_job(check_and_publish_pending_posts, 'interval', seconds=60)
    post_scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
