import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import json
import random
import os
from dotenv import load_dotenv


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def get_random_quiz():
    filename_json = 'words.json'

    # Load the JSON file
    with open(filename_json, 'r', encoding='utf-8') as f:
        word_list = json.load(f)

    # Pick a random word-description pair
    random_pair = random.choice(word_list)

    word = random_pair['word']
    description = random_pair['description']

    return f"Word: {word} Description: {description}"


async def callback_quiz(context: ContextTypes.DEFAULT_TYPE):
    random_anecdote = get_random_quiz()
    await context.bot.send_message(chat_id=context.job.chat_id, text=random_anecdote)


async def start_callback_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if not len(context.args) or not str(context.args[0]).isnumeric():
        interval_time = 60
    else:
        interval_time = int(context.args[0])
    await context.bot.send_message(chat_id=chat_id, text=f'Started timed Quiz!\n Here\'s the first one:')
    # Set the alarm:
    context.job_queue.run_repeating(callback_quiz, interval=interval_time, first=1, name="timed_quiz", chat_id=chat_id)


async def stop_callback_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    current_jobs = context.job_queue.get_jobs_by_name("timed_quiz")
    for job in current_jobs:
        job.schedule_removal()
    await context.bot.send_message(chat_id=chat_id, text='Stopped!')


if __name__ == '__main__':
    # Load environment variables from .env file
    load_dotenv()

    # Read environment variables
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    handlers = [
        CommandHandler('start', start_callback_quiz),
        CommandHandler('stop', stop_callback_quiz),
    ]

    for handler in handlers:
        application.add_handler(handler)

    application.run_polling()
