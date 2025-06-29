from pymongo import MongoClient
from bot.config import Telegram
# MongoDB setup
mongo = MongoClient(Telegram.MONGO_URI)
db = mongo["sharing_bot"]
tokens_col = db["tokens"]
auth_users_col = db["auth_users"]
users_col = db["users"]


