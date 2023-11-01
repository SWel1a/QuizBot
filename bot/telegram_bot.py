from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, Application
from telegram.constants import ParseMode

import json
import random
from functools import wraps

import constants
from utils import get_random_id, localized_text, quiz_start_args_parser, similarity_percentage, get_closeness_key, \
                  words_eq, preprocess_string, get_hint_text


def authorized(func):
    @wraps(func)
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_handle = update.message.from_user.username
        if '@' + user_handle not in self.allowed_handles:
            await context.bot.send_message(chat_id=update.message.chat_id, 
                                           parse_mode=ParseMode.HTML, 
                                           text=self._localized_text(update.message.chat_id, "unauthorized_command"))
            return
        return await func(self, update, context)
    return wrapper


class TelegramQuizBot:
    def __init__(self, telegram_token, allowed_handles, words_list, translations):
        self.words_list = words_list
        self.translations = translations
        # Telegram bot token
        self.telegram_token = telegram_token

        # Commands and handlers
        self.commands = [
            BotCommand(command="start", description=self._localized_text(None, "start_description")),
            BotCommand(command="stop", description=self._localized_text(None, "stop_description")),
            BotCommand(command="quiz", description=self._localized_text(None, "quiz_description")),
            BotCommand(command="language", description=self._localized_text(None, "language_description")),
            BotCommand(command="list", description=self._localized_text(None, "list_description")),
            BotCommand(command="add_word", description=self._localized_text(None, "add_word_description")),
            BotCommand(command="remove_word", description=self._localized_text(None, "remove_word_description")),
            BotCommand(command="change_description", description=self._localized_text(None, "change_description_description"))
        ]

        self.handlers = [
            CommandHandler('start', self.start_callback_quiz),
            CommandHandler('stop', self.stop_callback_quiz),
            CommandHandler('quiz', self.callback_quiz_on_demand),
            CommandHandler('add_word', self.add_word),
            CommandHandler('remove_word', self.remove_word),
            CommandHandler('change_description', self.change_description),
            CommandHandler('language', self.set_language),
            CommandHandler('list', self.list_words),
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.check_answer),
        ]

        # Custom data structures
        self.allowed_handles = allowed_handles
        self.ongoing_quizzes = {}
        self.language_preferences = {}
        self.bot_language_preferences = {}
        self.quiz_history = []

    def _localize_word_list(self, word_list, chat_id=None):
        if chat_id is None:
            language = constants.DEFAULT_BOT_LANGUAGE
        else:
            language = self.bot_language_preferences.get(chat_id, constants.DEFAULT_BOT_LANGUAGE)
        
        result_list = []
        for word_data in word_list:
            word = word_data.get("word")
            quiz_type = word_data.get("quiz_type")
            descriptions = word_data.get("descriptions", {})

            # Try to get the description in the preferred language
            description = descriptions.get(language)

            # If not found, try the default bot language
            if not description:
                description = descriptions.get(constants.DEFAULT_BOT_LANGUAGE)

            # If still not found, use any available description
            if not description and descriptions:
                description = next(iter(descriptions.values()))

            result_list.append({
                "word": word,
                "description": description,
                "quiz_type": quiz_type
            })
        return result_list
    
    def _localized_text(self, chat_id, key, format_params=None):
        if chat_id is None:
            language = constants.DEFAULT_BOT_LANGUAGE
        else:
            language = self.bot_language_preferences.get(chat_id, constants.DEFAULT_BOT_LANGUAGE)
        return localized_text(self.translations, language, key, format_params)

    async def set_language(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id
        if not context.args:
            # No language provided, inform the user about available languages
            available_languages = ", ".join(self.translations.keys())
            await context.bot.send_message(chat_id=chat_id,
                                           parse_mode=ParseMode.HTML, 
                                           text=self._localized_text(chat_id, "no_bot_language", {"available_languages": available_languages}))
            return

        new_language = preprocess_string(context.args[0])
        if new_language not in list(map(preprocess_string, self.translations)):
            await context.bot.send_message(chat_id=chat_id, 
                                           parse_mode=ParseMode.HTML, 
                                           text=self._localized_text(chat_id, "unsupported_language", {"available_languages": available_languages}))
            return

        self.bot_language_preferences[chat_id] = new_language
        await context.bot.send_message(chat_id=chat_id, 
                                       parse_mode=ParseMode.HTML, 
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
                                           parse_mode=ParseMode.HTML, 
                                           text=self._localized_text(update.effective_chat.id, "provide_word"))
        else:
            word = ' '.join(context.args)
            if action == 'add':
                try:
                    await self.words_list.add_word(word)
                    await context.bot.send_message(chat_id=update.message.chat_id, 
                                                   parse_mode=ParseMode.HTML, 
                                                   text=self._localized_text(update.message.chat_id, "word_added"))
                except json.JSONDecodeError:
                    await context.bot.send_message(chat_id=update.message.chat_id, 
                                                   parse_mode=ParseMode.HTML, 
                                                   text=self._localized_text(update.message.chat_id, "invalid_json_format"))
            elif action == 'remove':
                removed = await self.words_list.remove_word(word)
                if not removed:
                    await context.bot.send_message(chat_id=update.message.chat_id, 
                                                   parse_mode=ParseMode.HTML, 
                                                   text=self._localized_text(update.message.chat_id, "word_not_found", {"word": word}))
                else:
                    await context.bot.send_message(chat_id=update.message.chat_id, 
                                                   parse_mode=ParseMode.HTML, 
                                                   text=self._localized_text(update.message.chat_id, "word_removed", {"word": word}))

    @authorized
    async def change_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await context.bot.send_message(chat_id=update.effective_chat.id, 
                                           parse_mode=ParseMode.HTML, 
                                           text=self._localized_text(update.effective_chat.id, "provide_word"))
        else:
            word = ' '.join(context.args)
            try:
                await self.words_list.update_description(word)
                await context.bot.send_message(chat_id=update.message.chat_id, 
                                               parse_mode=ParseMode.HTML, 
                                               text=self._localized_text(update.message.chat_id, "description_updated"))
            except json.JSONDecodeError:
                await context.bot.send_message(chat_id=update.message.chat_id, 
                                               parse_mode=ParseMode.HTML,
                                               text=self._localized_text(update.message.chat_id, "invalid_json_format"))

    async def callback_quiz(self, context: ContextTypes.DEFAULT_TYPE, chat_id=None):
        if chat_id is None:
            chat_id = context.job.chat_id
        language = self.language_preferences.get(chat_id)
        
        word_list = await self.words_list.get_words_by_language(language)
        word_list = self._localize_word_list(word_list, chat_id)

        if not word_list:
            await context.bot.send_message(chat_id=chat_id, 
                                           parse_mode=ParseMode.HTML, 
                                           text=self._localized_text(chat_id, "no_words_specific_language", {"language": language}))
            return

        # Pick a random word-description pair
        random_pair = random.choice(word_list)

        word = random_pair['word']
        description = random_pair['description']
        quiz_type = random_pair["quiz_type"]

        if quiz_type == "fill":
            msg_key = "quiz_fill_question"
        else:
            msg_key = "quiz_question"

        message = await context.bot.send_message(chat_id=chat_id, 
                                                 parse_mode=ParseMode.HTML, 
                                                 text=self._localized_text(chat_id, msg_key, {"language": language, "description": description}))
        
        # Save to history
        self.quiz_history.append({
            'id': get_random_id(),
            'answer': word,
            'chat_id': chat_id,
            'attempts': 0,
            'hint_count': 0,
            'message_ids': [message.message_id]  # Initial valid reply IDs only contains the original message
        })
        
        self.quiz_history = [msg for chat_id in set(q['chat_id'] for q in self.quiz_history) 
                     for msg in [q for q in self.quiz_history if q['chat_id'] == chat_id][-constants.QUIZ_HISTORY_LENGTH:]]


    async def start_callback_quiz(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id
        
        if chat_id in self.ongoing_quizzes:
            await context.bot.send_message(chat_id=chat_id, 
                                           parse_mode=ParseMode.HTML, 
                                           text=self._localized_text(chat_id, "quiz_ongoing"))
            return

        language, interval_time_units = quiz_start_args_parser(context.args)

        word_list = await self.words_list.get_words_by_language(language)
        word_list = self._localize_word_list(word_list, chat_id)

        if not word_list:
            await context.bot.send_message(chat_id=chat_id, 
                                           parse_mode=ParseMode.HTML, 
                                           text=self._localized_text(chat_id, "no_words_specific_language", {"language": language}))
            return

        # Store language preference using chat_id as the key
        self.language_preferences[chat_id] = language
        
        await context.bot.send_message(chat_id=chat_id, 
                                       parse_mode=ParseMode.HTML, 
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
                                           parse_mode=ParseMode.HTML, 
                                           text=self._localized_text(chat_id, "quiz_stopped"))
        else:
            await context.bot.send_message(chat_id=chat_id, 
                                           parse_mode=ParseMode.HTML, 
                                           text=self._localized_text(chat_id, "no_ongoing"))

    async def callback_quiz_on_demand(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id
        if chat_id not in self.ongoing_quizzes:
            await context.bot.send_message(chat_id=chat_id, 
                                           parse_mode=ParseMode.HTML, 
                                           text=self._localized_text(chat_id, "start_first"))
            return
        await self.callback_quiz(context, chat_id)

    async def check_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_message = update.message.text  # Get user's message
        chat_id = update.message.chat_id  # Get chat_id
        chat_type = update.message.chat.type  # Check if the chat is private (i.e., a one-to-one chat)
        reply_to_message_id = update.message.reply_to_message.message_id if update.message.reply_to_message else None

        # If in a private chat and the user did not reply to a specific message, consider it as a reply to the latest quiz question
        if chat_type == 'private' and not reply_to_message_id and chat_id in self.ongoing_quizzes:
            last_quiz_question = next((qa for qa in reversed(self.quiz_history) if qa['chat_id'] == chat_id), None)
            if last_quiz_question:
                reply_to_message_id = last_quiz_question['message_ids'][-1]

        if not reply_to_message_id:  # If the user did not reply to a specific message, you might decide to ignore or handle differently
            if chat_id in self.ongoing_quizzes:
                await context.bot.send_message(chat_id=chat_id, 
                                            parse_mode=ParseMode.HTML, 
                                            text=self._localized_text(chat_id, "reply_to_question"))
            else:
                await context.bot.send_message(chat_id=chat_id, 
                                            parse_mode=ParseMode.HTML, 
                                            text=self._localized_text(chat_id, "start_first"))
            return

        # Find the question in history based on reply_to_message_id
        corresponding_question = next((qa for qa in self.quiz_history if qa['chat_id'] == chat_id and reply_to_message_id in qa['message_ids']), None)
        similarity = similarity_percentage(user_message, corresponding_question['answer'])
        similarity_msg = self._localized_text(chat_id, get_closeness_key(similarity))

        # Check if the user's reply is "idk" or any word in IDK_WORDS
        if preprocess_string(user_message) in constants.IDK_WORDS:
            if corresponding_question:
                await context.bot.send_message(chat_id=chat_id, 
                                               parse_mode=ParseMode.HTML,
                                               text=self._localized_text(chat_id, "idk_answer", {"correct_answer": corresponding_question["answer"]}))
            else:
                await context.bot.send_message(chat_id=chat_id, 
                                               parse_mode=ParseMode.HTML, 
                                               text=self._localized_text(chat_id, "incorrect_outdated"))
            return

        if corresponding_question and words_eq(user_message, corresponding_question['answer']):
            await context.bot.send_message(chat_id=chat_id, 
                                           parse_mode=ParseMode.HTML, 
                                           text=self._localized_text(chat_id, "correct_answer"))
        else:
            if corresponding_question:  # If a related question is found
                max_attempts = constants.DEFAULT_MAX_ATTEMPTS
                corresponding_question['attempts'] += 1
                corresponding_question['attempts'] = min(corresponding_question['attempts'], max_attempts)
                remaining_attempts = max_attempts - corresponding_question['attempts']
                
                if preprocess_string(user_message) in constants.HINT_WORDS or remaining_attempts <= constants.REMAINING_ATTEMPTS_HINT:
                    corresponding_question['hint_count'] += 1
                    hint_text = get_hint_text(corresponding_question['answer'], corresponding_question['hint_count'])
                    hint_msg = self._localized_text(chat_id, "hint", {"hint_text": hint_text})
                else:
                    hint_text = ""

                if remaining_attempts > 0:
                    text_to_send = self._localized_text(chat_id, "incorrect_answer", {"remaining_attempts": remaining_attempts})
                    text_to_send += "\n" + similarity_msg
                    if hint_text:
                        text_to_send += "\n" + hint_msg
                    msg = await context.bot.send_message(chat_id=chat_id, 
                                                         parse_mode=ParseMode.HTML, 
                                                         text=text_to_send)
                    corresponding_question['message_ids'].append(msg.message_id)  # Add new message_id to valid reply ids
                else:
                    await context.bot.send_message(chat_id=chat_id, 
                                                   parse_mode=ParseMode.HTML, 
                                                   text=self._localized_text(chat_id, "incorrect_final_answer", {"correct_answer": corresponding_question["answer"]}))
            else:
                await context.bot.send_message(chat_id=chat_id, 
                                               parse_mode=ParseMode.HTML, 
                                               text=self._localized_text(chat_id, "incorrect_outdated"))

    async def list_words(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id

        available_groups = await self.words_list.get_languages()

        if not context.args:
            # List only group descriptions without words
            result_text = ""
            for group_language in available_groups:
                group_descriptions = await self.words_list.get_group_description(group_language)

                description = group_descriptions.get(self.bot_language_preferences.get(chat_id, constants.DEFAULT_BOT_LANGUAGE), None)
                if not description:
                    description = group_descriptions.get(constants.DEFAULT_BOT_LANGUAGE, None)
                if not description and group_descriptions:
                    description = next(iter(group_descriptions.values()))

                if description:
                    result_text += f"{group_language} - {description}\n\n"

            if not result_text:
                await context.bot.send_message(chat_id=chat_id, 
                                               parse_mode=ParseMode.HTML, 
                                               text=self._localized_text(chat_id, "list_empty"))
            else:
                await context.bot.send_message(chat_id=chat_id, 
                                               parse_mode=ParseMode.HTML, 
                                               text=result_text)
        else:
            group = preprocess_string(context.args[0])
            if group not in list(map(preprocess_string, available_groups)):
                await context.bot.send_message(chat_id=chat_id, 
                                               parse_mode=ParseMode.HTML, 
                                               text=self._localized_text(chat_id, "list_unknown_group"))
                return

            group_descriptions = await self.words_list.get_group_description(group)

            description = group_descriptions.get(self.bot_language_preferences.get(chat_id, constants.DEFAULT_BOT_LANGUAGE), None)
            if not description:
                description = group_descriptions.get(constants.DEFAULT_BOT_LANGUAGE, None)
            if not description and group_descriptions:
                description = next(iter(group_descriptions.values()))

            word_list = await self.words_list.get_words_by_language(group)
            word_list = self._localize_word_list(word_list, chat_id)

            result_text = ""
            if description:
                result_text += f"{group} - {description}:\n\n"
            else:
                result_text += f"{group}:\n\n"

            result_text += "\n".join([f"{entry['word']}: {entry['description']}" for entry in word_list])

            await context.bot.send_message(chat_id=chat_id, 
                                           parse_mode=ParseMode.HTML, 
                                           text=result_text)


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
