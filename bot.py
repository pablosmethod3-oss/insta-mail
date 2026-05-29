import os
import re
import time
import random
import threading
import telebot
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# 1. Telegram Bot Token
BOT_TOKEN = "8883017716:AAEVENqtXin_yPedL7Sbuw6VKe5RsWagrn8"
bot = telebot.TeleBot(BOT_TOKEN)

# 2. Apna Main Gmail Username
MY_GMAIL_USERNAME = "pablosmethod3"

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.modify']

email_database = {}
active_monitors = set()

def get_gmail_service():
    # Render par hum direct token.json se login karenge, browser ki zaroorat nahi padegi
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        return build('gmail', 'v1', credentials=creds)
    else:
        raise Exception("Error: token.json file nahi mili! Please GitHub par token.json upload karein.")

def generate_dot_gmail():
    username = MY_GMAIL_USERNAME
    dot_username = username[0]
    for letter in username[1:]:
        if random.choice([True, False]) and dot_username[-1] != '.':
            dot_username += '.'
        dot_username += letter
    if '.' not in dot_username:
        dot_username = username[:-1] + '.' + username[-1]
    return f"{dot_username}@gmail.com"

def auto_fetch_otp(chat_id, target_email):
    print(f"[LIVE SCANNING] Dhoond raha hu: {target_email}")
    attempts = 0
    max_attempts = 30
    
    while attempts < max_attempts:
        if target_email not in active_monitors:
            break
        try:
            service = get_gmail_service()
            results = service.users().messages().list(userId='me', q='instagram').execute()
            messages = results.get('messages', [])
            
            for message in messages:
                msg = service.users().messages().get(userId='me', id=message['id']).execute()
                snippet = msg.get('snippet', '')
                
                otp_match = re.search(r'\b\d{6}\b', snippet)
                if otp_match:
                    otp_code = otp_match.group(0)
                    
                    success_text = (
                        f"⚡ **[OTP RECEIVED]** ⚡\n\n"
                        f"📧 **Email:** `{target_email}`\n"
                        f"🔑 **Instagram Code:** `{otp_code}`\n"
                    )
                    bot.send_message(chat_id, success_text, parse_mode='Markdown')
                    print(f"[SUCCESS] OTP mil gaya: {otp_code}")
                    
                    active_monitors.discard(target_email)
                    return
        except Exception as e:
            print(f"API Fetching error: {e}")
            
        time.sleep(5)
        attempts += 1

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🤖 Bot Online 24/7 on Render! `/generate` chalao.")

@bot.message_handler(commands=['generate'])
def generate_gmail(message):
    chat_id = message.chat.id
    generated_email = generate_dot_gmail()
    
    email_database[generated_email] = chat_id
    active_monitors.add(generated_email)
    
    bot.send_message(chat_id, f"🎉 **Email:** `{generated_email}`\n\nIse Instagram me dalo...", parse_mode='Markdown')
    threading.Thread(target=auto_fetch_otp, args=(chat_id, generated_email)).start()

if __name__ == '__main__':
    try:
        print("[SETUP] Checking Connection...")
        get_gmail_service()
        print("[SUCCESS] Bot successfully started 24/7!")
        bot.infinity_polling()
    except Exception as e:
        print(f"Failed: {e}")