from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from email.mime.text import MIMEText
import base64


def get_gmail_service(
    access_token,
    refresh_token=None,
    client_id=None,
    client_secret=None
):
    """
    Create Gmail API service.

    IMPORTANT:
    Do not pass scopes here.

    Google already knows the scopes associated with the
    OAuth refresh token. Passing a different scope list during
    token refresh can cause invalid_scope.
    """

    credentials = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
    )

    return build(
        "gmail",
        "v1",
        credentials=credentials
    )


def search_emails(
    access_token,
    refresh_token,
    client_id,
    client_secret,
    query=""
):
    service = get_gmail_service(
        access_token,
        refresh_token,
        client_id,
        client_secret
    )

    response = service.users().messages().list(
        userId="me",
        q=query,
        maxResults=10
    ).execute()

    messages = response.get("messages", [])

    results = []

    for message in messages:
        msg = service.users().messages().get(
            userId="me",
            id=message["id"],
            format="metadata",
            metadataHeaders=[
                "From",
                "To",
                "Subject",
                "Date"
            ]
        ).execute()

        headers = msg.get("payload", {}).get("headers", [])

        header_dict = {
            h["name"]: h["value"]
            for h in headers
        }

        results.append({
            "id": message["id"],
            "from": header_dict.get("From", ""),
            "to": header_dict.get("To", ""),
            "subject": header_dict.get("Subject", ""),
            "date": header_dict.get("Date", "")
        })

    return {
        "success": True,
        "count": len(results),
        "emails": results
    }


def read_email(
    access_token,
    refresh_token,
    client_id,
    client_secret,
    message_id
):
    service = get_gmail_service(
        access_token,
        refresh_token,
        client_id,
        client_secret
    )

    message = service.users().messages().get(
        userId="me",
        id=message_id,
        format="full"
    ).execute()

    headers = message.get("payload", {}).get("headers", [])

    header_dict = {
        h["name"]: h["value"]
        for h in headers
    }

    body = ""

    payload = message.get("payload", {})

    if "parts" in payload:

        for part in payload["parts"]:

            if part.get("mimeType") == "text/plain":

                data = part.get("body", {}).get("data")

                if data:
                    body = base64.urlsafe_b64decode(
                        data
                    ).decode(
                        "utf-8",
                        errors="ignore"
                    )

                    break

    else:

        data = payload.get("body", {}).get("data")

        if data:
            body = base64.urlsafe_b64decode(
                data
            ).decode(
                "utf-8",
                errors="ignore"
            )

    return {
        "success": True,
        "id": message_id,
        "from": header_dict.get("From", ""),
        "to": header_dict.get("To", ""),
        "subject": header_dict.get("Subject", ""),
        "date": header_dict.get("Date", ""),
        "body": body
    }


def create_draft(
    access_token,
    refresh_token,
    client_id,
    client_secret,
    to,
    subject,
    body
):
    service = get_gmail_service(
        access_token,
        refresh_token,
        client_id,
        client_secret
    )

    message = MIMEText(body)

    message["To"] = to
    message["Subject"] = subject

    encoded_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    draft = {
        "message": {
            "raw": encoded_message
        }
    }

    result = service.users().drafts().create(
        userId="me",
        body=draft
    ).execute()

    return {
        "success": True,
        "action": "create_draft",
        "draft_id": result["id"]
    }


def send_email(
    access_token,
    refresh_token,
    client_id,
    client_secret,
    to,
    subject,
    body
):
    service = get_gmail_service(
        access_token,
        refresh_token,
        client_id,
        client_secret
    )

    message = MIMEText(body)

    message["To"] = to
    message["Subject"] = subject

    encoded_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    result = service.users().messages().send(
        userId="me",
        body={
            "raw": encoded_message
        }
    ).execute()

    return {
        "success": True,
        "action": "send_email",
        "message_id": result["id"]
    }


def trash_email(
    access_token,
    refresh_token,
    client_id,
    client_secret,
    message_id
):
    service = get_gmail_service(
        access_token,
        refresh_token,
        client_id,
        client_secret
    )

    result = service.users().messages().trash(
        userId="me",
        id=message_id
    ).execute()

    return {
        "success": True,
        "action": "trash_email",
        "message_id": result["id"]
    }