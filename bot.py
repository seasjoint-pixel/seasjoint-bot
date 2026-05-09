from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from datetime import datetime
import sqlite3
import smtplib
import re
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
# STATES
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

            subject = "Seasjoint Agency Registration"

            body = """
🎉 Thank you for registering with Seasjoint Agency — Chat Support & Streamers.

To complete your registration, please ensure you make payment and join the official group accessible after payment confirmation.

📌 Telegram Group: t.me/Seasjoint
📞 WhatsApp Support: 08154429518

We look forward to working with you!
"""

        else:

            subject = "Seasjoint Agency 18+ Actor Registration"

            body = """
🔥 Thank you for registering for the Seasjoint Agency 18+ Actor Program.

Your application has been received successfully.

📞 WhatsApp Support: 08154429518

⚠️ Strictly 18+ only.
"""

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
        print(e)

# =========================================
# MAIN MENU
# =========================================

def home_keyboard():

    return InlineKeyboardMarkup([

        [InlineKeyboardButton(
            "💬 Chat Support",
            callback_data="chat"
        )],

        [InlineKeyboardButton(
            "🎬 Streamers",
            callback_data="streamers"
        )],

        [InlineKeyboardButton(
            "🔥 18+ Actors",
            callback_data="actors"
        )],

        [InlineKeyboardButton(
            "💼 My Applications",
            callback_data="applications"
        )],

        [InlineKeyboardButton(
            "⬅️ Start",
            callback_data="home"
        )]
    ])

# =========================================
# START
# =========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    username = (
        user.username
        if user.username
        else "No Username"
    )

    cursor.execute(
        "INSERT OR IGNORE INTO users VALUES (?, ?)",
        (user.id, username)
    )

    conn.commit()

    await update.message.reply_text(
        "👋 Welcome to Seasjoint Agency\n\n"
        "Choose a category below:",
        reply_markup=home_keyboard()
    )

# =========================================
# BUTTONS
# =========================================

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = query.from_user.id

    # =====================================
    # HOME
    # =====================================

    if data == "home":

        await query.edit_message_text(
            "👋 Welcome back to Seasjoint Agency",
            reply_markup=home_keyboard()
        )

    # =====================================
    # CHAT
    # =====================================

    elif data == "chat":

        user_data_store[user_id] = {
            "role": "CHAT SUPPORT",
            "step": "name"
        }

        await query.edit_message_text(
            "📝 CHAT SUPPORT APPLICATION\n\n"
            "Enter your full name:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="home"
                )]
            ])
        )

    # =====================================
    # STREAMER
    # =====================================

    elif data == "streamers":

        user_data_store[user_id] = {
            "role": "STREAMER",
            "step": "name"
        }

        await query.edit_message_text(
            "📝 STREAMER APPLICATION\n\n"
            "Enter your full name:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="home"
                )]
            ])
        )

    # =====================================
    # ACTOR
    # =====================================

    elif data == "actors":

        user_data_store[user_id] = {
            "role": "18+ ACTOR",
            "step": "name"
        }

        await query.edit_message_text(
            "🔥 18+ ACTOR APPLICATION\n\n"
            "Enter your full name:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="home"
                )]
            ])
        )

    # =====================================
    # APPLICATIONS
    # =====================================

    elif data == "applications":

        cursor.execute("""
        SELECT app_id, role, status
        FROM applications
        WHERE user_id=?
        """, (user_id,))

        rows = cursor.fetchall()

        if not rows:

            await query.edit_message_text(
                "📂 No applications found.",
                reply_markup=home_keyboard()
            )
            return

        text = "📂 YOUR APPLICATIONS\n\n"

        for app_id, role, status in rows:

            text += (
                f"🆔 {app_id}\n"
                f"💼 {role}\n"
                f"📌 {status}\n\n"
            )

        await query.edit_message_text(
            text,
            reply_markup=home_keyboard()
        )

    # =====================================
    # APPROVE
    # =====================================

    elif data.startswith("approve_"):

        app_id = data.split("_")[1]

        cursor.execute("""
        UPDATE applications
        SET status='APPROVED'
        WHERE app_id=?
        """, (app_id,))

        conn.commit()

        cursor.execute("""
        SELECT user_id
        FROM applications
        WHERE app_id=?
        """, (app_id,))

        user = cursor.fetchone()

        if user:

            await context.bot.send_message(
                chat_id=user[0],
                text=(
                    "🎉 Congratulations!\n\n"
                    "Your application has been approved."
                )
            )

        await query.edit_message_text(
            f"✅ Application {app_id} approved."
        )

    # =====================================
    # REJECT
    # =====================================

    elif data.startswith("reject_"):

        app_id = data.split("_")[1]

        cursor.execute("""
        UPDATE applications
        SET status='REJECTED'
        WHERE app_id=?
        """, (app_id,))

        conn.commit()

        cursor.execute("""
        SELECT user_id
        FROM applications
        WHERE app_id=?
        """, (app_id,))

        user = cursor.fetchone()

        if user:

            await context.bot.send_message(
                chat_id=user[0],
                text=(
                    "❌ Sorry.\n\n"
                    "Your application was not approved."
                )
            )

        await query.edit_message_text(
            f"❌ Application {app_id} rejected."
        )

