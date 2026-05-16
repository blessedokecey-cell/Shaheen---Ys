from aiogram import Dispatcher, Bot
from crontab import *
import os
from utility import generate_event_text
import logging

# تهيئة البوت والموزع المتوافق بشكل مفرد وصحيح
bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

DELAY = -30

my_cron = CronTab(user="your_user_name")
command_at = 'python3 /home/zavid/Scheduler_Bot/sender.py {0} \'{1}\''.format(event_id, text)
job = my_cron.new(command=command_at, comment=str(event_id))
job.enable()
time_parts = time.split(":")
job.setall(time_parts[1] + " " + time_parts[0] + " * * " + wday)
my_cron.write()



def set_up_notification(chat_id: int, event: dict):
    text_to_send = event["event_name"] + " starts in 30 minutes!"
    # text_to_send += generate_event_text(event)
    delayed_time = [int(x) for x in event["event_time"].split(":")]
    delayed_time[1] += DELAY
    while delayed_time[1] < 0:
        delayed_time[0] -= 1
        delayed_time[1] += 60
    if delayed_time[0] < 0:
        delayed_time[0] += 24
    delayed_time = str(delayed_time[0]) + ":" + str(delayed_time[1])
    create_job(event_id=event["event_id"],
               chat_id=chat_id,
               text=text_to_send,
               wday=(event["event_wday"].upper()[0:3]),
               time=delayed_time
               )


def delete_notification(event_id: int):
    cron = CronTab(user="zavid")
    cron.remove_all(comment=str(event_id))
    cron.write()
  
