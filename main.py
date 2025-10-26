from flask import app
import os
import logging
from logging.handlers import RotatingFileHandler
from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InputFile, InlineKeyboardMarkup, InlineKeyboardButton

app = app.Flask(__name__)

# --- logging setup ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
log_dir = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(log_dir, exist_ok=True)
logger = logging.getLogger("telegram_bot")
logger.setLevel(LOG_LEVEL)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s", "%Y-%m-%d %H:%M:%S")

stream_h = logging.StreamHandler()
stream_h.setLevel(LOG_LEVEL)
stream_h.setFormatter(formatter)
logger.addHandler(stream_h)

file_h = RotatingFileHandler(os.path.join(log_dir, "bot.log"), maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8")
file_h.setLevel(LOG_LEVEL)
file_h.setFormatter(formatter)
logger.addHandler(file_h)

TOKEN = os.getenv("API_TOKEN", "8458550485:AAE4D4EGbdg0dDVDWwPW8MpyuM4sKKsnIGI")

bot = TeleBot(token=TOKEN)
DATA_PATH = "data"

menus = {
    "menu1": {
        "title": "🏫 القبول والتسجيل",
        "items": [
            "📅 الخط الزمني للفصل الأول",
            "🕐 مواعيد القبول والتسجيل للفصل القادم",
            "📝 التقديم اليدوي للكلية",
            "🏢 التعريف بالمؤسسة",
            "ℹ️ تعرف علينا",
            "📖 أقسام الكلية",
            "🌙 الدبلوم المسائي",
            "📘 معادلة مقررات الكلية",
            "🏅 متفوقو الكلية",
        ],
    },
    "menu2": {
        "title": "🎓 شؤون المتدربين",
        "items": [
            "📋 الخطة التدريبية",
            "📧 بريد المتدرب الرسمي",
            "💰 المكافأة",
            "⚠️ آلية الاعتراض",
            "🚫 الحرمان وحالات الإنذار",
            "🚫 الحرمان وحالات الإنذار 1",
            "🚫 الحرمان وحالات الإنذار 2",
            "📗 دليل المتدرب",
            "💳 الشؤون المالية للمتدرب",
            "🧰 أدوات مساعدة للمتدرب",
            "📝 تقديم شكوى أو اعتراض من المتدرب",
            "🤲 خدمة المجتمع",
        ],
    },
    "menu3": {
        "title": "📚 الشؤون الأكاديمية",
        "items": [
            "🧮 إرشادات الاختبارات والتقييمات",
            "📖 دليل التصنيف",
            "📑 تقرير المقررات المتبقية",
            "📞 التواصل مع أقسام الكلية",
            "🤝 التدريب التعاوني",
            "🎓 برنامج دعم مشاريع التخرج",
            "🧭 مكتب التنسيق الوظيفي",
            "📝 إرشادات الاختبارات ولتقييمات2",
        ],
    },
    "menu4": {
        "title": "💻 المنصات والخدمات الإلكترونية",
        "items": [
            "🌐 منصة خدمات المتدربين ومنصة رايات",
            "💼 منصة المكتب Office 365 ومنصة البريد بيرود",
            "📲 التواصل مع رايات",
            "📘 معلومات مهمة للمستجدين والمستمرين",
            "🆕 معلومات مهمة للمستجدين",
            "🗓️ التقويم التدريبي 1446–1447",
        ],
    },
    "menu5": {
        "title": "🤝 التواصل والدعم",
        "items": [
            "📨 التواصل مع الكلية",
            "📞 التواصل مع أقسام الكلية",
            "🏅 متفوقو المؤسسة",
            "🚗 مواقف المتدربين داخل حرم الكلية",
        ],
    },
    "menu6": {
        "title": "🌍 الشهادات والأكاديميات",
        "items": [
            "🎓 الأكاديميات الدولية",
            "📜 الشهادات الاحترافية والأكاديميات الدولية",
        ],
    },
    "menu7": {
        "title": "🏠 الخدمات العامة والمساندة",
        "items": [
            "🏠 سكن الكلية",
            "📊 طريقة عرض الجدول في رايات",
            "📄 برشور قديم",
        ],
    },
}

# ===== إنشاء القائمة الرئيسية =====
def main_menu():
    # Reply keyboard with one button per row (fixed buttons)
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for key, menu in menus.items():
        markup.row(KeyboardButton(menu["title"]))
    return markup


def main_menu_inline():
    """Inline keyboard for the main menu so it can be shown inside the same message.
    We also set a reply keyboard separately (sent then deleted) to keep the reply keys visible.
    Callback format: menu|<menu_key>
    """
    markup = InlineKeyboardMarkup()
    for key, menu in menus.items():
        markup.add(InlineKeyboardButton(menu["title"], callback_data=f"menu|{key}"))
    return markup


# ===== إنشاء قائمة فرعية =====
def submenu(menu_key):
    # Helper to safely truncate strings so their UTF-8 encoding fits in max_bytes
    def _truncate_utf8(s: str, max_bytes: int) -> str:
        b = s.encode("utf-8")
        if len(b) <= max_bytes:
            return s
        # cut bytes and ignore incomplete trailing multibyte sequences
        return b[:max_bytes].decode("utf-8", "ignore")

    markup = InlineKeyboardMarkup()
    prefix = "item|"
    max_callback_bytes = 64
    # compute how many bytes remain for the item part after the prefix
    allowed_bytes = max_callback_bytes - len(prefix.encode("utf-8"))
    for item in menus[menu_key]["items"]:
        # truncate by bytes (not characters) to avoid BUTTON_DATA_INVALID
        safe_data = _truncate_utf8(item, allowed_bytes)
        markup.add(InlineKeyboardButton(item, callback_data=prefix + safe_data))
    markup.add(InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
    return markup


def submenu_inline(menu_key):
    """Return an InlineKeyboardMarkup for the submenu so we can send it as a new message
    (keeps the reply keyboard visible). Uses short callback_data in the form: item|<menu_key>|<index>
    """
    markup = InlineKeyboardMarkup()
    for idx, item in enumerate(menus[menu_key]["items"]):
        cb = f"item|{menu_key}|{idx}"
        markup.add(InlineKeyboardButton(item, callback_data=cb))
    # add a close button to remove the inline menu message
    markup.add(InlineKeyboardButton("🔙 إغلاق", callback_data=f"close|{menu_key}"))
    return markup


# ===== /start =====
@bot.message_handler(commands=["start"])
def start(message):
    text = "👋 مرحباً بك!\nاختر من التصنيفات التالية:"
    logger.info("/start from chat_id=%s user=%s", message.chat.id, getattr(message.from_user, 'id', None))
    # send the visible menu as an inline keyboard (so the message contains the buttons)
    bot.send_message(message.chat.id, text, reply_markup=main_menu_inline())

    # then send a short message with the ReplyKeyboardMarkup to set the reply keyboard for the chat
    # and delete that helper message so the user only sees the inline-menu message.
    try:

        helper = bot.send_message(message.chat.id, "سوف تجد ازرار الوصول للمحتوى متاحه في القائمة الازرار للوصول بشكل اسرع.", reply_markup=main_menu())
        try:
            bot.delete_message(message.chat.id, helper.message_id)
        except Exception:
            # ignore delete failures (bot might not have permission)
            
            pass
    except Exception as e:
        # if setting the reply keyboard fails, ignore — the inline menu still works
        logger.exception("failed to set reply keyboard for chat_id=%s: %s", message.chat.id, e)
        pass

# ===== التعامل مع الضغط على الأزرار =====
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text
    logger.info("message from chat_id=%s: %s", message.chat.id, text)

    # map menu titles to keys
    title_to_key = {menu["title"]: key for key, menu in menus.items()}

    # If user pressed a main menu button, send the submenu as a NEW message with inline buttons
    # this keeps the main reply keyboard visible while the submenu appears as an inline keyboard
    if text in title_to_key:
        key = title_to_key[text]
        bot.send_message(message.chat.id, menus[key]["title"], reply_markup=submenu_inline(key))
        return

    # Back to main menu
    if text == "🔙 رجوع":
        bot.send_message(message.chat.id, "👋 مرحباً بك!\nاختر من التصنيفات التالية:", reply_markup=main_menu())
        logger.info("sent main menu reply keyboard to chat_id=%s", message.chat.id)
        return

    # If pressed an item button, send folder content
    for key, menu in menus.items():
        if text in menu["items"]:
            logger.info("selected item '%s' from menu '%s'", text, key)
            send_folder_content(message.chat.id, text)
            return

    # Unknown input: ignore or inform user
    # (optional) send a help message or re-show main menu
    # bot.send_message(message.chat.id, "اختر أحد الأزرار أدناه:", reply_markup=main_menu())


# ===== إرسال محتوى المجلد =====
def send_folder_content(chat_id, item_name):
    logger.info("send_folder_content: chat_id=%s item=%s", chat_id, item_name)
    folder_path = os.path.join(DATA_PATH, item_name)
    if not os.path.exists(folder_path):
        logger.warning("folder not found: %s", folder_path)
        bot.send_message(chat_id, f"❌ لا يوجد محتوى في القسم {item_name}")
        return

    files = os.listdir(folder_path)
    if not files:
        bot.send_message(chat_id, f"📂 قسم {item_name} فارغ حالياً.")
        return

    for file in files:
        path = os.path.join(folder_path, file)

        if file.endswith(".txt"):
            with open(path, "r", encoding="utf-8") as f:
                try:
                    bot.send_message(chat_id, f.read().strip())
                except Exception as e:
                    logger.exception("failed to send text file %s to chat_id=%s: %s", path, chat_id, e)

        elif file.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
            with open(path, "rb") as img:
                try:
                    bot.send_photo(chat_id, img)
                except Exception as e:
                    logger.exception("failed to send image %s to chat_id=%s: %s", path, chat_id, e)

        else:
            with open(path, "rb") as doc:
                try:
                    bot.send_document(chat_id, InputFile(doc, file_name=file))
                except Exception as e:
                    logger.exception("failed to send document %s to chat_id=%s: %s", path, chat_id, e)



# ===== التعامل مع الضغط على أزرار القوائم الداخلية (Inline) =====
@bot.callback_query_handler(func=lambda call: True)
def inline_callback(call):
    data = call.data or ""

    if data.startswith("item|"):
        # format: item|<menu_key>|<index>
        parts = data.split("|")
        if len(parts) != 3:
            bot.answer_callback_query(call.id, "خطأ في بيانات الزر")
            return
        _, menu_key, idx = parts
        try:
            idx = int(idx)
            item_name = menus[menu_key]["items"][idx]
        except Exception:
            bot.answer_callback_query(call.id, "خطأ في بيانات الزر")
            return

        # send the folder content for the selected item
        send_folder_content(call.message.chat.id, item_name)
        bot.answer_callback_query(call.id)
    elif data.startswith("menu|"):
        # format: menu|<menu_key>
        parts = data.split("|")
        if len(parts) != 2:
            bot.answer_callback_query(call.id, "خطأ في بيانات الزر")
            return
        _, menu_key = parts
        if menu_key not in menus:
            bot.answer_callback_query(call.id, "خطأ في بيانات الزر")
            return

        # edit message to show submenu
        bot.edit_message_text(
            menus[menu_key]["title"],
            call.message.chat.id,
            call.message.message_id,
            reply_markup=submenu(menu_key),
        )

        bot.answer_callback_query(call.id)
    elif data == "back_main":
        bot.edit_message_text(
            "👋 مرحباً بك!\nاختر من التصنيفات التالية:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=main_menu_inline(),
        )
        bot.answer_callback_query(call.id)
    elif data.startswith("close|"):
        # remove the inline menu message (if possible)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            # ignore delete failures
            pass
        bot.answer_callback_query(call.id)


# ===== تفعيل استضافة للبوت ليعمل طول الوقت =====
@app.route("/" )
def home():
    return "Bot is running."

# ===== تشغيل البوت =====
if __name__ == "__main__":
    
    import threading

    def run_flask():
        app.run(host="0.0.0.0", port=5000)

    threading.Thread(target=run_flask).start()
    bot.polling()