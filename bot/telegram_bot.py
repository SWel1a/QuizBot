from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, Application

import json
import random
from functools import wraps

import constants
from utils import get_random_id, localized_text, quiz_start_args_parser


def authorized(func):
    @wraps(func)
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_handle = update.message.from_user.username
        if '@' + user_handle not in self.allowed_handles:
            await context.bot.send_message(chat_id=update.message.chat_id, text=localized_text(self.translations, self.bot_language, "unauthorized_command"))
            return
        return await func(self, update, context)
    return wrapper


class TelegramQuizBot:
    def __init__(self, telegram_token, allowed_handles, words_list, translations):
        self.words_list = words_list
        self.translations = translations
        self.bot_language = constants.DEFAULT_BOT_LANGUAGE
        # Telegram bot token
        self.telegram_token = telegram_token

        # Commands and handlers
        self.commands = [
            BotCommand(command="start", description=localized_text(self.translations, self.bot_language, "start_description")),
            BotCommand(command="stop", description=localized_text(self.translations, self.bot_language, "stop_description")),
            BotCommand(command="add_word", description=localized_text(self.translations, self.bot_language, "add_word_description")),
            BotCommand(command="remove_word", description=localized_text(self.translations, self.bot_language, "remove_word_description")),
            BotCommand(command="language", description=localized_text(self.translations, self.bot_language, "language_description"))
        ]

        self.handlers = [
            CommandHandler('start', self.start_callback_quiz),
            CommandHandler('stop', self.stop_callback_quiz),
            CommandHandler('add_word', self.add_word),
            CommandHandler('remove_word', self.remove_word),
            CommandHandler('language', self.set_language),
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.check_answer),
        ]

        # Custom data structures
        self.allowed_handles = allowed_handles
        self.ongoing_quizzes = {}
        self.language_preferences = {}
        self.bot_language_preferences = {}
        self.quiz_history = []

    def _localized_text(self, chat_id, key, format_params=None):
        language = self.bot_language_preferences.get(chat_id, constants.DEFAULT_BOT_LANGUAGE)
        return localized_text(self.translations, language, key, format_params)

    async def set_language(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id
        if not context.args:
            # No language provided, inform the user about available languages
            available_languages = ", ".join(self.translations.keys())
            await context.bot.send_message(chat_id=chat_id, 
                                           text=self._localized_text(chat_id, "no_bot_language", {"available_languages": available_languages}))
            return

        new_language = context.args[0].lower()
        if new_language not in self.translations:
            await context.bot.send_message(chat_id=chat_id, 
                                           text=self._localized_text(chat_id, "unsupported_language", {"available_languages": available_languages}))
            return

        self.bot_language_preferences[chat_id] = new_language
        await context.bot.send_message(chat_id=chat_id, 
                                       text=self._localized_text(chat_id, "language_set", {"new_language": new_language}))

    @authorized
    async def add_word(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.manage_word(update, context, 'add')
            
    @authorized
    async def remove_word(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.manage_word(update, context, 'remove')

    async def manage_word(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str):
        if not context.args:
            await context.bot.send_message(chat_id=update.effective_chat.id, 
                                           text=self._localized_text(update.effective_chat.id, "provide_word"))
        else:
            word = context.args[0]  # Assume that the word is the first argument
            if action == 'add':
                try:
                    await self.words_list.add_word(' '.join(context.args))
                    await context.bot.send_message(chat_id=update.message.chat_id, 
                                                   text=self._localized_text(update.message.chat_id, "word_added"))
                except json.JSONDecodeError:
                    await context.bot.send_message(chat_id=update.message.chat_id, 
                                                   text=self._localized_text(update.message.chat_id, "invalid_json_format"))
            elif action == 'remove':
                removed = await self.words_list.remove_word(word)
                if not removed:
                    await context.bot.send_message(chat_id=update.message.chat_id, 
                                                   text=self._localized_text(update.message.chat_id, "word_not_found", {"word": word}))
                else:
                    await context.bot.send_message(chat_id=update.message.chat_id, 
                                                   text=self._localized_text(update.message.chat_id, "word_removed", {"word": word}))

    async def callback_quiz(self, context: ContextTypes.DEFAULT_TYPE):
        language = self.language_preferences.get(context.job.chat_id)
        
        word_list = await self.words_list.get_words_by_language(language)

        if not word_list:
            await context.bot.send_message(chat_id=context.job.chat_id, 
                                           text=self._localized_text(context.job.chat_id, "no_words_specific_language", {"language": language}))
            return

        # Pick a random word-description pair
        random_pair = random.choice(word_list)

        word = random_pair['word']
        description = random_pair['description']

        message = await context.bot.send_message(chat_id=context.job.chat_id, 
                                                 text=self._localized_text(context.job.chat_id, "quiz_question", {"language": language, "description": description}))
        
        # Save to history
        self.quiz_history.append({
            'id': get_random_id(),
            'answer': word,
            'chat_id': context.job.chat_id,
            'attempts': 0,
            'message_ids': [message.message_id]  # Initial valid reply IDs only contains the original message
        })
        
        self.quiz_history = self.quiz_history[-constants.QUIZ_HISTORY_LENGTH:]


    async def start_callback_quiz(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id
        
        if chat_id in self.ongoing_quizzes:
            await context.bot.send_message(chat_id=chat_id, 
                                           text=self._localized_text(chat_id, "quiz_ongoing"))
            return

        language, interval_time_units = quiz_start_args_parser(context.args)

        word_list = await self.words_list.get_words_by_language(language)

        if not word_list:
            await context.bot.send_message(chat_id=chat_id, 
                                           text=self._localized_text(chat_id, "no_words_specific_language", {"language": language}))
            return

        # Store language preference using chat_id as the key
        self.language_preferences[chat_id] = language
        
        await context.bot.send_message(chat_id=chat_id, 
                                       text=self._localized_text(chat_id, "quiz_started", {"language": language}))
        # Set the alarm:
        # Store the job for the quiz
        job = context.job_queue.run_repeating(self.callback_quiz, interval=interval_time_units, first=1, name="timed_quiz", chat_id=chat_id)
        
        # Add the job to the ongoing_quizzes dict
        self.ongoing_quizzes[chat_id] = job


    async def stop_callback_quiz(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id
        ongoing_job = self.ongoing_quizzes.pop(chat_id, None)
        if ongoing_job:
            ongoing_job.schedule_removal()
            await context.bot.send_message(chat_id=chat_id, 
                                           text=self._localized_text(chat_id, "quiz_stopped"))
        else:
            await context.bot.send_message(chat_id=chat_id, 
                                           text=self._localized_text(chat_id, "no_ongoing"))


    async def check_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_message = update.message.text  # Get user's message
        chat_id = update.message.chat_id  # Get chat_id
        reply_to_message_id = update.message.reply_to_message.message_id if update.message.reply_to_message else None

        if not reply_to_message_id:  # If the user did not reply to a specific message, you might decide to ignore or handle differently
            await context.bot.send_message(chat_id=chat_id, 
                                           text=self._localized_text(chat_id, "reply_to_question"))
            return

        # Find the question in history based on reply_to_message_id
        corresponding_question = next((qa for qa in self.quiz_history if qa['chat_id'] == chat_id and reply_to_message_id in qa['message_ids']), None)
        
        if corresponding_question and user_message.lower().strip() == corresponding_question['answer'].lower().strip():
            await context.bot.send_message(chat_id=chat_id, 
                                           text=self._localized_text(chat_id, "correct_answer"))
        else:
            if corresponding_question:  # If a related question is found
                max_attempts = constants.DEFAULT_MAX_ATTEMPTS
                corresponding_question['attempts'] += 1
                corresponding_question['attempts'] = min(corresponding_question['attempts'], max_attempts)
                remaining_attempts = max_attempts - corresponding_question['attempts']
                
                if remaining_attempts > 0:
                    msg = await context.bot.send_message(chat_id=chat_id, 
                                                         text=self._localized_text(chat_id, "incorrect_answer", {"remaining_attempts": remaining_attempts}))
                    corresponding_question['message_ids'].append(msg.message_id)  # Add new message_id to valid reply ids
                else:
                    await context.bot.send_message(chat_id=chat_id, 
                                                   text=self._localized_text(chat_id, "incorrect_final_answer", {"correct_answer": corresponding_question["answer"]}))
            else:
                await context.bot.send_message(chat_id=chat_id, 
                                               text=self._localized_text(chat_id, "incorrect_outdated"))

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
