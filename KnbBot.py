import logging
import random
from random import choice
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes,filters, CommandHandler, MessageHandler, Application, CallbackQueryHandler, ConversationHandler
from configparser import ConfigParser
import aiosqlite
import asyncio
import pytz
import time

ADMIN_ID = 1106956385
#states
CHOOSING_DATA, CHOOSING_ACTION, ADMIN = range(3)
#callback_data
PLAY, REGISTER, ADMIN_PANEL = range(3)


async def init_db():
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                wins INTEGER,
                defeats INTEGER,        
                name TEXT,
                phone TEXT,
                conversation_status INTEGER default 0
            )
        """)
        await db.commit()


logging.basicConfig(    
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

config = ConfigParser()

config.read("token.ini")
BOT_TOKEN = config["Telegram"]["tg_token"]



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        keyboard = [
            [InlineKeyboardButton("Играть",callback_data=PLAY), InlineKeyboardButton("Регистрация", callback_data=REGISTER)],
            [InlineKeyboardButton("Админ панель",callback_data=ADMIN_PANEL)]
        ]
    else:
        keyboard = [
        [InlineKeyboardButton("Играть",callback_data=PLAY), InlineKeyboardButton("Регистрация", callback_data=REGISTER)]
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Давай сыграем в камень ножницы бумага?", reply_markup=reply_markup)

async def start_routes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ConversationHandler.END

async def get_move(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ConversationHandler.END
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ConversationHandler.END

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start',start)],
        states={
            CHOOSING_DATA: [CallbackQueryHandler(start_routes)],
            CHOOSING_ACTION: [MessageHandler(filters.Regex("^(Камень|Ножницы|Бумага)$"), get_move)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    application.add_handler(conv_handler)
    application.run_polling()



if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_db())
    main()