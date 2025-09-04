import uuid
import aiohttp
import asyncio
import base64
import requests
from hydrogram import filters
from hydrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from hydrogram.errors import FloodWait
from secrets import token_hex
from bot import TelegramBot, logger
from bot.config import Telegram, Server
from bot.modules.decorators import verify_user
from bot.modules.static import *
from datetime import datetime, timezone, timedelta
from bot.database.db import *
from collections import defaultdict

user_data = {}
TOKEN_VALIDITY_SECONDS = 24 * 60 * 60  # 24 hours
MAX_FILES_PER_SESSION = 10   
user_file_count = defaultdict(int)

@TelegramBot.on_message(
    filters.private
    & (
        filters.document
        | filters.video
        | filters.video_note
        | filters.audio
        | filters.voice
        | filters.photo
    )
)
@verify_user
async def handle_user_file(_, msg: Message):
    sender_id = msg.from_user.id
    secret_code = token_hex(Telegram.SECRET_CODE_LENGTH)
    file = await msg.copy(
        chat_id=Telegram.CHANNEL_ID,
        caption=f'||{secret_code}/{sender_id}||'
    )
    file_id = file.id
    dl_link = f'{Server.BASE_URL}/dl/{file_id}?code={secret_code}'

    if (msg.document and 'video' in msg.document.mime_type) or msg.video:
        # Check if user is authorized
        if sender_id != Telegram.OWNER_ID and not is_user_authorized(sender_id):
            now = datetime.now(timezone.utc)
            token_doc = tokens_col.find_one({
                    "user_id": sender_id,
                    "expiry": {"$gt": now}
                })
            token_id = token_doc["token_id"] if token_doc else generate_token(sender_id)
            short_link = shorten_url(get_token_link(token_id, Telegram.BOT_USERNAME))
            reply = await safe_api_call(msg.reply_text(
                "❌ You are not authorized\n"
                "Please use this link to get access for 24 hours:",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Get Access Link", url=short_link)]]
                )
            ))
            await auto_delete_message(msg, reply)
            return 
            
        # Limit file access per session
        if sender_id != Telegram.OWNER_ID and user_file_count[sender_id] >= MAX_FILES_PER_SESSION:
            await safe_api_call(msg.reply_text("❌ You have reached the maximum of 10 files per session."))
            return

        stream_link = f'{Server.BASE_URL}/stream/{file_id}?code={secret_code}'
        await msg.reply(
            text=MediaLinksText % {'dl_link': dl_link, 'stream_link': stream_link},
            quote=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton('Download', url=dl_link),
                        InlineKeyboardButton('Stream', url=stream_link)
                    ],
                    [
                        InlineKeyboardButton('Revoke', callback_data=f'rm_{file_id}_{secret_code}')
                    ]
                ]
            )
        )
    else:
        await msg.reply(
            text=FileLinksText % {'dl_link': dl_link},
            quote=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton('Download', url=dl_link),
                        InlineKeyboardButton('Revoke', callback_data=f'rm_{file_id}_{secret_code}')
                    ]
                ]
            )
        )
    user_file_count[sender_id] += 1
    await msg.delete()

async def auto_delete_message(user_message, bot_message):
    try:
        await user_message.delete()
        await asyncio.sleep(60)
        await bot_message.delete()
    except Exception as e:
        print(f"{e}")


# =========================
# Token Utilities
# =========================

def add_user(user_id):
    users_col.update_one(
        {"user_id": user_id},
        {"$set": {"user_id": user_id}},
        upsert=True
    )

def authorize_user(user_id):
    """Authorize a user for 24 hours."""
    expiry = datetime.now(timezone.utc) + timedelta(seconds=TOKEN_VALIDITY_SECONDS)
    auth_users_col.update_one(
        {"user_id": user_id},
        {"$set": {"expiry": expiry}},
        upsert=True
    )

def is_user_authorized(user_id):
    """Check if a user is authorized."""
    doc = auth_users_col.find_one({"user_id": user_id})
    if not doc:
        return False
    expiry = doc["expiry"]
    if isinstance(expiry, str):
        try:
            expiry = datetime.fromisoformat(expiry)
        except Exception:
            return False
    if isinstance(expiry, datetime) and expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)
    if expiry < datetime.now(timezone.utc):
        return False
    return True

def generate_token(user_id):
    """Generate a new access token for a user."""
    token_id = str(uuid.uuid4())
    expiry = datetime.now(timezone.utc) + timedelta(seconds=TOKEN_VALIDITY_SECONDS)
    tokens_col.insert_one({
        "token_id": token_id,
        "user_id": user_id,
        "expiry": expiry,
        "created_at": datetime.now(timezone.utc)
    })
    return token_id

def is_token_valid(token_id, user_id):
    """Check if a token is valid for a user."""
    token = tokens_col.find_one({"token_id": token_id, "user_id": user_id})
    if not token:
        return False
    expiry = token["expiry"]
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)
    if expiry < datetime.now(timezone.utc):
        tokens_col.delete_one({"_id": token["_id"]})
        return False
    return True

def get_token_link(token_id, bot_username):
    """Generate a Telegram deep link for a token."""
    return f"https://telegram.dog/{bot_username}?start=token_{token_id}"

def shorten_url(long_url):
    """
    Shorten a URL using the configured shortener service.
    Returns the original URL if shortening fails.
    """
    try:
        resp = requests.get(
            f"https://{Telegram.SHORTERNER_URL}/api?api={Telegram.URLSHORTX_API_TOKEN}&url={long_url}",
            timeout=5
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "success" and data.get("shortenedUrl"):
                return data["shortenedUrl"]
        logger.warning(f"Failed to shorten URL, status code: {resp.status_code}")
        return long_url
    except Exception as e:
        logger.error(f"Exception while shortening URL: {e}")
        return long_url
    
async def safe_api_call(coro):
    """Utility wrapper to add delay before every bot API call."""
    while True:
        try:
            return await coro
        except FloodWait as e:
            print(f"FloodWait: Sleeping for {e.value} seconds")
            await asyncio.sleep(e.value)
        except Exception:
            raise