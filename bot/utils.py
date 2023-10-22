import logging
import uuid
import string

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
        if key in translations['en']:
            translated_text = translations['en'][key]
        else:
            logging.warning(f"No english definition found for key '{key}' in translations.json")
            # return key as text
            return key

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
    interval_time = constants.DEFAULT_INTERVAL_TIME  # Default time
    
    # Handling arguments
    if len(args_list) >= 1:
        first_arg = args_list[0]
        if first_arg.isnumeric():
            interval_time = str(first_arg)
        else:
            language = first_arg
            if len(args_list) > 1 and args_list[1].isnumeric():
                interval_time = str(args_list[1])
    
    if constants.DEFAULT_TIME_UNIT == 'm':
        interval_time_units = int(interval_time) * 60
    elif constants.DEFAULT_TIME_UNIT == 'h':
        interval_time_units = int(interval_time) * 60 * 60
    else:
        interval_time_units = int(interval_time)
    language = language.lower().strip()
    
    return language, interval_time_units


def preprocess_string(text: str) -> str:
    # Remove punctuation
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))

    # Remove stopwords
    for _, stopwords in constants.stopwords.items():
        text = ' '.join([word for word in text.split() if word not in stopwords])
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
