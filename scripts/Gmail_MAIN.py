from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, UTC
import os
import base64
import json
import boto3



load_dotenv(dotenv_path='config.env') 
load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
S3_BUCKET = os.getenv("S3_BUCKET")
LABEL = os.getenv("EMAIL_LABEL")

# AWS S3 Client
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)

def authenticate_gmail():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def fetch_gmail_messages(service):
    results = service.users().messages().list(userId='me', labelIds=[LABEL], maxResults=15).execute()
    messages = results.get('messages', [])
    return messages

def get_email_content(service, msg_id):
    msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
    headers = msg.get('payload', {}).get('headers', [])
    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "No Subject")
    snippet = msg.get('snippet', '')
    timestamp_ms = int(msg['internalDate'])
    dt = datetime.fromtimestamp(timestamp_ms / 1000,UTC)

    body = ''
    parts = msg.get('payload', {}).get('parts', [])
    for part in parts:
        if part['mimeType'] == 'text/plain':
            data = part['body'].get('data')
            if data:
                body = base64.urlsafe_b64decode(data).decode('utf-8')
    return {"data":{
        'id': msg_id,
        'subject': subject,
        'snippet': snippet,
        'body': body},"time":dt
    }

def upload_to_s3(email_obj,time):
    year = str(time.year)
    month = f"{time.month:02}"
    day = f"{time.day:02}"
    hour = f"{time.hour:02}"
    key = f"emails/raw/{year}/{month}/{day}/{hour}/{email_obj['id']}.json"
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=json.dumps(email_obj)
    )
    print(f"Uploaded: {key}")

def main():
    service = authenticate_gmail()
    messages = fetch_gmail_messages(service)
    for msg in messages:
        data = get_email_content(service, msg['id'])
        upload_to_s3(data["data"],data["time"])

if __name__ == '__main__':
    main()