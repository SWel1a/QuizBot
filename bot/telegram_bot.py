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
            await context.bot.send_message(chat_id=update.message.chat_id, text=localized_text(self.translations, "unauthorized_command", self.bot_language))
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
            BotCommand(command="start", description=localized_text(self.translations, "start_description", self.bot_language)),
            BotCommand(command="stop", description=localized_text(self.translations, "stop_description", self.bot_language)),
            BotCommand(command="add_word", description=localized_text(self.translations, "add_word_description", self.bot_language)),
            BotCommand(command="remove_word", description=localized_text(self.translations, "remove_word_description", self.bot_language)),
        ]

        self.handlers = [
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

    @authorized
    async def add_word(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.manage_word(update, context, 'add')
            
    @authorized
    async def remove_word(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.manage_word(update, context, 'remove')

    async def manage_word(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str):
        if not context.args:
            await context.bot.send_message(chat_id=update.effective_chat.id, 
                                           text=localized_text(self.translations, "provide_word", self.bot_language))
        else:
            word = context.args[0]  # Assume that the word is the first argument
            if action == 'add':
                try:
                    await self.words_list.add_word(' '.join(context.args))
                    await context.bot.send_message(chat_id=update.message.chat_id, 
                                                   text=localized_text(self.translations, "word_added", self.bot_language))
                except json.JSONDecodeError:
                    await context.bot.send_message(chat_id=update.message.chat_id, 
                                                   text=localized_text(self.translations, "invalid_json_format", self.bot_language))
            elif action == 'remove':
                removed = await self.words_list.remove_word(word)
                if not removed:
                    await context.bot.send_message(chat_id=update.message.chat_id, 
                                                   text=localized_text(self.translations, "word_not_found", self.bot_language, {"word": word}))
                else:
                    await context.bot.send_message(chat_id=update.message.chat_id, 
                                                   text=localized_text(self.translations, "word_removed", self.bot_language, {"word": word}))

    async def _get_random_quiz(self, words_list, language=None):
        word_list = await words_list.get_words_by_language(language)

        if not word_list:
            return localized_text(self.translations, "no_words_specific_language", self.bot_language, {"language": language}), None, None

        # Pick a random word-description pair
        random_pair = random.choice(word_list)

        word = random_pair['word']
        description = random_pair['description']
        question_id = get_random_id()
        question_text = localized_text(self.translations, "quiz_question", self.bot_language, {"language": language, "description": description})

        return question_text, word, question_id

    async def callback_quiz(self, context: ContextTypes.DEFAULT_TYPE):
        language = self.language_preferences.get(context.job.chat_id)
        random_quiz, correct_answer, question_id = await self._get_random_quiz(self.words_list, language)

        if correct_answer:
            message = await context.bot.send_message(chat_id=context.job.chat_id, text=random_quiz)
        else:
            await context.bot.send_message(chat_id=context.job.chat_id, 
                                           text=localized_text(self.translations, "no_words_specific_language", self.bot_language, {"language": language}))
            return
        
        # Save to history
        self.quiz_history.append({
            'id': question_id,
            'answer': correct_answer,
            'chat_id': context.job.chat_id,
            'attempts': 0,
            'message_ids': [message.message_id]  # Initial valid reply IDs only contains the original message
        })
        
        self.quiz_history = self.quiz_history[-constants.QUIZ_HISTORY_LENGTH:]


    async def start_callback_quiz(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id
        
        if chat_id in self.ongoing_quizzes:
            await context.bot.send_message(chat_id=chat_id, 
                                           text=localized_text(self.translations, "quiz_ongoing", self.bot_language))
            return

        language, interval_time_units = quiz_start_args_parser(context.args)

        word_list = await self.words_list.get_words_by_language(language)

        if not word_list:
            await context.bot.send_message(chat_id=chat_id, 
                                           text=localized_text(self.translations, "no_words_specific_language", self.bot_language, {"language": language}))
            return

        # Store language preference using chat_id as the key
        self.language_preferences[chat_id] = language
        
        await context.bot.send_message(chat_id=chat_id, 
                                       text=localized_text(self.translations, "quiz_started", self.bot_language, {"language": language}))
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
                                           text=localized_text(self.translations, "quiz_stopped", self.bot_language))
        else:
            await context.bot.send_message(chat_id=chat_id, 
                                           text=localized_text(self.translations, "no_ongoing", self.bot_language))


    async def check_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_message = update.message.text  # Get user's message
        chat_id = update.message.chat_id  # Get chat_id
        reply_to_message_id = update.message.reply_to_message.message_id if update.message.reply_to_message else None

        if not reply_to_message_id:  # If the user did not reply to a specific message, you might decide to ignore or handle differently
            await context.bot.send_message(chat_id=chat_id, 
                                           text=localized_text(self.translations, "reply_to_question", self.bot_language))
            return

        # Find the question in history based on reply_to_message_id
        corresponding_question = next((qa for qa in self.quiz_history if qa['chat_id'] == chat_id and reply_to_message_id in qa['message_ids']), None)
        
        if corresponding_question and user_message.lower().strip() == corresponding_question['answer'].lower().strip():
            await context.bot.send_message(chat_id=chat_id, 
                                           text=localized_text(self.translations, "correct_answer", self.bot_language))
        else:
            if corresponding_question:  # If a related question is found
                max_attempts = constants.DEFAULT_MAX_ATTEMPTS
                corresponding_question['attempts'] += 1
                corresponding_question['attempts'] = min(corresponding_question['attempts'], max_attempts)
                remaining_attempts = max_attempts - corresponding_question['attempts']
                
                if remaining_attempts > 0:
                    msg = await context.bot.send_message(chat_id=chat_id, 
                                                         text=localized_text(self.translations, "incorrect_answer", self.bot_language, remaining_attempts))
                    corresponding_question['message_ids'].append(msg.message_id)  # Add new message_id to valid reply ids
                else:
                    await context.bot.send_message(chat_id=chat_id, 
                                                   text=localized_text(self.translations, "incorrect_final_answer", self.bot_language, {"correct_answer": corresponding_question["answer"]}))
            else:
                await context.bot.send_message(chat_id=chat_id, 
                                               text=localized_text(self.translations, "incorrect_outdated", self.bot_language))

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
