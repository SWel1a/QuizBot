import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import json
import random
import os
from dotenv import load_dotenv


quiz_answers = {}


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
    language = random_pair['language']
    description = random_pair['description']

    return f"What is the word (in {language}) with given description: {description}?", word


async def callback_quiz(context: ContextTypes.DEFAULT_TYPE):
    random_anecdote, correct_answer = get_random_quiz()
    # Store the correct answer using chat_id as the key
    quiz_answers[context.job.chat_id] = correct_answer
    await context.bot.send_message(chat_id=context.job.chat_id, text=random_anecdote)


async def start_callback_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if not len(context.args) or not str(context.args[0]).isnumeric():
        interval_time = 60
    else:
        interval_time = int(context.args[0])
    await context.bot.send_message(chat_id=chat_id, text=f'Started timed Quiz!\nHere\'s the first one:')
    # Set the alarm:
    context.job_queue.run_repeating(callback_quiz, interval=interval_time, first=1, name="timed_quiz", chat_id=chat_id)


async def stop_callback_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    current_jobs = context.job_queue.get_jobs_by_name("timed_quiz")
    for job in current_jobs:
        job.schedule_removal()
    await context.bot.send_message(chat_id=chat_id, text='Stopped!')


async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text  # Get user's message
    chat_id = update.message.chat_id  # Get chat_id
    correct_answer = quiz_answers.get(chat_id)  # Retrieve the correct answer for this chat_id
    
    if correct_answer:  # If a correct answer exists for this chat_id
        if user_message.lower().strip() == correct_answer.lower().strip():  # Check correctness
            await context.bot.send_message(chat_id=chat_id, text='Correct! 🎉')
        else:
            await context.bot.send_message(chat_id=chat_id, text=f'Incorrect! The correct answer was: {correct_answer}')


if __name__ == '__main__':
    # Load environment variables from .env file
    load_dotenv()

    # Read environment variables
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    handlers = [
        CommandHandler('start', start_callback_quiz),
        CommandHandler('stop', stop_callback_quiz),
        MessageHandler(filters.TEXT & ~filters.COMMAND, check_answer),
    ]

    for handler in handlers:
        application.add_handler(handler)

    application.run_polling()
