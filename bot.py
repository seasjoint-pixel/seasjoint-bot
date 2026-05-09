import logging
import sqlite3
import uuid
from datetime import datetime
import smtplib

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================
# CONFIG
# =========================
TELEGRAM_TOKEN = "8736118266:AAFDKiyE7sEVmYX4GgCr5bU8gc-ijcS7GvI"
ADMIN_ID = 5922263974

EMAIL_ADDRESS = "seasjoint@gmail.com"
EMAIL_PASSWORD = "zmtw rnke cymb ljov"

CHAT_STREAMER_FORM = "https://forms.gle/dP6DZwjMGLfP5sSV7"
ACTOR_FORM = "https://forms.gle/tvVRfT4JczP6mHqG7"

# =========================
# LOGGING
# =========================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# =========================
# DB
# =========================
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

# =========================
# MEMORY
# =========================
user_data = {}
waiting_payment = {}

# =========================
# KEYBOARD
# =========================
def home_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Chat Support", callback_data="chat")],
        [InlineKeyboardButton("🎬 Streamers", callback_data="streamers")],
        [InlineKeyboardButton("🔥 18+ Actors", callback_data="actors")],
    ])

# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    cursor.execute(
        "INSERT OR IGNORE INTO users VALUES (?, ?)",
        (user.id, user.username or "No Username")
    )
    conn.commit()

    await update.message.reply_text(
        "👋 Welcome to Seasjoint Agency",
        reply_markup=home_keyboard()
    )

# =========================
# BUTTONS
# =========================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data in ["chat", "streamers", "actors"]:
        role_map = {
            "chat": "CHAT SUPPORT",
            "streamers": "STREAMER",
            "actors": "18+ ACTOR"
        }

        user_data[user_id] = {
            "role": role_map[query.data],
            "step": "name"
        }

        await query.edit_message_text("Enter your full name:")

# =========================
# MESSAGE FLOW
# =========================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    if user.id not in user_data:
        return

    data = user_data[user.id]

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

        app_id = "APP-" + str(uuid.uuid4())[:8]

        cursor.execute("""
            INSERT INTO applications VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
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

        link = ACTOR_FORM if data["role"] == "18+ ACTOR" else CHAT_STREAMER_FORM

        await update.message.reply_text(
            f"✅ Submitted {app_id}\nComplete form:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Complete", url=link)]
            ])
        )

        del user_data[user.id]

# =========================
# MAIN START (FIXED)
# =========================
def main():
    print("Bot running...")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # 🚨 IMPORTANT FIX:
    app.run_polling()

# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    main()
