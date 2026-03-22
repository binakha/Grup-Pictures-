import os
import logging
import telebot
from telebot import types

# ─────────────────────────────────────────────
# Logging Setup
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Bot Initialization
# ─────────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
bot = telebot.TeleBot(BOT_TOKEN)

# ─────────────────────────────────────────────
# Passwords
# ─────────────────────────────────────────────
MAIN_PASSWORD = "NYTGrupPIC"
SAAFE_PASSWORD = "A1S1H1A1"

# ─────────────────────────────────────────────
# Google Drive ZIP Links  ← Paste your links here
# ─────────────────────────────────────────────
LINK_GROUP_PICTURES  = "[drive.google.com](https://drive.google.com/your-group-zip-link)"
LINK_SAAFE_PERSONAL  = "[drive.google.com](https://drive.google.com/your-saafe-personal-zip-link)"
LINK_SAAFE_SYLHET    = "[drive.google.com](https://drive.google.com/your-saafe-sylhet-zip-link)"

# ─────────────────────────────────────────────
# Session Store
# Keys: user_id (int)
# Values: dict with keys:
#   authenticated  – bool, passed main login
#   state          – current awaited input or None
# ─────────────────────────────────────────────
sessions: dict[int, dict] = {}


def get_session(user_id: int) -> dict:
    """Return existing session or create a fresh one."""
    if user_id not in sessions:
        sessions[user_id] = {"authenticated": False, "state": None}
    return sessions[user_id]


def is_authenticated(user_id: int) -> bool:
    return get_session(user_id).get("authenticated", False)


# ─────────────────────────────────────────────
# Keyboard Builders
# ─────────────────────────────────────────────

def kb_main_menu() -> types.ReplyKeyboardMarkup:
    """Main menu shown after login."""
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton("🫂 Click For - Pictures 🖼️"))
    return kb


def kb_pictures_menu() -> types.ReplyKeyboardMarkup:
    """Sub-menu for the Pictures section."""
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(types.KeyboardButton("1️⃣ Our Grup Pictures 🖼️"))
    kb.row(types.KeyboardButton("2️⃣ SaaFe - Personal 💻"))
    kb.row(types.KeyboardButton("3️⃣ SaaFe - Sylhet Picture's 🖼️"))
    kb.row(types.KeyboardButton("🔙 Back"))
    return kb


def kb_back_only() -> types.ReplyKeyboardMarkup:
    """Keyboard with only the Back button."""
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton("🔙 Back"))
    return kb


def kb_remove() -> types.ReplyKeyboardRemove:
    return types.ReplyKeyboardRemove()


# ─────────────────────────────────────────────
# /start Handler
# ─────────────────────────────────────────────

@bot.message_handler(commands=["start"])
def handle_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.first_name or "User"

    # Reset session on every /start
    sessions[user_id] = {"authenticated": False, "state": "awaiting_main_password"}

    logger.info("User %s (%d) started the bot.", username, user_id)
    bot.send_message(
        user_id,
        "🔑 Sir Please Send your Password.",
        reply_markup=kb_remove(),
    )


# ─────────────────────────────────────────────
# Main Message Router
# ─────────────────────────────────────────────

@bot.message_handler(func=lambda m: True)
def handle_message(message: types.Message):
    user_id  = message.from_user.id
    text     = message.text or ""
    session  = get_session(user_id)
    state    = session.get("state")

    # ── Guard: user hasn't started yet ──────────
    if state is None and not session["authenticated"]:
        bot.send_message(
            user_id,
            "Please send /start to begin.",
        )
        return

    # ── Route by state ───────────────────────────
    if state == "awaiting_main_password":
        _handle_main_password(message, session)

    elif state == "awaiting_saafe_password_personal":
        _handle_saafe_password(message, session, section="personal")

    elif state == "awaiting_saafe_password_sylhet":
        _handle_saafe_password(message, session, section="sylhet")

    elif session["authenticated"]:
        _handle_menu(message, session)

    else:
        bot.send_message(user_id, "Please send /start to begin.")


# ─────────────────────────────────────────────
# Password Handlers
# ─────────────────────────────────────────────

def _handle_main_password(message: types.Message, session: dict):
    user_id = message.from_user.id
    text    = message.text or ""

    if text == MAIN_PASSWORD:
        session["authenticated"] = True
        session["state"]         = None
        logger.info("User %d authenticated successfully.", user_id)
        bot.send_message(user_id, "✅ Access Granted.", reply_markup=kb_main_menu())
    else:
        logger.warning("User %d entered wrong main password.", user_id)
        bot.send_message(user_id, "❌ Wrong Password. Try Again.")


def _handle_saafe_password(message: types.Message, session: dict, section: str):
    user_id = message.from_user.id
    text    = message.text or ""

    if text == SAAFE_PASSWORD:
        session["state"] = None
        logger.info("User %d unlocked SaaFe section: %s.", user_id, section)

        if section == "personal":
            bot.send_message(
                user_id,
                f"Here is SaaFe Personal ZIP File:\n{LINK_SAAFE_PERSONAL}",
                reply_markup=kb_back_only(),
            )
        elif section == "sylhet":
            bot.send_message(
                user_id,
                f"Here is Sylhet Pictures ZIP File:\n{LINK_SAAFE_SYLHET}",
                reply_markup=kb_back_only(),
            )
    else:
        logger.warning("User %d entered wrong SaaFe password for %s.", user_id, section)
        # Keep state so they can try again
        bot.send_message(user_id, "❌ Wrong Password")


# ─────────────────────────────────────────────
# Menu Navigation Handler
# ─────────────────────────────────────────────

def _handle_menu(message: types.Message, session: dict):
    user_id  = message.from_user.id
    text     = message.text or ""

    # ── Main Menu ────────────────────────────────
    if text == "🫂 Click For - Pictures 🖼️":
        session["menu"] = "pictures"
        bot.send_message(
            user_id,
            "📁 Choose a category:",
            reply_markup=kb_pictures_menu(),
        )

    # ── Pictures Sub-Menu ────────────────────────
    elif text == "1️⃣ Our Grup Pictures 🖼️":
        logger.info("User %d requested Group Pictures.", user_id)
        bot.send_message(
            user_id,
            f"Here are Our Group Pictures:\n{LINK_GROUP_PICTURES}",
            reply_markup=kb_back_only(),
        )

    elif text == "2️⃣ SaaFe - Personal 💻":
        session["state"] = "awaiting_saafe_password_personal"
        bot.send_message(
            user_id,
            "🔐 Please Enter Password",
            reply_markup=kb_remove(),
        )

    elif text == "3️⃣ SaaFe - Sylhet Picture's 🖼️":
        session["state"] = "awaiting_saafe_password_sylhet"
        bot.send_message(
            user_id,
            "🔐 Please Enter Password",
            reply_markup=kb_remove(),
        )

    # ── Back Button ──────────────────────────────
    elif text == "🔙 Back":
        current_menu = session.get("menu")

        if current_menu == "pictures":
            # From a sub-item inside pictures → go back to pictures menu
            session.pop("menu", None)
            bot.send_message(
                user_id,
                "📁 Choose a category:",
                reply_markup=kb_pictures_menu(),
            )
        else:
            # From pictures menu → go back to main menu
            session.pop("menu", None)
            bot.send_message(
                user_id,
                "🏠 Main Menu",
                reply_markup=kb_main_menu(),
            )

    # ── Unknown Input ────────────────────────────
    else:
        bot.send_message(
            user_id,
            "Please use the keyboard buttons to navigate.",
        )


# ─────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    logger.info("Bot is starting...")
    bot.infinity_polling(logger_level=logging.WARNING)
