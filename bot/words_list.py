import json
import constants
from utils import preprocess_string

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
        words_data = json.loads(json_word_data)
        if isinstance(words_data, list):
            # Mass word addition
            await self._add_multiple_words(words_data)
        elif isinstance(words_data, dict):
            # Single word addition
            await self._add_single_word(words_data)
        else:
            raise ValueError("Invalid input format")

    async def _add_single_word(self, word_data):
        language = word_data["language"]
        if "quiz_tyoe" in word_data:
            quiz_type = word_data["quiz_type"]
        else:
            quiz_type = constants.DEFAULT_QUIZ_TYPE
        words = await self._load_words()

        if language not in words:
            words[language] = {"description": {}, "words": []}

        new_word = {
            "word": word_data["word"],
            "descriptions": word_data["descriptions"],
            "quiz_type": quiz_type
        }

        words[language]["words"].append(new_word)
        await self._save_words(words)

    async def _add_multiple_words(self, words_data):
        for word_data in words_data:
            await self._add_single_word(word_data)

    async def remove_word(self, word_text):
        words = await self._load_words()
        preprocessed_text = preprocess_string(word_text)

        for _, lang_data in words.items():
            lang_data["words"] = [word for word in lang_data["words"] if preprocess_string(word['word']) != preprocessed_text]

        await self._save_words(words)
        return True

    async def get_word_by_text(self, word_text):
        preprocessed_text = preprocess_string(word_text)
        words = await self._load_words()

        for lang_data in words.values():
            for word in lang_data["words"]:
                if preprocess_string(word['word']) == preprocessed_text:
                    return word
        return None

    async def get_words_by_text(self, word_text=None):
        words = await self._load_words()
        if word_text is not None:
            preprocessed_text = preprocess_string(word_text)
            for _, lang_data in words.items():
                lang_data["words"] = [word for word in lang_data["words"] if preprocess_string(word['word']) != preprocessed_text]
        return words

    async def get_words_by_language(self, language=None):
        words = await self._load_words()
        if language is not None:
            preprocessed_language = preprocess_string(language)
            for lang, lang_data in words.items():
                if preprocess_string(lang) == preprocessed_language:
                    return lang_data["words"]
            return []
        return [word for lang_data in words.values() for word in lang_data["words"]]

    async def get_languages(self):
        words = await self._load_words()
        return list(words.keys())

    async def get_group_description(self, language):
        words = await self._load_words()
        preprocessed_language = preprocess_string(language)
        group_data = None
        for lang, lang_data in words.items():
            if preprocess_string(lang) == preprocessed_language:
                group_data = lang_data
                break
        if group_data:
            descriptions = group_data.get("description", {})
            return descriptions
        return None

    async def update_description(self, json_word_data):
        word_data = json.loads(json_word_data)
        language = word_data["language"]
        description = word_data["descriptions"]
        words = await self._load_words()
        preprocessed_language = preprocess_string(language)
        group_data = None
        for lang, lang_data in words.items():
            if preprocess_string(lang) == preprocessed_language:
                group_data = lang_data
                break
        if group_data:
            group_data["description"] = description
            await self._save_words(words)
            return True
        return False
