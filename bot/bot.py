import logging
from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import InlineQueryHandler

import os
from dotenv import load_dotenv


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a quiz bot, please use commands /start_easy, /start_hard to use me!")


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")


async def anecdote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    random_anecdote = get_random_anecdote()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=random_anecdote)


async def callback_anecdote(context: ContextTypes.DEFAULT_TYPE):
    random_anecdote = get_random_anecdote()
    await context.bot.send_message(chat_id=context.job.chat_id, text=random_anecdote)


async def start_callback_anecdote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    await context.bot.send_message(chat_id=chat_id, text=f'Started timed anecdotes!')
    # Set the alarm:
    context.job_queue.run_repeating(callback_anecdote, interval=25200, first=1, name="timed_anecdotes", chat_id=chat_id)


async def stop_callback_anecdote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    current_jobs = context.job_queue.get_jobs_by_name("timed_anecdotes")
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
        CommandHandler('start', start),  # start_handler
        CommandHandler('anecdote', anecdote),  # anecdote_handler
        CommandHandler('start_anecdote', start_callback_anecdote),  # timed anecdote_handler
        CommandHandler('stop_anecdote', stop_callback_anecdote),  # timed anecdote_handler
        MessageHandler(filters.COMMAND, unknown),  # unknown_handler
    ]

    for handler in handlers:
        application.add_handler(handler)

    application.run_polling()
# here will be the code