# =========================================
# HANDLE FORMS
# =========================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    text = update.message.text or ""

    # =====================================
    # BROADCAST MODE
    # =====================================

    if (
        user.id == ADMIN_ID
        and user.id in broadcast_mode
    ):

        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()

        sent = 0

        for u in users:

            try:

                await context.bot.send_message(
                    chat_id=u[0],
                    text=text
                )

                sent += 1

            except:
                pass

        del broadcast_mode[user.id]

        await update.message.reply_text(
            f"✅ Broadcast sent to {sent} users."
        )

        return

    # =====================================
    # FORM FLOW
    # =====================================

    if user.id not in user_data_store:
        return

    data = user_data_store[user.id]

    # NAME

    if data["step"] == "name":

        data["name"] = text
        data["step"] = "age"

        await update.message.reply_text(
            "Enter your age:"
        )

    # AGE

    elif data["step"] == "age":

        data["age"] = text
        data["step"] = "phone"

        await update.message.reply_text(
            "Enter your phone number:"
        )

    # PHONE

    elif data["step"] == "phone":

        data["phone"] = text
        data["step"] = "email"

        await update.message.reply_text(
            "Enter your email:"
        )

    # EMAIL

    elif data["step"] == "email":

        data["email"] = text

        role = data["role"]

        if role == "18+ ACTOR":

            data["step"] = "gender"

            await update.message.reply_text(
                "Enter your gender:"
            )

        elif role == "STREAMER":

            data["step"] = "platform"

            await update.message.reply_text(
                "Enter your streaming platform:"
            )

        else:

            data["step"] = "experience"

            await update.message.reply_text(
                "Enter your experience:"
            )

    # GENDER

    elif data["step"] == "gender":

        data["gender"] = text
        data["step"] = "experience"

        await update.message.reply_text(
            "Enter your experience:"
        )

    # PLATFORM

    elif data["step"] == "platform":

        data["platform"] = text
        data["step"] = "experience"

        await update.message.reply_text(
            "Enter your experience:"
        )

    # EXPERIENCE

    elif data["step"] == "experience":

        data["experience"] = text

        app_id = (
            "APP-" +
            str(uuid.uuid4())[:8].upper()
        )

        timestamp = datetime.now().strftime(
            "%Y-%m-%d %H:%M"
        )

        username = (
            user.username
            if user.username
            else "No Username"
        )

        cursor.execute("""
        INSERT INTO applications (
            app_id,
            user_id,
            username,
            role,
            name,
            age,
            phone,
            email,
            gender,
            platform,
            experience,
            status,
            timestamp
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (

            app_id,
            user.id,
            username,
            data["role"],
            data.get("name"),
            data.get("age"),
            data.get("phone"),
            data.get("email"),
            data.get("gender"),
            data.get("platform"),
            data.get("experience"),
            "PENDING",
            timestamp
        ))

        conn.commit()

        send_email(
            data["email"],
            data["role"]
        )

        waiting_payment[user.id] = app_id

        # PAYMENT LINK

        if data["role"] == "18+ ACTOR":
            form_link = ACTOR_FORM
        else:
            form_link = CHAT_STREAMER_FORM




        keyboard = InlineKeyboardMarkup([

            [InlineKeyboardButton(
                "💳 Complete Registration",
                url=form_link
            )],

            [InlineKeyboardButton(
                "⬅️ Back",
                callback_data="home"
            )]
        ])

        await update.message.reply_text(
            f"✅ Application Submitted\n\n"
            f"🆔 {app_id}\n\n"
            "Complete the registration form below.\n"
            "After payment, send a screenshot here.",
            reply_markup=keyboard
        )

        # ADMIN MESSAGE

        admin_keyboard = InlineKeyboardMarkup([

            [
                InlineKeyboardButton(
                    "✅ Approve",
                    callback_data=f"approve_{app_id}"
                ),

                InlineKeyboardButton(
                    "❌ Reject",
                    callback_data=f"reject_{app_id}"
                )
            ]
        ])

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"📥 NEW APPLICATION\n\n"
                f"🆔 {app_id}\n"
                f"👤 @{username}\n"
                f"💼 {data['role']}\n"
                f"📧 {data['email']}"
            ),
            reply_markup=admin_keyboard
        )

        del user_data_store[user.id]

# =========================================
# PAYMENT SCREENSHOT
# =========================================

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    if user.id not in waiting_payment:
        return

    app_id = waiting_payment[user.id]

    photo = update.message.photo[-1].file_id

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo,
        caption=(
            f"💳 PAYMENT PROOF\n\n"
            f"🆔 {app_id}\n"
            f"👤 {user.username}"
        )
    )

    await update.message.reply_text(
        "✅ Payment proof received.\n\n"
        "Your application is under review."
    )

    del waiting_payment[user.id]

# =========================================
# BROADCAST COMMAND
# =========================================

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    broadcast_mode[update.effective_user.id] = True

    await update.message.reply_text(
        "📢 Send the message you want to broadcast."
    )

# =========================================
# ADMIN PANEL
# =========================================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM applications")
    total_apps = cursor.fetchone()[0]

    await update.message.reply_text(
        f"👑 ADMIN PANEL\n\n"
        f"👥 Users: {total_users}\n"
        f"📂 Applications: {total_apps}"
    )

# =========================================
# MAIN
# =========================================

app = (
    ApplicationBuilder()
    .token(TELEGRAM_TOKEN)
    .connect_timeout(30)
    .read_timeout(30)
    .write_timeout(30)
    .pool_timeout(30)
    .build()
    )

app.add_handler(CommandHandler(
    "start",
    start
))

app.add_handler(CommandHandler(
    "admin",
    admin
))

app.add_handler(CommandHandler(
    "broadcast",
    broadcast
))

app.add_handler(CallbackQueryHandler(
    button_click
))

app.add_handler(MessageHandler(
    filters.TEXT & ~filters.COMMAND,
    handle_message
))

app.add_handler(MessageHandler(
    filters.PHOTO,
    handle_photo
))

print("✅ Seasjoint Agency Bot Running...")

app.run_polling(drop_pending_updates=True)
    
    
