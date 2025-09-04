from os import environ as env
from dotenv import load_dotenv

load_dotenv('.env', override=True)

class Telegram:
    API_ID = int(env.get("TELEGRAM_API_ID"))
    API_HASH = env.get("TELEGRAM_API_HASH")
    OWNER_ID = int(env.get("OWNER_ID"))
    ALLOWED_USER_IDS = env.get("ALLOWED_USER_IDS").split()
    BOT_USERNAME = env.get("TELEGRAM_BOT_USERNAME")
    BOT_TOKEN = env.get("TELEGRAM_BOT_TOKEN")
    CHANNEL_ID = int(env.get("TELEGRAM_CHANNEL_ID"))
    SECRET_CODE_LENGTH = int(env.get("SECRET_CODE_LENGTH", 24))
    SHORTERNER_URL = str (env.get("SHORTERNER_URL"))
    URLSHORTX_API_TOKEN = str (env.get("URLSHORTX_API_TOKEN"))
    MONGO_URI = str (env.get("MONGO_URI"))
class Server:
    BASE_URL = env.get("BASE_URL")
    BIND_ADDRESS = env.get("BIND_ADDRESS", "0.0.0.0")
    PORT = int(env.get("PORT", 8080))

# LOGGING CONFIGURATION
LOGGER_CONFIG_JSON = {
    'version': 1,
    'formatters': {
        'default': {
            'format': '[%(asctime)s][%(name)s][%(levelname)s] -> %(message)s',
            'datefmt': '%d/%m/%Y %H:%M:%S'
        },
    },
    'handlers': {
        'file_handler': {
            'class': 'logging.FileHandler',
            'filename': 'event-log.txt',
            'formatter': 'default'
        },
        'stream_handler': {
            'class': 'logging.StreamHandler',
            'formatter': 'default'
        }
    },
    'loggers': {
        'uvicorn': {
            'level': 'WARNING',
            'handlers': ['file_handler', 'stream_handler']
        },
        'uvicorn.error': {
            'level': 'WARNING',
            'handlers': ['file_handler', 'stream_handler']
        },
        'bot': {
            'level': 'WARNING',
            'handlers': ['file_handler', 'stream_handler']
        },
        'hydrogram': {
            'level': 'WARNING',
            'handlers': ['file_handler', 'stream_handler']
        }
    }
}
