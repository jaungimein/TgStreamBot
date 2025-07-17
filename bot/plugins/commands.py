from hydrogram import filters
from hydrogram.types import Message
from bot import TelegramBot
from bot.config import Telegram
from bot.modules.static import *
from bot.modules.decorators import verify_user
from bot.plugins.files import add_user, authorize_user, is_token_valid, safe_api_call, auto_delete_message

@TelegramBot.on_message(filters.command(['start', 'help']) & filters.private)
@verify_user
async def start_command(_, msg: Message):
    reply = None
    sender_id = msg.from_user.id
    user = msg.from_user
    user_name = user.first_name or user.last_name or (user.username and f"@{user.username}") or "USER"
    add_user(sender_id)
    
    # --- Token-based authorization ---
    if len(msg.command) == 2 and msg.command[1].startswith("token_"):
        if is_token_valid(msg.command[1][6:], sender_id):
            authorize_user(sender_id)
            reply = await safe_api_call(msg.reply_text("✅ You are now authorized to access files for 24 hours."))
            reply = await safe_api_call(TelegramBot.send_message(Telegram.CHANNEL_ID, f"✅ User <b>{user_name}</b> (<code>{user.id}</code>) authorized via token."))
        else:
            reply = await safe_api_call(msg.reply_text("❌ Invalid or expired token. Please get a new link."))
        return
    
    reply = await msg.reply(
        text = WelcomeText % {'first_name': msg.from_user.first_name},
        quote = True
    )
    if reply:
        await auto_delete_message(msg, reply)

@TelegramBot.on_message(filters.command('privacy') & filters.private)
@verify_user
async def privacy_command(_, msg: Message):
    reply = None
    reply = await msg.reply(text=PrivacyText, quote=True, disable_web_page_preview=True)
    if reply:
        await auto_delete_message(msg, reply)

@TelegramBot.on_message(filters.command('log') & filters.chat(Telegram.OWNER_ID))
async def log_command(_, msg: Message):
    await msg.reply_document('event-log.txt', quote=True)

