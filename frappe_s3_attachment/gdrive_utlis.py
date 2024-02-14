from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload

import uuid

GOOGLE_SERVICE = None


def get_google_service():
    global GOOGLE_SERVICE
    if GOOGLE_SERVICE:
        return GOOGLE_SERVICE
    SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
    creds = None
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            creds = service_account.Credentials.from_service_account_file(
                "/workspace/development/frappe-bench/nodal-fountain-361410-5f71dfa12880.json",
                scopes=SCOPES,
            )
    service = build("drive", "v3", credentials=creds)
    GOOGLE_SERVICE = service
    return GOOGLE_SERVICE


def download_file_from_gdrive(url):
    service = get_google_service()
    file_id = url.split("/")[-2]
    file_name = service.files().get(fileId=file_id).execute()["name"]
    file_name = uuid.uuid4().hex[:7].upper() + "_" + file_name
    request = service.files().get_media(fileId=file_id)
    path = "/tmp/" + file_name
    with open(path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
    return file_name, path
