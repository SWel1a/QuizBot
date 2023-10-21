Telegram Quiz Bot
The Telegram Quiz Bot is an open-source bot that lets you create and participate in quizzes on Telegram. It provides a fun and interactive way to test your knowledge or challenge your friends. You can use the bot to start timed quizzes, add new words to the quiz database, remove words, change the bot's language, and list the available words in different language groups.

Table of Contents
Getting Started
Commands
Adding Words
Changing Bot Language
Listing Words

Getting Started
To use the Telegram Quiz Bot, you need to interact with it through a Telegram chat. Follow these simple steps to get started:

Access the Bot: You can access the bot by clicking on the following link: Telegram Quiz Bot. Make sure you're logged in to your Telegram account.

Start a Quiz: Use the /start command to initiate a quiz. You can specify the language for the quiz and the time interval between questions. 
For example:
/start English 60
This command will start an English language quiz with a 60-second interval between questions. You can customize the language and interval as per your preferences.

Answer Questions: The bot will start asking questions based on the chosen language. Reply to the questions with your answers. If you're unsure of the answer, you can use /idk to indicate that you don't know the answer.

Stop the Quiz: To stop an ongoing quiz, use the /stop command. This will end the quiz and stop further questions.

Force the Next Question: If you want to skip to the next question in the quiz, use the /quiz command. This is handy when you're ready for the next challenge.

Add Words (Authorized Users Only): If you're an authorized user, you can add new words to the quiz database using the /add_word command.
For example:
/add_word apple A fruit that grows on trees.
This command will add the word "apple" with the description provided.

Remove Words (Authorized Users Only): Authorized users can also remove words from the database using the /remove_word command.
For example:
/remove_word apple
This command will remove the word "apple" from the database.

Change Bot Language: You can change the bot's language preference using the /language command. Specify the desired language, and the bot will respond in that language.

List Words: Use the /list command to display the words available in a specific language group.
For example:
/list English
This command will list all the English words in the database.

Commands
Here's a list of commands you can use with the Telegram Quiz Bot:

/start [Language] [Interval]: Start a quiz in the specified language with a given interval between questions.
/stop: Stop the ongoing quiz.
/quiz: Force the next quiz question.
/add_word [Word] [Description]: Add a new word to the quiz database (Authorized Users Only).
/remove_word [Word]: Remove a word from the quiz database (Authorized Users Only).
/language [Language]: Change the bot's language preference.
/list [Language]: List the words available in a specific language group.

Adding Words
Authorized users can add new words to the quiz database using the /add_word command. 
To add a word, follow this format:
/add_word [Word] [Description]
For example:
/add_word apple A fruit that grows on trees.
This will add the word "apple" to the database with the provided description. Please ensure that you format your input correctly.

Changing Bot Language
You can change the bot's language preference using the /language command. Specify the desired language, and the bot will respond in that language.
/language [Language]
For example:
/language Spanish
This will change the bot's language to Spanish, and it will respond in Spanish for subsequent interactions.

Listing Words
You can list the words available in a specific language group using the /list command. Provide the language group you want to list.
/list [Language]
For example:
/list French
This will display a list of all the French words available in the quiz database.

Enjoy the Telegram Quiz Bot and have fun challenging your knowledge! If you have any questions or need assistance, feel free to reach out to the bot's developers.