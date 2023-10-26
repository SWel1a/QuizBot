# 🎉 Telegram Quiz Bot 🎉

Welcome to the **Telegram Quiz Bot** - an engaging and dynamic way to challenge your knowledge on Telegram! Whether you're here to test your intellect or want a friendly competition with your pals, our bot has got you covered. And the best part? It's open source!

🔗 Interact with the bot directly on Telegram: [@This_quiz_bot](https://t.me/This_quiz_bot)

## 🚀 Project Evolution Notice 🚀
The journey of this bot takes a new and exciting turn! 🌟 The project now continues in a fork over at [Flagro's PhriniFluent](https://github.com/Flagro/PhriniFluent). This fork integrates LLM for some seriously cool features, including a dynamic word library generation! 📚🔥

Feel free to hop over and explore the extended capabilities and features that have been introduced. Let's keep pushing the boundaries together!

## 🚀 Features:

- 🌐 **Multi-language Support**: From English to Spanish, and more!
- 🕐 **Timed Quizzes**: Customize intervals between questions.
- ✏️ **Add & Remove Words**: Authorized users can expand or refine the quiz database.
- 📚 **List Words**: Check out the vocabulary for different languages.
- 🌍 **Change Bot Language**: Want the bot to converse in French? No problem!

## 🎖 Getting Started:

**1. Dive Right In**:
Kick things off with `/start English 60` to launch an English quiz with questions every 60 seconds. Customize as you like!

**2. Answering**: 
Reply directly to bot's questions. Stumped by a tough one? Just say `/idk`.

**3. Control**:
Use `/stop` to conclude your quiz or `/quiz` to jump to the next question without waiting.

**4. Modify Database**:
Authorized users, enhance the database with `/add_word` or prune it with `/remove_word`.

**5. Play in Your Language**:
Switch bot's language using `/language` and check words with `/list`.

## 🖥️ Running the Project Locally:

### Installation & Setup:

```bash
git clone https://github.com/SWel1a/QuizBot
cd QuizBot
mv .env-example .env
echo "TELEGRAM_TOKEN=<your telegram token>" >> .env
docker-compose up
```

🎈 That's it! Enjoy the thrill of quizzes right in your Telegram chat. Should you have questions or need some guidance, our developer community is always here to help. Happy quizzing! 🎈
