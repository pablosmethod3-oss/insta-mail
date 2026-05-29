import os
import re
import time
import random
import threading
import telebot
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from http.server import BaseHTTPRequestHandler, HTTPServer

# 1. Telegram Bot Token
BOT_TOKEN = "8883017716:AAEVENqtXin_yPedL7Sbuw6VKe5RsWagrn8"
bot = telebot.TeleBot(BOT_TOKEN)

# 2. Apna Main Gmail Username (Bina @gmail.com ke)
MY_GMAIL_USERNAME = "pablosmethod3"

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.modify']

email_database = {}
active_monitors = set()

# === RENDER PORT FIX ===
class HealthCheckServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot is running 24/7 with Safe Dot-Mix Generator!")

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckServer)
    server.serve_forever()

def get_gmail_service():
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        return build('gmail', 'v1', credentials=creds)
    else:
        raise Exception("Error: token.json file nahi mili!")

# Safe Dot + Letters Mix Generator (Jo 100% aapke inbox me hi deliver hoga)
def generate_safe_dot_gmail():
    username = MY_GMAIL_USERNAME
    result = username[0]
    
    # Letters ke beech me random dots settings
    for letter in username[1:]:
        if random.choice([True, False]):
            result += '.'
        result += letter
        
    return f"{result}@gmail.com"

def auto_fetch_otp(chat_id, target_email):
    print(f"[LIVE SCANNING] Checking fresh mail for: {target_email}")
    attempts = 0
    max_attempts = 36  # 3 minute timeout
    
    while attempts < max_attempts:
        if target_email not in active_monitors:
            break
        try:
            service = get_gmail_service()
            # PURE INBOX me se jo bhi UNREAD mail Instagram ka ho use nikalega (Subject jhanjhat khatam)
            results = service.users().messages().list(userId='me', q='instagram is:unread').execute()
            messages = results.get('messages', [])
            
            for message in messages:
                msg = service.users().messages().get(userId='me', id=message['id']).execute()
                snippet = msg.get('snippet', '')
                
                # 6 digit OTP dhundne ke liye
                otp_match = re.search(r'\b\d{6}\b', snippet)
                if otp_match:
                    otp_code = otp_match.group(0)
                    
                    success_text = (
                        f"⚡ **[FRESH OTP RECEIVED]** ⚡\n\n"
                        f"📧 **Email Used:** `{target_email}`\n"
                        f"🔑 **Instagram Code:** `{otp_code}`\n"
                    )
                    bot.send_message(chat_id, success_text, parse_mode='Markdown')
                    
                    # Mail ko read mark kar do taaki agla wala setup fresh rhae
                    service.users().messages().batchModify(
                        userId='me', 
                        body={'ids': [message['id']], 'removeLabelIds': ['UNREAD']}
                    ).execute()
                    
                    active_monitors.discard(target_email)
                    return
        except Exception as e:
            print(f"API Fetching error: {e}")
            
        time.sleep(5)
        attempts += 1
    
    print(f"[TIMEOUT] OTP nahi mila: {target_email}")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🤖 **Safe Dot-Generator Ready!**\n\nNaya unique email lene ke liye `/generate` chalao.")

@bot.message_handler(commands=['generate'])
def generate_gmail(message):
    chat_id = message.chat.id
    generated_email = generate_safe_dot_gmail()
    
    email_database[generated_email] = chat_id
    active_monitors.add(generated_email)
    
    bot.send_message(chat_id, f"🎉 **New Email:** `{generated_email}`\n\nIse Instagram me dalo, bot fresh OTP nikaal dega!", parse_mode='Markdown')
    threading.Thread(target=auto_fetch_otp, args=(chat_id, generated_email)).start()

if __name__ == '__main__':
    try:
        get_gmail_service()
        threading.Thread(target=run_health_server, daemon=True).start()
        print("[SUCCESS] Bot successfully started 24/7!")
        bot.infinity_polling()
    except Exception as e:
        print(f"Failed: {e}")
