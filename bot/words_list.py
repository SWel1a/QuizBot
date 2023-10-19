import json
from utils import get_random_id


class WordsList:
    def __init__(self, filepath):
        self.filepath = filepath

    async def _load_words(self):
        with open(self.filepath, 'r', encoding='utf-8') as file:
            return json.load(file)

    async def _save_words(self, words):
        with open(self.filepath, 'w', encoding='utf-8') as file:
            json.dump(words, file, ensure_ascii=False, indent=4)

    async def add_word(self, json_word_data):
        word_data = json.loads(json_word_data)
        word_data["id"] = self._generate_id()
        words = await self._load_words()
        words.append(word_data)
        await self._save_words(words)

    async def remove_word(self, word_text):
        words = self.get_words_by_text(word_text)
        original_length = len(words)
        if len(words) == original_length:
            return False
        await self._save_words(words)
        return True

    async def get_word_by_text(self, word_text):
        words = await self._load_words()
        for word in words:
            if word['word'].lower() == word_text.lower():
                return word
        return None
    
    async def get_words_by_text(self, word_text=None):
        words = await self._load_words()
        if word_text is not None:
             words = [word for word in words if word['word'].lower() != word_text.lower()]
        return words
    
    async def get_words_by_language(self, language=None):
        words = await self._load_words()
        if language is not None:
            words = [word for word in words if word['language'].lower() == language.lower()]
        return words

    async def get_languages(self):
        words = await self._load_words()
        languages = list(set([word['language'] for word in words]))
        return languages

    def _generate_id(self):
        return get_random_id()
