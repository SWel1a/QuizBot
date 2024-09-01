import os
import logging
from dotenv import load_dotenv
from telegram_bot import TelegramQuizBot
from words_list import WordsList
import json


def main():
    # Load environment variables from .env file
    load_dotenv()

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    words = WordsList(filepath="./data/words.json", file_sets_path="./data/word_sets/")
    with open("./data/translations.json", 'r', encoding='utf-8') as f:
        translations = json.load(f)

    bot = TelegramQuizBot(telegram_token=os.getenv('TELEGRAM_TOKEN'),
                          allowed_handles=os.getenv('ALLOWED_HANDLES').split(','),
                          words_list=words,
                          translations=translations)
    
    bot.run()


if __name__ == '__main__':
    main()