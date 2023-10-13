import os
import logging
from dotenv import load_dotenv
from telegram_bot import TelegramQuizBot
from words_list import WordsList


def main():
    # Load environment variables from .env file
    load_dotenv()

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    words = WordsList(filepath="./data/words.json")

    bot = TelegramQuizBot(telegram_token=os.getenv('TELEGRAM_TOKEN'),
                          allowed_handles=os.getenv('ALLOWED_HANDLES').split(','),
                          words_list=words)
    
    bot.run()


if __name__ == '__main__':
    main()