import os
import json
import base64
import requests
import sqlite3
import pickle
import time
from datetime import datetime
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import google.generativeai as genai

load_dotenv()

OAUTH_CREDENTIALS_FILE = os.getenv("OAUTH_CREDENTIALS_FILE")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DB_FILE = os.getenv("DB_FILE")

genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-2.0-flash")

def setup_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS emails (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email_subject TEXT,
        category TEXT,
        email_link TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS last_processed (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        last_email_id TEXT
    )
    """)
    conn.commit()
    conn.close()

setup_database()

def authenticate_gmail_oauth():
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(OAUTH_CREDENTIALS_FILE, ["https://www.googleapis.com/auth/gmail.readonly"])
            creds = flow.run_local_server(port=0)
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    return build("gmail", "v1", credentials=creds)

def analyze_email_with_gemini(subject, body):
    prompt = f"""
    Classify this email into one of the categories:
    - Job Opportunity
    - Application Update
    - Event Invite
    - Spam / Promotion
    - General Information

    Email Subject: {subject}
    Email Content: {body}
    """
    try:
        response = gemini_model.generate_content(prompt)
        analysis = response.text.strip()
        return "Spam / Promotion" if "Spam" in analysis or "Promotion" in analysis else analysis
    except Exception as e:
        return f"Error: {str(e)}"

def move_email_to_spam(service, email_id):
    try:
        service.users().messages().modify(userId="me", id=email_id, body={"addLabelIds": ["SPAM"], "removeLabelIds": ["INBOX"]}).execute()
        print(f"Moved email {email_id} to spam.")
    except Exception as e:
        print(f"Error moving email to spam: {e}")

def get_last_processed_email():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT last_email_id FROM last_processed ORDER BY id DESC LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def update_last_processed_email(email_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO last_processed (last_email_id) VALUES (?)", (email_id,))
    conn.commit()
    conn.close()

def send_progress_bar(current, total):
    progress = int((current / total) * 10)
    bar = "█" * progress + "░" * (10 - progress)
    message = f"Processing emails...\n[{bar}] {int((current / total) * 100)}% completed."
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", json={"chat_id": TELEGRAM_CHAT_ID, "text": message})

def save_attachment(service, email_id):
    try:
        msg = service.users().messages().get(userId="me", id=email_id).execute()
        for part in msg.get("payload", {}).get("parts", []):
            if part.get("filename") and part.get("body", {}).get("attachmentId"):
                attachment = service.users().messages().attachments().get(userId="me", messageId=email_id, id=part["body"]["attachmentId"]).execute()
                file_data = base64.urlsafe_b64decode(attachment["data"].encode("UTF-8"))
                with open(f"attachments/{part['filename']}", "wb") as f:
                    f.write(file_data)
                print(f"Saved attachment: {part['filename']}")
    except Exception as e:
        print(f"Error saving attachment: {e}")

def process_emails(service):
    try:
        last_email_id = get_last_processed_email()
        query_params = {"userId": "me", "labelIds": ["INBOX"], "maxResults": 500}
        if last_email_id:
            query_params["pageToken"] = last_email_id  
        results = service.users().messages().list(**query_params).execute()
        messages = results.get("messages", [])
        if not messages:
            print("No new emails found.")
            return
        total_emails = len(messages)
        print(f"Found {total_emails} new emails.")
        send_progress_bar(0, total_emails)
        for i, message in enumerate(messages):
            msg = service.users().messages().get(userId="me", id=message["id"]).execute()
            email_body = msg.get("snippet", "No content available.")
            headers = msg.get("payload", {}).get("headers", [])
            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
            email_link = f"https://mail.google.com/mail/u/0/#inbox/{message['id']}"
            category = analyze_email_with_gemini(subject, email_body)
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO emails (email_subject, category, email_link) VALUES (?, ?, ?)", (subject, category, email_link))
            conn.commit()
            conn.close()
            update_last_processed_email(message["id"])
            if "application/pdf" in str(msg):
                save_attachment(service, message["id"])
            if (i + 1) % 10 == 0 or i + 1 == total_emails:
                send_progress_bar(i + 1, total_emails)
    except Exception as e:
        print(f"Gmail API Error: {e}")

if __name__ == "__main__":
    service = authenticate_gmail_oauth()
    if service:
        print("Gmail API ready.")
        while True:
            process_emails(service)
            time.sleep(300)
