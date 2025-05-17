import os
import subprocess
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from datetime import datetime
import pyautogui
import cv2
import tempfile
import psutil

# ✅ CONFIGURATION SECTION
TOKEN = 'YOUR_BOT_TOKEN_HERE'  # Replace with your bot token
ALLOWED_USER_ID = 1234567890   # Replace with your Telegram ID

# ✅ ALLOWED USER CHECK
def is_allowed(user_id: int) -> bool:
    return user_id == ALLOWED_USER_ID

# ✅ SEARCH FILE VIA Everything HTTP Server
def search_with_everything(filename: str):
    try:
        url = f"http://127.0.0.1:80/?search={filename}&json=1"
        response = requests.get(url)
        if response.status_code == 200:
            results = response.json().get("results", [])
            if results:
                return results[0]['path'] + "\\" + results[0]['name']
    except Exception as e:
        print("Everything HTTP Error:", e)
    return None

# ✅ FALLBACK SEARCH USING os.walk()
def search_with_os(filename, search_path="C:/Users/"):
    for root, dirs, files in os.walk(search_path):
        if filename in files:
            return os.path.join(root, filename)
    return None

# ✅ START MENU
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return
    keyboard = [
        [InlineKeyboardButton("Shutdown", callback_data='shutdown'),
         InlineKeyboardButton("Reboot", callback_data='reboot')],
        [InlineKeyboardButton("Open Yandex", callback_data='open_yandex'),
         InlineKeyboardButton("Open Steam", callback_data='open_steam')],
        [InlineKeyboardButton("Open Sites", callback_data='open_sites')],
        [InlineKeyboardButton("Screenshot", callback_data='screenshot'),
         InlineKeyboardButton("Webcam Photo", callback_data='photo')],
        [InlineKeyboardButton("Kill Process", callback_data='kill_process')],
        [InlineKeyboardButton("Find File", callback_data='find_file')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose an action:", reply_markup=reply_markup)

# ✅ BUTTON HANDLER
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if not is_allowed(user_id):
        await query.edit_message_text("Access denied.")
        return

    action = query.data

    if action == 'shutdown':
        os.system("shutdown /s /t 1")
        await query.edit_message_text("Shutting down PC.")
    elif action == 'reboot':
        os.system("shutdown /r /t 1")
        await query.edit_message_text("Rebooting PC.")
    elif action == 'open_yandex':
        subprocess.Popen(r"C:\Users\YOUR_USERNAME\AppData\Local\Yandex\YandexBrowser\Application\browser.exe")
        await query.edit_message_text("Opening Yandex Browser.")
    elif action == 'open_steam':
        subprocess.Popen(r"C:\Program Files (x86)\Steam\Steam.exe")
        await query.edit_message_text("Opening Steam.")
    elif action == 'open_sites':
        browser = r"C:\Users\YOUR_USERNAME\AppData\Local\Yandex\YandexBrowser\Application\browser.exe"
        subprocess.Popen([browser, "https://web.telegram.org"])
        subprocess.Popen([browser, "https://web.whatsapp.com"])
        await query.edit_message_text("Opening Telegram and WhatsApp Web.")
    elif action == 'screenshot':
        screenshot = pyautogui.screenshot()
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        screenshot.save(temp_file.name)
        await query.message.reply_photo(photo=open(temp_file.name, 'rb'))
    elif action == 'photo':
        cam = cv2.VideoCapture(0)
        ret, frame = cam.read()
        cam.release()
        if ret:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            cv2.imwrite(temp_file.name, frame)
            await query.message.reply_photo(photo=open(temp_file.name, 'rb'))
        else:
            await query.message.reply_text("Failed to capture photo.")
    elif action == 'find_file':
        await query.message.reply_text("Enter the file name or absolute path:")
        context.user_data['awaiting_file'] = True
    elif action == 'kill_process':
        apps = {
            "Yandex": "browser.exe",
            "Steam": "Steam.exe",
            "Discord": "Discord.exe",
            "Explorer": "explorer.exe",
            "PyCharm": "pycharm64.exe"
        }
        keyboard = [[InlineKeyboardButton(name, callback_data=f'kill_{proc}')] for name, proc in apps.items()]
        keyboard.append([InlineKeyboardButton("🔍 Enter manually", callback_data='kill_manual')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("Select a process to kill or enter manually:", reply_markup=reply_markup)

# ✅ TEXT HANDLER (file search or manual process kill)
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return
    text = update.message.text

    if context.user_data.get('awaiting_file'):
        path = search_with_everything(text) or search_with_os(text)
        if not path and os.path.isfile(text):
            path = text

        if path:
            try:
                await update.message.reply_document(open(path, 'rb'))
            except Exception as e:
                await update.message.reply_text(f"Error sending file: {e}")
        else:
            await update.message.reply_text("File not found.")
        context.user_data['awaiting_file'] = False

    elif context.user_data.get('awaiting_kill'):
        os.system(f"taskkill /f /im {text}")
        await update.message.reply_text(f"Process {text} killed.")
        context.user_data['awaiting_kill'] = False

# ✅ CALLBACK FOR MANUAL KILL
async def process_manual_kill(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['awaiting_kill'] = True
    await query.message.reply_text("Enter the process name (e.g., chrome.exe):")

# ✅ CALLBACK FOR PREDEFINED KILL
async def kill_specific_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    process_name = query.data.replace("kill_", "")
    os.system(f"taskkill /f /im {process_name}")
    await query.message.reply_text(f"Process {process_name} killed.")

# ✅ BOT MAIN FUNCTION
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(?!kill_).*"))
    app.add_handler(CallbackQueryHandler(kill_specific_process, pattern=r'^kill_[\w.]+$'))
    app.add_handler(CallbackQueryHandler(process_manual_kill, pattern="kill_manual"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
