import logging
import uuid
import string
import random
import re

import constants


def get_random_id():
    return str(uuid.uuid4())  # Returns a random UUID as a string


def localized_text(translations, bot_language, key, format_params=None):
    """
    Return translated text for a key in specified bot_language.
    Keys and translations can be found in the translations.json.
    """
    try:
        translated_text = translations[bot_language][key]
    except KeyError:
        logging.warning(f"No translation available for bot_language code '{bot_language}' and key '{key}'")
        # Fallback to English if the translation is not available
        if key in translations['english']:
            translated_text = translations['english'][key]
        else:
            logging.warning(f"No english definition found for key '{key}' in translations.json")
            # return key as text
            return key
        
    if type(translated_text) == list:
        # Select a random text from the list
        translated_text = random.choice(translated_text)

    # Format the translated text with provided parameters if any
    if format_params:
        try:
            return translated_text.format(**format_params)
        except KeyError as e:
            logging.warning(f"Parameter '{e}' not provided for key '{key}' formatting")
            return translated_text

    return translated_text



def quiz_start_args_parser(args_list):
    # Default values
    language = constants.DEFAULT_LANGUAGE  # Default language
    
    # Handling arguments
    language_parts = []
    time_str = ""

    for arg in args_list:
        if re.match(r"^\d+[smh]$", arg):  # Check for time values like "100s", "100m", "100h"
            time_str = arg
        else:
            language_parts.append(arg)

    if language_parts:
        language = " ".join(language_parts).lower().strip()

    if not time_str:
        time_str = str(constants.DEFAULT_INTERVAL_TIME) + constants.DEFAULT_TIME_UNIT
    if time_str[-1] not in constants.TIME_UNITS:
        time_str += constants.DEFAULT_TIME_UNIT
    if time_str[-1] == 's':
        interval_time_units = int(time_str[:-1])  # Remove the 's' and convert to seconds
    elif time_str[-1] == 'm':
        interval_time_units = int(time_str[:-1]) * 60  # Remove the 'm' and convert to minutes
    elif time_str[-1] == 'h':
        interval_time_units = int(time_str[:-1]) * 60 * 60  # Remove the 'h' and convert to hours

    return language, interval_time_units


def preprocess_string(text: str) -> str:
    text = text.lower()
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))

    # If the text is a single word, return it as it is
    if len(text.split()) == 1:
        return text

    # Remove stopwords
    for _, stopwords in constants.stopwords.items():
        text = ' '.join([word for word in text.split() if word not in stopwords])
    text = text.replace("_", "")
    text = text.replace(" ", "")
    return text


def words_eq(s1, s2, preprocess=True) -> bool:
    if preprocess:
        s1 = preprocess_string(s1)
        s2 = preprocess_string(s2)
    return s1 == s2


def levenshtein_distance(s1: str, s2: str) -> int:
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    # len(s1) >= len(s2)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1 
            deletions = current_row[j] + 1       
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def similarity_percentage(s1: str, s2: str, preprocess=True) -> float:
    if preprocess:
        s1 = preprocess_string(s1)
        s2 = preprocess_string(s2)
    distance = levenshtein_distance(s1, s2)
    max_len = max(len(s1), len(s2))
    similarity = (1 - distance / max_len) * 100
    return similarity


def get_closeness_key(similarity: float) -> str:
    if similarity > 90:
        return "closeness90"
    elif similarity > 80:
        return "closeness80"
    elif similarity > 70:
        return "closeness70"
    elif similarity > 50:
        return "closeness50"
    else:
        return "closeness0"
    

def get_hint_text(text: str, multiplier: int) -> str:
    percentage_to_give = constants.HINT_ITERATION_PERCENTAGE * multiplier
    hint_text = text[:min(len(text), max(int(len(text) * percentage_to_give / 100), 1))]
    return hint_text
