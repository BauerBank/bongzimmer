import imaplib
import email
import time
from datetime import datetime
import asyncio
import requests
import logging
from pygame import mixer
import glob
import random
import telegram

from config import connect_to_printer, config

WRAP_WIDTH = config["wrap_width"]
CHUNK_SIZE = config["chunk_size"]
CHUNK_TIME = config["chunk_time"]
MAX_SIZE = WRAP_WIDTH * 250

MUSIC_PATH = config["music_path"]

mixer.init()

p = connect_to_printer()

bot = telegram.Bot(token=config["tg_token"])

# p.text("HaDiKo-L printer up.....")
# p.cut()

def play_sound():
    files = glob.glob(MUSIC_PATH+"*.mp3")
    random_number = int(random.uniform(0,len(files)-1))
    filename = files[random_number]
    mixer.music.load(filename)
    mixer.music.play()

def print_out(to_print, body=""):
    # Sanity check: Length
    if len(body) < MAX_SIZE:
        to_print += body
    else:
        to_print += body[:MAX_SIZE]
        to_print += "...\n\nMESSAGE TOO LONG"

    logging.info("Received Message, printing:\n\n" + to_print)

    to_print_chunks = [to_print[i:i+CHUNK_SIZE] for i in range(0, len(to_print), CHUNK_SIZE)]

    play_sound()
    
    for chunk in to_print_chunks:
        chunk = chunk.encode('cp437', errors='replace')
        #chunk = chunk.decode('cp437', errors='replace')
        p._raw(chunk)
        time.sleep(CHUNK_TIME)

    p.cut()

async def check_telegram():
    global LAST_UPDATE_ID
    file = open('allowed_telegram_users.txt','r')
    allowed_chat_ids = file.read().split(',')
    updates = await bot.getUpdates()
    for update in updates:
        if update.message is not None and (update.message.message_id > LAST_UPDATE_ID):
            LAST_UPDATE_ID = update.message.message_id
            if update.message.chat.username in allowed_chat_ids:
                if update.message.text[-5:].lower() == "start" or update.message.text[-4:].lower() == "help" or update.message.text[-4:].lower() == "test":
                    reply_text = "Hello " + update.message.from_user.first_name + ",\nWelcome to Weizenbierfreunde F3!"
                else:
                    to_print = "Telegram message from: " + update.message.chat.first_name + "\n\n" + update.message.text
                    print_out(to_print)
                    reply_text = "Hello " + update.message.from_user.first_name + ",\nThanks, your message was sent to the printer!"
                await bot.sendMessage(chat_id=update.message.chat.id, text=reply_text)
            else:
                await bot.sendMessage(chat_id=update.message.chat.id, text="Sorry, that's not allowed.")

async def fetch_emails():

    if config["health_url"] != "http://health.example.com/bongzimmer":
        try:
            requests.get(config["health_url"], timeout=config["health_timeout"])
        except requests.RequestException:
            # Log ping failure here...
            logging.exception("Ping failed")
    
    # Login to the email server
    logging.debug("Logging into the IMAP server")
    mail = imaplib.IMAP4_SSL(config["imap_server"])
    mail.login(config["imap_email"], config["imap_password"])
    mail.select(config["imap_directory"])

    # Search for all unseen emails
    status, messages = mail.search(None, 'UNSEEN')
    num_messages = len(messages[0].split())
    logging.debug(f"Found %s email%s", num_messages, "s" if num_messages != 1 else "")

    # Loop through all unseen emails
    for num in messages[0].split():
        status, email_data = mail.fetch(num, '(RFC822)')
        raw_email = email_data[0][1]
        email_message = email.message_from_bytes(raw_email)
        date_time_str = email_message['Date']
        date_time_obj = email.utils.parsedate_tz(date_time_str)
        date_time_obj = datetime.fromtimestamp(email.utils.mktime_tz(date_time_obj))

        # Extract the plain text body of the email
        body = ''
        for part in email_message.walk():
            # Check if the part is an attachment
            if part.get('Content-Disposition') is None:
                # If not, extract the text body and append it to the result
                if part.get_content_type() == 'text/plain':
                    charset = part.get_content_charset()
                    # decode the payload using the charset
                    body += part.get_payload(decode=True).decode(charset)
                    # body += part.get_payload()

        # Print the email details to the console
        to_print = 'From: ' + email_message['From'] + '\n' + 'Subject: ' + email_message['Subject'] + '\n' + 'Date: ' + date_time_obj.strftime("%Y-%m-%d %H:%M:%S %Z") + '\n\n'

        print_out(to_print, body)

    logging.debug("done fetching and printing mails")
    # Logout from the email server
    mail.close()
    mail.logout()


async def main():
    logging.basicConfig(level="WARNING", format="%(asctime)s :: %(levelname)s :: %(message)s")

    # get newest update id
    global LAST_UPDATE_ID
    updates = await bot.getUpdates()
    if updates[-1].message is not None:
        LAST_UPDATE_ID = updates[-1].message.message_id

    # Keep the main thread running
    while True:
        try:
            await fetch_emails()
            await check_telegram()
        except Exception:
            logging.exception("exception occurred")
            continue
        await asyncio.sleep(5)



if __name__ == "__main__":
    asyncio.run(main())
