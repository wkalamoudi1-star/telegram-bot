from flask import Flask, request, send_file, abort, render_template_string
import os
import logging
from logging.handlers import RotatingFileHandler
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, InputFile

# =========================
# Flask + Telegram Webhook Bot
# =========================

app = Flask(__name__)

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
bot = telebot.TeleBot(TOKEN)
DATA_PATH = "data"

# =========================
# MENUS
# =========================
menus = {
    "menu1": {"title": "🏫 القبول والتسجيل", "items": ["📅 الخط الزمني للفصل الأول", "🕐 مواعيد القبول والتسجيل للفصل القادم", "📝 التقديم اليدوي للكلية", "ℹ️ تعرف علينا", "📖 أقسام الكلية", "🌙 الدبلوم المسائي", "📘 معادلة مقررات الكلية", "🏅 متفوقو الكلية"]},
    "menu2": {"title": "🎓 شؤون المتدربين", "items": ["📋 الخطة التدريبية", "📧 بريد المتدرب الرسمي", "💰 المكافأة", "⚠️ آلية الاعتراض", "🚫 الحرمان وحالات الإنذار", "🚫 الحرمان وحالات الإنذار 1", "📗 دليل المتدرب", "💳 الشؤون المالية للمتدرب", "🧰 أدوات مساعدة للمتدرب", "📝 تقديم شكوى أو اعتراض من المتدرب", "🤲 خدمة المجتمع"]},
    "menu3": {"title": "📚 الشؤون الأكاديمية", "items": ["🧮 إرشادات الاختبارات والتقييمات", "📖 دليل التصنيف", "📑 تقرير المقررات المتبقية", "📞 التواصل مع أقسام الكلية", "🤝 التدريب التعاوني", "🎓 برنامج دعم مشاريع التخرج", "🧭 مكتب التنسيق الوظيفي", "📝 إرشادات الاختبارات ولتقييمات2"]},
    "menu4": {"title": "💻 المنصات والخدمات الإلكترونية", "items": ["🌐 منصة خدمات المتدربين ومنصة رايات", "💼 منصة المكتب Office 365 ومنصة البريد بيرود", "📲 التواصل مع رايات", "📘 معلومات مهمة للمستجدين والمستمرين", "🆕 معلومات مهمة للمستجدين", "🗓️ التقويم التدريبي 1446–1447"]},
    "menu5": {"title": "🤝 التواصل والدعم", "items": ["📨 التواصل مع الكلية", "📞 التواصل مع أقسام الكلية", "🏅 متفوقو المؤسسة", "🚗 مواقف المتدربين داخل حرم الكلية"]},
    "menu6": {"title": "🌍 الشهادات والأكاديميات", "items": ["🎓 الأكاديميات الدولية", "📜 الشهادات الاحترافية والأكاديميات الدولية"]},
    "menu7": {"title": "🏠 الخدمات العامة والمساندة", "items": ["🏠 سكن الكلية", "📊 طريقة عرض الجدول في رايات", "📄 برشور قديم", "📄 1برشور قديم"]},
}

# =========================
# MAIN MENU
# =========================

def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for key, menu in menus.items():
        markup.row(KeyboardButton(menu["title"]))
    return markup

def main_menu_inline():
    markup = InlineKeyboardMarkup()
    for key, menu in menus.items():
        markup.add(InlineKeyboardButton(menu["title"], callback_data=f"menu|{key}"))
    return markup

# =========================
# SUB MENUS
# =========================

def submenu_inline(menu_key):
    markup = InlineKeyboardMarkup()
    for idx, item in enumerate(menus[menu_key]["items"]):
        markup.add(InlineKeyboardButton(item, callback_data=f"item|{menu_key}|{idx}"))
    markup.add(InlineKeyboardButton("🔙 إغلاق", callback_data=f"close|{menu_key}"))
    return markup

# =========================
# SEND FOLDER CONTENT
# =========================

def send_folder_content(chat_id, item_name):
    folder_path = os.path.join(DATA_PATH, item_name)
    if not os.path.exists(folder_path):
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
                bot.send_message(chat_id, f.read().strip())

        elif file.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
            with open(path, "rb") as img:
                bot.send_photo(chat_id, img)

        else:
            with open(path, "rb") as doc:
                bot.send_document(chat_id, InputFile(doc, file_name=file))

# =========================
# HANDLERS
# =========================

@bot.message_handler(commands=["start"])
def start():
    # TODO: handler code goes here
    pass
    text = """
مرحباً بك انا مساعدك التقني 🤖 ..

🌟 لمساعدة متدربي كليات الاتصالات
دبلوم و بكالوريوس  بنين ..

🔻كل اللي عليك تضغط على الأزرار
الي حاب تعرف أجابته ..
"""
    bot.send_message(message.chat.id, text, reply_markup=main_menu_inline(), parse_mode="HTML")
    bot.send_message(message.chat.id, "اختر من القائمة بالأسفل ⬇️", reply_markup=main_menu())

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text
    title_to_key = {menu["title"]: key for key, menu in menus.items()}

    if text in title_to_key:
        key = title_to_key[text]
        bot.send_message(message.chat.id, menus[key]["title"], reply_markup=submenu_inline(key))
        return

    for key, menu in menus.items():
        if text in menu["items"]:
            send_folder_content(message.chat.id, text)
            return

@bot.callback_query_handler(func=lambda call: True)
def inline_callback(call):
    data = call.data

    if data.startswith("item|"):
        _, menu_key, idx = data.split("|")
        item_name = menus[menu_key]["items"][int(idx)]
        send_folder_content(call.message.chat.id, item_name)
        bot.answer_callback_query(call.id)

    elif data.startswith("menu|"):
        _, menu_key = data.split("|")
        bot.edit_message_text(menus[menu_key]["title"], call.message.chat.id, call.message.message_id, reply_markup=submenu_inline(menu_key))
        bot.answer_callback_query(call.id)

    elif data.startswith("close|"):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)

# =========================
# FLASK ROUTES
# =========================

@app.route("/")
def home():
    return "Bot is running."

@app.route(f"/{TOKEN}", methods=["POST"])
def telegram_webhook():
    json_data = request.get_json(force=True)
    update = telebot.types.Update.de_json(json_data)
    bot.process_new_updates([update])
    return "OK", 200

# =========================
# START WEBHOOK
# =========================

if __name__ == "__main__":
    import requests

    WEBHOOK_URL = "https://telegram-bot-5m8i.onrender.com/" + TOKEN

    try:
        requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook")
        requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}")
    except Exception as e:
        print("Failed to set webhook:", e)

    app.run(host="0.0.0.0", port=5000)
