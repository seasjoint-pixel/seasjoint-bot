# =========================================
# IMPORTS
# =========================================

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from datetime import datetime
import sqlite3
import smtplib
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# =========================================
# SETTINGS
# =========================================

TELEGRAM_TOKEN ="8736118266:AAFDKiyE7sEVmYX4GgCr5bU8gc-ijcS7GvI"
ADMIN_ID = 5922263974



EMAIL_ADDRESS = "seasjoint@gmail.com"
EMAIL_PASSWORD = "zmtw rnke cymb ljov"

CHAT_STREAMER_FORM = "https://forms.gle/dP6DZwjMGLfP5sSV7"
ACTOR_FORM = "https://forms.gle/tvVRfT4JczP6mHqG7"

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
broadcast_mode = {}

# =========================================
# EMAIL FUNCTION
# =========================================

def send_email(receiver_email, role):
    try:
        if role in ["CHAT SUPPORT", "STREAMER"]:
            subject = "Seasjoint Registration"
            body = "Thank you for registering as Chat Support / Streamer."
        else:
            subject = "18+ Actor Registration"
            body = "Thank you for registering as 18+ Actor."

        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = receiver_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()

    except Exception as e:
        print("Email error:", e)

# =========================================
# KEYBOARD
# =========================================

def home_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Chat Support", callback_data="chat")],
        [InlineKeyboardButton("🎬 Streamers", callback_data="streamers")],
        [InlineKeyboardButton("🔥 18+ Actors", callback_data="actors")],
        [InlineKeyboardButton("💼 My Applications", callback_data="applications")],
    ])

# =========================================
# START COMMAND
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
# BUTTON HANDLER
# =========================================

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    if data == "chat":
        user_data_store[user_id] = {"role": "CHAT SUPPORT", "step": "name"}

    elif data == "streamers":
        user_data_store[user_id] = {"role": "STREAMER", "step": "name"}

    elif data == "actors":
        user_data_store[user_id] = {"role": "18+ ACTOR", "step": "name"}

    elif data == "home":
        await query.edit_message_text("Menu:", reply_markup=home_keyboard())
        return

    elif data == "applications":
        cursor.execute("SELECT app_id, role, status FROM applications WHERE user_id=?",
                       (user_id,))
        rows = cursor.fetchall()

        if not rows:
            await query.edit_message_text("No applications found.", reply_markup=home_keyboard())
            return

        text = "Your Applications:\n\n"
        for r in rows:
            text += f"{r[0]} | {r[1]} | {r[2]}\n"

        await query.edit_message_text(text, reply_markup=home_keyboard())
        return

    await query.edit_message_text("Enter your full name:")

# =========================================
# MESSAGE FLOW
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
        data["step"] = "experience"
        await update.message.reply_text("Enter experience:")

    elif data["step"] == "experience":

        app_id = "APP-" + str(uuid.uuid4())[:8].upper()
        time = datetime.now().strftime("%Y-%m-%d %H:%M")

        cursor.execute("""
        INSERT INTO applications (
            app_id, user_id, username, role, name, age,
            phone, email, gender, platform, experience,
            status, timestamp
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            app_id,
            user.id,
            user.username or "No Username",
            data["role"],
            data.get("name"),
            data.get("age"),
            data.get("phone"),
            data.get("email"),
            "",
            "",
            text,
            "PENDING",
            time
        ))

        conn.commit()
        send_email(data["email"], data["role"])

        await update.message.reply_text(
            f"Application submitted ✅\nID: {app_id}"
        )

        del user_data_store[user.id]

# =========================================
# MAIN RUNNER (IMPORTANT FIX)
# =========================================

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot running...")

    app.run_polling()

# =========================================
# START
# =========================================

if __name__ == "__main__":
    main()
