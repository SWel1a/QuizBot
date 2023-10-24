DEFAULT_LANGUAGE = 'english_b2'  # Default language for a quiz

DEFAULT_INTERVAL_TIME = 120  # Default time
TIME_UNITS = ['s', 'm', 'h']
DEFAULT_TIME_UNIT = TIME_UNITS[1]

DEFAULT_MAX_ATTEMPTS = 4

QUIZ_HISTORY_LENGTH = 100  # How many quiz history to keep in memory

DEFAULT_BOT_LANGUAGE = 'english'  # Default language for the bot

stopwords = {
    "english": ["i", "me", "my", "we", "us", "you", "he", "she", "it", "they", "this", "that", "and", "but", "or", "is", "are", "was", "were", "be", "have", "has", "do", "does", "did", "a", "an", "the", "on", "in", "at", "by", "for", "with", "of", "to", "from", "up", "down", "as", "at", "before", "after", "over", "under", "no", "not", "only", "own", "so", "than", "too", "very", "can", "will", "just", "should", "now", "to"],
    "spanish": ["de", "la", "que", "el", "en", "y", "a", "los", "las", "un", "una", "su", "lo", "como", "más", "pero", "o", "este", "porque", "con", "sin", "sobre", "también", "me", "hasta", "donde", "quien", "todos", "ni", "contra", "otros", "eso", "ante", "ellos", "este", "mí", "algunos", "qué", "unos", "otro", "otras", "otra", "él", "tanto", "esa"],
    "russian": ["и", "в", "не", "что", "он", "на", "с", "как", "а", "то", "все", "она", "его", "но", "да", "ты", "у", "же", "вы", "за", "по", "только", "ее", "мне"],
    "korean": ["이", "그", "저", "그녀", "우리", "너", "그들", "이것", "저것", "그것", "그리고", "하지만", "또는", "입니다", "있는", "그랬어", "하나", "두", "세", "네", "다섯"]
}

DEFAULT_QUIZ_TYPE = "translate"  # Default quiz type

REMAINING_ATTEMPTS_HINT = 2
HINT_ITERATION_PERCENTAGE = 20

IDK_WORDS = ["idk"]
HINT_WORDS = ["hint"]
