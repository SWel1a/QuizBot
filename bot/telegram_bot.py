from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, Application
import json
import random
import uuid


def get_random_id():
    return str(uuid.uuid4())  # Returns a random UUID as a string


def get_random_quiz(filename_json, language=None):
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


class TelegramQuizBot:
    def __init__(self, telegram_token, allowed_handles, words_file_path):
        self.words_file_path = words_file_path
        # Telegram bot token
        self.telegram_token = telegram_token

        # Commands and handlers
        self.commands = [
            BotCommand(command="start", description=""),
            BotCommand(command="stop", description=""),
            BotCommand(command="add_word", description=""),
            BotCommand(command="remove_word", description=""),
        ]

        handlers = [
            CommandHandler('start', self.start_callback_quiz),
            CommandHandler('stop', self.stop_callback_quiz),
            CommandHandler('add_word', self.add_word),
            CommandHandler('remove_word', self.remove_word),
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.check_answer),
        ]

        # Custom data structures
        self.allowed_handles = allowed_handles
        self.ongoing_quizzes = {}
        self.language_preferences = {}
        self.quiz_history = []


    async def add_word(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_handle = update.message.from_user.username
        if '@' + user_handle not in self.allowed_handles:
            await context.bot.send_message(chat_id=update.message.chat_id, text="You are not authorized to use this command.")
            return
        
        if context.args:
            try:
                word_data = json.loads(' '.join(context.args))
                word_data["id"] = get_random_id()
                with open(self.words_file_path, 'r', encoding='utf-8') as f:
                    word_list = json.load(f)
                word_list.append(word_data)
                with open(self.words_file_path, 'w', encoding='utf-8') as f:
                    json.dump(word_list, f, ensure_ascii=False, indent=4)
                await context.bot.send_message(chat_id=update.message.chat_id, text=f"Word added with ID: {word_data['id']}")
            except json.JSONDecodeError:
                await context.bot.send_message(chat_id=update.message.chat_id, text="Invalid JSON format.")
        else:
            await context.bot.send_message(chat_id=update.message.chat_id, text="Please provide word data in JSON format.")
            

    async def remove_word(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_handle = update.message.from_user.username
        if '@' + user_handle not in self.allowed_handles:
            await context.bot.send_message(chat_id=update.message.chat_id, text="You are not authorized to use this command.")
            return
        if not context.args:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Please provide a word to remove.")
        else:
            word_to_remove = context.args[0]  # Assume that the word is the first argument
            with open(self.words_file_path, 'r', encoding='utf-8') as f:
                word_list = json.load(f)
            
            # Store the original list length to check against it later
            original_length = len(word_list)
            
            # Filter the list to keep only words that are NOT equal to `word_to_remove`
            word_list = [word for word in word_list if word.get('word').lower() != word_to_remove.lower()]
            
            # If the length of the word_list has not changed, no word was removed
            if len(word_list) == original_length:
                await context.bot.send_message(chat_id=update.message.chat_id, text=f"No word found for: {word_to_remove}")
            else:
                with open(self.words_file_path, 'w', encoding='utf-8') as f:
                    json.dump(word_list, f, ensure_ascii=False, indent=4)
                await context.bot.send_message(chat_id=update.message.chat_id, text=f"Word: {word_to_remove} removed.")


    async def callback_quiz(self, context: ContextTypes.DEFAULT_TYPE):
        language = self.language_preferences.get(context.job.chat_id, 'korean')  # Default to 'korean' if no preference found
        
        random_quiz, correct_answer, question_id = get_random_quiz(self.words_file_path, language=language)

        if correct_answer:
            message = await context.bot.send_message(chat_id=context.job.chat_id, text=random_quiz)
        else:
            await context.bot.send_message(chat_id=context.job.chat_id, text="No words found for the specified language.")
            return
        
        # Save to history
        self.quiz_history.append({
            'id': question_id,
            'answer': correct_answer,
            'chat_id': context.job.chat_id,
            'attempts': 0,
            'message_ids': [message.message_id]  # Initial valid reply IDs only contains the original message
        })
        
        # Trim quiz_history to only keep the last 100 questions
        while len(self.quiz_history) > 100:
            self.quiz_history.pop(0)


    async def start_callback_quiz(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id
        
        if chat_id in self.ongoing_quizzes:
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
        language = language.lower().strip()

        # Load the JSON file
        with open(self.words_file_path, 'r', encoding='utf-8') as f:
            word_list = json.load(f)

        if language:
            word_list = [word for word in word_list if word['language'] == language]
        else:
            word_list = []

        if not word_list:
            await context.bot.send_message(chat_id=chat_id, text=f'No words found for the specified language \"{language}\".')
            return

        # Store language preference using chat_id as the key
        self.language_preferences[chat_id] = language
        
        await context.bot.send_message(chat_id=chat_id, text=f'Started timed Quiz with language: {language}!\nHere\'s the first one:')
        # Set the alarm:
        # Store the job for the quiz
        job = context.job_queue.run_repeating(self.callback_quiz, interval=interval_time, first=1, name="timed_quiz", chat_id=chat_id)
        
        # Add the job to the ongoing_quizzes dict
        self.ongoing_quizzes[chat_id] = job


    async def stop_callback_quiz(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id
        ongoing_job = self.ongoing_quizzes.pop(chat_id, None)
        if ongoing_job:
            ongoing_job.schedule_removal()
            await context.bot.send_message(chat_id=chat_id, text='Stopped!')
        else:
            await context.bot.send_message(chat_id=chat_id, text='No ongoing quiz to stop!')


    async def check_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_message = update.message.text  # Get user's message
        chat_id = update.message.chat_id  # Get chat_id
        reply_to_message_id = update.message.reply_to_message.message_id if update.message.reply_to_message else None

        if not reply_to_message_id:  # If the user did not reply to a specific message, you might decide to ignore or handle differently
            await context.bot.send_message(chat_id=chat_id, text='Please reply directly to the question.')
            return

        # Find the question in history based on reply_to_message_id
        corresponding_question = next((qa for qa in self.quiz_history if qa['chat_id'] == chat_id and reply_to_message_id in qa['message_ids']), None)
        
        if corresponding_question and user_message.lower().strip() == corresponding_question['answer'].lower().strip():
            await context.bot.send_message(chat_id=chat_id, text='Correct! 🎉')
        else:
            if corresponding_question:  # If a related question is found
                max_attempts = 3
                corresponding_question['attempts'] += 1
                corresponding_question['attempts'] = min(corresponding_question['attempts'], max_attempts)
                remaining_attempts = max_attempts - corresponding_question['attempts']
                
                if remaining_attempts > 0:
                    msg = await context.bot.send_message(chat_id=chat_id, text=f'Incorrect. You have {remaining_attempts} attempts left. Try again by replying to this message.')
                    corresponding_question['message_ids'].append(msg.message_id)  # Add new message_id to valid reply ids
                else:
                    await context.bot.send_message(chat_id=chat_id, text=f'Incorrect. The correct answer was: {corresponding_question["answer"]}')
            else:
                await context.bot.send_message(chat_id=chat_id, text='Incorrect or outdated answer. Try again with a new question!')

    async def post_init(self, application: Application):
            """
            Post initialization hook for the bot.
            """
            await application.bot.set_my_commands(self.commands)

    def run(self):
        """
        Runs the bot indefinitely until the user presses Ctrl+C
        """
        application = ApplicationBuilder() \
            .token(self.telegram_token) \
            .post_init(self.post_init) \
            .build()

        for handler in self.handlers:
            application.add_handler(handler)
        
        application.run_polling()
