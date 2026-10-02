import re
from typing import Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


def get_google_credentials(
    access_token: str,
    refresh_token: Optional[str],
    client_id: str,
    client_secret: str,
    scopes: list[str],
):
    return Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=scopes,
    )


def get_sheets_service(
    access_token: str,
    refresh_token: Optional[str],
    client_id: str,
    client_secret: str,
    scopes: list[str],
):
    credentials = get_google_credentials(
        access_token,
        refresh_token,
        client_id,
        client_secret,
        scopes,
    )

    return build(
        "sheets",
        "v4",
        credentials=credentials,
        cache_discovery=False,
    )


def extract_spreadsheet_id(resource: str) -> Optional[str]:
    """
    Extract a spreadsheet ID from:

    https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit

    or accept a raw spreadsheet ID.
    """

    if not resource:
        return None

    resource = resource.strip()

    match = re.search(
        r"/spreadsheets/d/([a-zA-Z0-9_-]+)",
        resource,
    )

    if match:
        return match.group(1)

    if re.fullmatch(
        r"[a-zA-Z0-9_-]{20,}",
        resource,
    ):
        return resource

    return None


def get_spreadsheet_metadata(
    access_token: str,
    refresh_token: Optional[str],
    client_id: str,
    client_secret: str,
    spreadsheet_id: str,
    scopes: list[str],
):
    """
    Get metadata for a Google Spreadsheet.
    """

    service = get_sheets_service(
        access_token=access_token,
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        scopes=scopes,
    )

    metadata = (
        service.spreadsheets()
        .get(
            spreadsheetId=spreadsheet_id,
            fields=(
                "spreadsheetId,"
                "properties(title),"
                "sheets("
                "properties("
                "sheetId,"
                "title,"
                "index,"
                "gridProperties"
                ")"
                ")"
            ),
        )
        .execute()
    )

    sheets = []

    for sheet in metadata.get("sheets", []):
        properties = sheet.get("properties", {})
        grid = properties.get("gridProperties", {})

        sheets.append(
            {
                "id": properties.get("sheetId"),
                "title": properties.get("title"),
                "index": properties.get("index"),
                "row_count": grid.get("rowCount"),
                "column_count": grid.get("columnCount"),
            }
        )

    return {
        "spreadsheet_id": metadata.get("spreadsheetId"),
        "name": metadata.get("properties", {}).get("title"),
        "url": (
            "https://docs.google.com/spreadsheets/d/"
            f"{metadata.get('spreadsheetId')}/edit"
        ),
        "sheets": sheets,
    }


def resolve_spreadsheet(
    access_token: str,
    refresh_token: Optional[str],
    client_id: str,
    client_secret: str,
    resource: str,
    scopes: list[str],
):
    """
    Sheets-only resolver.

    Accepts:
      - Google Sheets URL
      - Spreadsheet ID

    The spreadsheet name is returned from Google Sheets metadata.
    """

    if not resource or not resource.strip():
        raise ValueError(
            "Please provide a Google Sheet URL or spreadsheet ID."
        )

    spreadsheet_id = extract_spreadsheet_id(resource)

    if not spreadsheet_id:
        raise ValueError(
            "Please provide the Google Sheet URL. "
            "Example: https://docs.google.com/spreadsheets/d/..."
        )

    try:
        return get_spreadsheet_metadata(
            access_token=access_token,
            refresh_token=refresh_token,
            client_id=client_id,
            client_secret=client_secret,
            spreadsheet_id=spreadsheet_id,
            scopes=scopes,
        )

    except Exception as exc:
        raise ValueError(
            f"Could not access Google Sheet: {exc}"
        ) from exc