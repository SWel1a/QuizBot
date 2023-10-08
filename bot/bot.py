import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import json
import random
import os
import uuid
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

# Read environment variables
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
ALLOWED_HANDLES = os.getenv('ALLOWED_HANDLES').split(',')
ongoing_quizzes = {}
language_preferences = {}
quiz_history = []


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def get_random_id():
    return str(uuid.uuid4())  # Returns a random UUID as a string


async def add_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_handle = update.message.from_user.username
    if '@' + user_handle not in ALLOWED_HANDLES:
        await context.bot.send_message(chat_id=update.message.chat_id, text="You are not authorized to use this command.")
        return
    
    if context.args:
        try:
            word_data = json.loads(' '.join(context.args))
            word_data["id"] = get_random_id()
            with open('words.json', 'r', encoding='utf-8') as f:
                word_list = json.load(f)
            word_list.append(word_data)
            with open('words.json', 'w', encoding='utf-8') as f:
                json.dump(word_list, f, ensure_ascii=False, indent=4)
            await context.bot.send_message(chat_id=update.message.chat_id, text=f"Word added with ID: {word_data['id']}")
        except json.JSONDecodeError:
            await context.bot.send_message(chat_id=update.message.chat_id, text="Invalid JSON format.")
    else:
        await context.bot.send_message(chat_id=update.message.chat_id, text="Please provide word data in JSON format.")
        

async def remove_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_handle = update.message.from_user.username
    if '@' + user_handle not in ALLOWED_HANDLES:
        await context.bot.send_message(chat_id=update.message.chat_id, text="You are not authorized to use this command.")
        return
    if not context.args:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Please provide a word to remove.")
    else:
        word_to_remove = context.args[0]  # Assume that the word is the first argument
        with open('words.json', 'r', encoding='utf-8') as f:
            word_list = json.load(f)
        
        # Store the original list length to check against it later
        original_length = len(word_list)
        
        # Filter the list to keep only words that are NOT equal to `word_to_remove`
        word_list = [word for word in word_list if word.get('word').lower() != word_to_remove.lower()]
        
        # If the length of the word_list has not changed, no word was removed
        if len(word_list) == original_length:
            await context.bot.send_message(chat_id=update.message.chat_id, text=f"No word found for: {word_to_remove}")
        else:
            with open('words.json', 'w', encoding='utf-8') as f:
                json.dump(word_list, f, ensure_ascii=False, indent=4)
            await context.bot.send_message(chat_id=update.message.chat_id, text=f"Word: {word_to_remove} removed.")



def get_random_quiz(language=None):
    filename_json = 'words.json'

    # Load the JSON file
    with open(filename_json, 'r', encoding='utf-8') as f:
        word_list = json.load(f)

    # Filter the word list based on the specified language
    if language:
        word_list = [word for word in word_list if word['language'] == language]

    if not word_list:
        return "No words found for the specified language.", None

    # Pick a random word-description pair
    random_pair = random.choice(word_list)

    word = random_pair['word']
    description = random_pair['description']
    question_id = get_random_id()

    return f"What is the word (in {language}) with given description: {description}?", word, question_id



async def callback_quiz(context: ContextTypes.DEFAULT_TYPE):
    language = language_preferences.get(context.job.chat_id, 'korean')  # Default to 'korean' if no preference found
    
    random_quiz, correct_answer, question_id = get_random_quiz(language=language)

    # Save to history
    quiz_history.append({
        'id': question_id,
        'answer': correct_answer,
        'chat_id': context.job.chat_id
    })
    
    # Trim quiz_history to only keep the last 100 questions
    while len(quiz_history) > 100:
        quiz_history.pop(0)

    if correct_answer:
        await context.bot.send_message(chat_id=context.job.chat_id, text=random_quiz)
    else:
        await context.bot.send_message(chat_id=context.job.chat_id, text="No words found for the specified language.")



async def start_callback_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    
    if chat_id in ongoing_quizzes:
        await context.bot.send_message(chat_id=chat_id, text='A quiz is already ongoing in this chat! Use /stop to stop it.')
        return

    # Default values
    language = 'korean'  # Default language
    interval_time_min = 120  # Default time
    
    # Handling arguments
    if len(context.args) >= 1:
        first_arg = context.args[0]
        if first_arg.isnumeric():
            interval_time_min = int(first_arg)
        else:
            language = first_arg
            if len(context.args) > 1 and context.args[1].isnumeric():
                interval_time_min = int(context.args[1])
    
    interval_time = interval_time_min * 60
    
    # Store language preference using chat_id as the key
    language_preferences[chat_id] = language
    
    await context.bot.send_message(chat_id=chat_id, text=f'Started timed Quiz with language: {language}!\nHere\'s the first one:')
    # Set the alarm:
    # Store the job for the quiz
    job = context.job_queue.run_repeating(callback_quiz, interval=interval_time, first=1, name="timed_quiz", chat_id=chat_id)
    
    # Add the job to the ongoing_quizzes dict
    ongoing_quizzes[chat_id] = job


async def stop_callback_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    ongoing_job = ongoing_quizzes.pop(chat_id, None)
    if ongoing_job:
        ongoing_job.schedule_removal()
        await context.bot.send_message(chat_id=chat_id, text='Stopped!')
    else:
        await context.bot.send_message(chat_id=chat_id, text='No ongoing quiz to stop!')


async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text  # Get user's message
    chat_id = update.message.chat_id  # Get chat_id
    
    # Look for the answer in the history
    corresponding_question = None
    for qa in quiz_history:
        if qa['chat_id'] == chat_id and user_message.lower().strip() == qa['answer'].lower().strip():
            corresponding_question = qa
            break
    
    if corresponding_question:  # If a correct answer was found
        await context.bot.send_message(chat_id=chat_id, text='Correct! 🎉')
        quiz_history.remove(corresponding_question)  # Remove the answered Q-A pair
    else:
        await context.bot.send_message(chat_id=chat_id, text='Incorrect or outdated answer. Try again with a new question!')


if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    handlers = [
        CommandHandler('start', start_callback_quiz),
        CommandHandler('stop', stop_callback_quiz),
        CommandHandler('add_word', add_word),
        CommandHandler('remove_word', remove_word),
        MessageHandler(filters.TEXT & ~filters.COMMAND, check_answer),
    ]

    for handler in handlers:
        application.add_handler(handler)

    application.run_polling()
