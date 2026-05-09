from flask import Flask, request
import asyncio
import os
import sqlite3
import smtplib
import uuid
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# =========================================
# CONFIG
# =========================================

TELEGRAM_TOKEN = os.environ.get("8736118266:AAFDKiyE7sEVmYX4GgCr5bU8gc-ijcS7GvI")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")


ADMIN_ID = 5922263974



EMAIL_ADDRESS = "seasjoint@gmail.com"
EMAIL_PASSWORD = "zmtw rnke cymb ljov"

CHAT_STREAMER_FORM = "https://forms.gle/dP6DZwjMGLfP5sSV7"
ACTOR_FORM = "https://forms.gle/tvVRfT4JczP6mHqG7"

# =========================================
# FLASK APP
# =========================================

flask_app = Flask(__name__)

# =========================================
# TELEGRAM APP
# =========================================

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# =========================================
# DATABASE
# =========================================

conn = sqlite3.connect("Seasjoint.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_id TEXT,
    user_id INTEGER,
    username TEXT,
    role TEXT,
    name TEXT,
    age TEXT,
    phone TEXT,
    email TEXT,
    gender TEXT,
    platform TEXT,
    experience TEXT,
    status TEXT,
    timestamp TEXT
)
""")

conn.commit()

# =========================================
# MEMORY STORAGE
# =========================================

user_data_store = {}
waiting_payment = {}

# =========================================
# KEYBOARD
# =========================================

def home_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Chat Support", callback_data="chat")],
        [InlineKeyboardButton("🎬 Streamers", callback_data="streamers")],
        [InlineKeyboardButton("🔥 18+ Actors", callback_data="actors")]
    ])

# =========================================
# START
# =========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    cursor.execute("INSERT OR IGNORE INTO users VALUES (?, ?)",
                   (user.id, user.username or "No Username"))
    conn.commit()

    await update.message.reply_text(
        "👋 Welcome to Seasjoint Agency",
        reply_markup=home_keyboard()
    )

# =========================================
# BUTTONS
# =========================================

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data in ["chat", "streamers", "actors"]:

        role_map = {
            "chat": "CHAT SUPPORT",
            "streamers": "STREAMER",
            "actors": "18+ ACTOR"
        }

        user_data_store[user_id] = {
            "role": role_map[query.data],
            "step": "name"
        }

        await query.edit_message_text("Enter your full name:")

# =========================================
# MESSAGE HANDLER
# =========================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    text = update.message.text

    if user.id not in user_data_store:
        return

    data = user_data_store[user.id]

    if data["step"] == "name":
        data["name"] = text
        data["step"] = "age"
        await update.message.reply_text("Enter age:")

    elif data["step"] == "age":
        data["age"] = text
        data["step"] = "phone"
        await update.message.reply_text("Enter phone:")

    elif data["step"] == "phone":
        data["phone"] = text
        data["step"] = "email"
        await update.message.reply_text("Enter email:")

    elif data["step"] == "email":
        data["email"] = text

        app_id = "APP-" + str(uuid.uuid4())[:8].upper()

        cursor.execute("""
        INSERT INTO applications (
            app_id, user_id, username, role, name, age,
            phone, email, gender, platform, experience,
            status, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            app_id,
            user.id,
            user.username or "No Username",
            data["role"],
            data["name"],
            data["age"],
            data["phone"],
            data["email"],
            "",
            "",
            "",
            "PENDING",
            datetime.now().strftime("%Y-%m-%d %H:%M")
        ))

        conn.commit()

        waiting_payment[user.id] = app_id

        form = ACTOR_FORM if data["role"] == "18+ ACTOR" else CHAT_STREAMER_FORM

        await update.message.reply_text(
            f"✅ Submitted\n\nID: {app_id}\n\nComplete form:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Complete", url=form)]
            ])
        )

        del user_data_store[user.id]

# =========================================
# WEBHOOK ROUTE
# =========================================

@flask_app.route("/webhook", methods=["POST"])
def webhook():

    update = Update.de_json(request.get_json(force=True), app.bot)

    asyncio.run(app.process_update(update))

    return "OK"

# =========================================
# HOME ROUTE
# =========================================

@flask_app.route("/")
def home():
    return "Seasjoint Bot Running 🚀"

# =========================================
# SET WEBHOOK
# =========================================

async def set_webhook():
    await app.bot.set_webhook(url=WEBHOOK_URL)

# =========================================
# MAIN
# =========================================

def main():

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 Starting bot...")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(set_webhook())

    print("✅ Webhook set successfully")

    flask_app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080))
    )

if __name__ == "__main__":
    main()
