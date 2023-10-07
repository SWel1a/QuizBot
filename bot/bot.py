import logging
from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import InlineQueryHandler


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["words"] = []  # Initialize an empty list to store words
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)


async def caps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_caps = ' '.join(context.args).upper()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)


async def inline_caps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query
    if not query:
        return
    results = []
    results.append(
        InlineQueryResultArticle(
            id=query.upper(),
            title='Caps',
            input_message_content=InputTextMessageContent(query.upper())
        )
    )
    await context.bot.answer_inline_query(update.inline_query.id, results)


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


async def callback_alarm(context: ContextTypes.DEFAULT_TYPE):
    # Beep the person who called this alarm:
    await context.bot.send_message(chat_id=context.job.chat_id, text=f'BEEP {context.job.data}!')


async def callback_timer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    name = update.effective_chat.full_name
    if name is None:
        name = '@' + update.message.from_user.username
    if not len(context.args) or not str(context.args[0]).isnumeric():
        timer_time = 60
    else:
        timer_time = int(context.args[0])
    await context.bot.send_message(chat_id=chat_id, text=f'Setting a timer for {timer_time} second(s)!')
    # Set the alarm:
    context.job_queue.run_once(callback_alarm, timer_time, data=name, chat_id=chat_id)


if name == '__main__':
    application = ApplicationBuilder().token(TG_TOKEN).build()

    handlers = [
        CommandHandler('start', start),  # start_handler
        MessageHandler(filters.TEXT & (~filters.COMMAND), echo),  # echo_handler
        CommandHandler('caps', caps),  # caps_handler
        CommandHandler('anecdote', anecdote),  # anecdote_handler
        CommandHandler('start_anecdote', start_callback_anecdote),  # timed anecdote_handler
        CommandHandler('stop_anecdote', stop_callback_anecdote),  # timed anecdote_handler
        CommandHandler('timer', callback_timer),
        InlineQueryHandler(inline_caps),  # inline_caps_handler
        MessageHandler(filters.COMMAND, unknown),  # unknown_handler
    ]

    for handler in handlers:
        application.add_handler(handler)

    application.run_polling()


    async def remove_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Please provide a word to remove.")
        else:
            word_to_remove = context.args[0].lower()
            if word_to_remove in context.user_data.get("words", []):
                context.user_data["words"].remove(word_to_remove)
                await context.bot.send_message(chat_id=update.effective_chat.id,
                                               text=f"Word '{word_to_remove}' removed.")
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id,
                                               text=f"Word '{word_to_remove}' not found in the list.")


    # Add the new command handler to the list of handlers
    CommandHandler('removeword', remove_word),


