import logging
import uuid

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
