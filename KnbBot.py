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
CHOOSING_DATA, CHOOSING_ACTION, ADMIN , RESULT= range(4)
#callback_data
PLAY, REGISTER, ADMIN_PANEL, CONVERSIONS, CANCEL, USERS, SEND_MESS = range(7)


async def init_db():
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                wins INTEGER,
                defeats INTEGER,        
                name TEXT,
                phone TEXT,
                mail TEXT,
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
    if update.callback_query:
        await update.callback_query.edit_message_text("Давай сыграем в камень ножницы бумага?", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Давай сыграем в камень ножницы бумага?", reply_markup=reply_markup)
    return CHOOSING_DATA
async def start_routes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if int(query.data) == PLAY:
        await update.callback_query.edit_message_text("Отлично, давай сыграем")
        return await game(update, context)
    if int(query.data) == REGISTER:
        ConversationHandler.END
    if int(query.data) == ADMIN_PANEL:
        return await admin(update, context)

async def game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    keyboard = [["Камень", "Ножницы"],["Бумага"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.callback_query.message.reply_text("Выберите действие:", reply_markup=reply_markup)
    return CHOOSING_ACTION

async def get_move(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    action = ["Камень", "Ножницы", "Бумага"]
    choose_bot = choice(action)
    result = check_win(message,choose_bot)
    keyboard = [
        [InlineKeyboardButton("Играть снова", callback_data=PLAY)],
         [InlineKeyboardButton("Вернуться назад", callback_data=CANCEL)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"Вы выбрали: {message}\nКомпьютер выбрал: {choose_bot}\nИтог: {result}")
    message_id = await update.message.reply_text("Что делать дальше?", reply_markup=reply_markup)
    context.user_data['last_message_id'] = message_id.message_id
    return RESULT

def check_win(player_move: str, computer_move: str):
    if player_move == computer_move:
        return 'Ничья'
    elif (player_move == 'Камень' and computer_move == 'Ножницы') \
        or (player_move == 'Ножницы' and computer_move == 'Бумага') \
        or (player_move == 'Бумага' and computer_move == 'Камень'):
        return 'Вы победили'
    else:
        return 'Вы проиграли'

async def result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    last_message_id = context.user_data.get('last_message_id')
    if int(query.data) == PLAY:
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=last_message_id)
        return await game(update, context)
    if int(query.data) == CANCEL:
        return await start(update, context)

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Показать пользователей", callback_data=USERS),
        InlineKeyboardButton("Отправить рассылку", callback_data=SEND_MESS)],
        [InlineKeyboardButton("Показать конверсии", callback_data=CONVERSIONS),
         InlineKeyboardButton("Вернуться назад", callback_data=CANCEL)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text("Выберите действие:", reply_markup=reply_markup)
    return ADMIN

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if int(query.data) == USERS:
        await query.edit_message_text("Все пользователи")
        return ConversationHandler.END
    if int(query.data) == SEND_MESS:
        await query.edit_message_text("Введите сообщение")
        return ConversationHandler.END
    if int(query.data) == CONVERSIONS:
        await query.edit_message_text("Конверсия")   
        return ConversationHandler.END
    if int(query.data) == CANCEL:
        return await start(update, context)

   
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return ConversationHandler.END


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start',start)],
        states={
            CHOOSING_DATA: [CallbackQueryHandler(start_routes)],
            CHOOSING_ACTION: [MessageHandler(filters.Regex("^(Камень|Ножницы|Бумага)$"), get_move)],
            RESULT: [CallbackQueryHandler(result)],
            ADMIN: [CallbackQueryHandler(admin_panel)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    application.add_handler(conv_handler)
    
    application.run_polling()



if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_db())
    main()