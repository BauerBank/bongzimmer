import imaplib
import email
import time
from datetime import datetime
import asyncio
import requests
import logging

from config import connect_to_printer, config

WRAP_WIDTH = config["wrap_width"]
CHUNK_SIZE = config["chunk_size"]
CHUNK_TIME = config["chunk_time"]
MAX_SIZE = WRAP_WIDTH * 250

p = connect_to_printer()

# p.text("HaDiKo-L printer up.....")
# p.cut()

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

        # Sanity check: Length
        if len(body) < MAX_SIZE:
            to_print += body
        else:
            to_print += body[:MAX_SIZE]
            to_print += "...\n\nMESSAGE TOO LONG"

        logging.info("Received Message, printing:\n\n" + to_print)

        to_print_chunks = [to_print[i:i+CHUNK_SIZE] for i in range(0, len(to_print), CHUNK_SIZE)]

        for chunk in to_print_chunks:
            chunk = chunk.encode('cp437', errors='replace')
            #chunk = chunk.decode('cp437', errors='replace')
            p._raw(chunk)
            time.sleep(CHUNK_TIME)

        p.cut()

    logging.debug("done fetching and printing mails")
    # Logout from the email server
    mail.close()
    mail.logout()


async def main():
    logging.basicConfig(level="DEBUG", format="%(asctime)s :: %(levelname)s :: %(message)s")

    # Keep the main thread running
    while True:
        try:
            await fetch_emails()
        except Exception:
            logging.exception("exception occurred")
            continue
        await asyncio.sleep(5)



if __name__ == "__main__":
    asyncio.run(main())
