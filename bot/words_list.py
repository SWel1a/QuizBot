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
        language = word_data["language"]
        
        words = await self._load_words()
        if language not in words:
            words[language] = []
        words[language].append(word_data)
        
        await self._save_words(words)

    async def remove_word(self, word_text):
        words = await self._load_words()
        
        for language, lang_words in words.items():
            words[language] = [word for word in lang_words if word['word'].lower() != word_text.lower()]
        
        await self._save_words(words)
        return True

    async def get_word_by_text(self, word_text):
        words = await self._load_words()
        for lang_words in words.values():
            for word in lang_words:
                if word['word'].lower() == word_text.lower():
                    return word
        return None
    
    async def get_words_by_text(self, word_text=None):
        words = await self._load_words()
        if word_text is not None:
            return {lang: [word for word in lang_words if word['word'].lower() != word_text.lower()] for lang, lang_words in words.items()}
        return words
    
    async def get_words_by_language(self, language=None):
        words = await self._load_words()
        if language is not None:
            return words.get(language.lower(), [])
        return words
