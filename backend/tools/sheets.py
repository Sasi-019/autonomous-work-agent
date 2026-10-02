from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


def get_credentials(
    access_token,
    refresh_token=None,
    client_id=None,
    client_secret=None,
    scopes=None
):
    return Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=scopes
    )


def get_service(
    access_token,
    refresh_token,
    client_id,
    client_secret,
    scopes
):
    credentials = get_credentials(
        access_token,
        refresh_token,
        client_id,
        client_secret,
        scopes
    )

    return build(
        "sheets",
        "v4",
        credentials=credentials
    )


def get_sheet_id(
    service,
    spreadsheet_id,
    range_name
):
    metadata = (
        service.spreadsheets()
        .get(
            spreadsheetId=spreadsheet_id,
            fields="sheets.properties"
        )
        .execute()
    )

    sheets = metadata.get("sheets", [])

    if not sheets:
        raise ValueError(
            "The spreadsheet contains no sheets."
        )

    if "!" in range_name:
        sheet_name = range_name.split("!")[0].strip("'")

        for sheet in sheets:
            properties = sheet.get("properties", {})

            if properties.get("title") == sheet_name:
                return properties.get("sheetId")

        raise ValueError(
            f"Sheet tab '{sheet_name}' was not found."
        )

    return sheets[0]["properties"]["sheetId"]


def read_sheet(
    access_token,
    refresh_token,
    client_id,
    client_secret,
    scopes,
    spreadsheet_id,
    range_name
):
    service = get_service(
        access_token,
        refresh_token,
        client_id,
        client_secret,
        scopes
    )

    response = (
        service.spreadsheets()
        .values()
        .get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        )
        .execute()
    )

    return response.get("values", [])


def update_sheet(
    access_token,
    refresh_token,
    client_id,
    client_secret,
    scopes,
    spreadsheet_id,
    range_name,
    values
):
    service = get_service(
        access_token,
        refresh_token,
        client_id,
        client_secret,
        scopes
    )

    body = {
        "values": values
    }

    result = (
        service.spreadsheets()
        .values()
        .update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="USER_ENTERED",
            body=body
        )
        .execute()
    )

    return {
        "success": True,
        "updatedRange": result.get("updatedRange"),
        "updatedRows": result.get("updatedRows", 0),
        "updatedColumns": result.get(
            "updatedColumns",
            0
        ),
    }


def append_rows(
    access_token,
    refresh_token,
    client_id,
    client_secret,
    scopes,
    spreadsheet_id,
    range_name,
    values
):
    service = get_service(
        access_token,
        refresh_token,
        client_id,
        client_secret,
        scopes
    )

    body = {
        "values": values
    }

    result = (
        service.spreadsheets()
        .values()
        .append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body=body
        )
        .execute()
    )

    return {
        "success": True,
        "updatedRange": result.get("updates", {}).get(
            "updatedRange"
        ),
        "updatedRows": result.get("updates", {}).get(
            "updatedRows",
            0
        ),
    }


def clear_range(
    access_token,
    refresh_token,
    client_id,
    client_secret,
    scopes,
    spreadsheet_id,
    range_name
):
    service = get_service(
        access_token,
        refresh_token,
        client_id,
        client_secret,
        scopes
    )

    result = (
        service.spreadsheets()
        .values()
        .clear(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            body={}
        )
        .execute()
    )

    return {
        "success": True,
        "clearedRange": result.get("clearedRange")
    }


def delete_column(
    access_token,
    refresh_token,
    client_id,
    client_secret,
    scopes,
    spreadsheet_id,
    range_name,
    column_index
):
    service = get_service(
        access_token,
        refresh_token,
        client_id,
        client_secret,
        scopes
    )

    sheet_id = get_sheet_id(
        service,
        spreadsheet_id,
        range_name
    )

    request_body = {
        "requests": [
            {
                "deleteDimension": {
                    "range": {
                        "sheetId": sheet_id,
                        "dimension": "COLUMNS",
                        "startIndex": column_index,
                        "endIndex": column_index + 1
                    }
                }
            }
        ]
    }

    (
        service.spreadsheets()
        .batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=request_body
        )
        .execute()
    )

    return {
        "success": True,
        "deletedColumnIndex": column_index
    }


def delete_row(
    access_token,
    refresh_token,
    client_id,
    client_secret,
    scopes,
    spreadsheet_id,
    range_name,
    row_index
):
    service = get_service(
        access_token,
        refresh_token,
        client_id,
        client_secret,
        scopes
    )

    sheet_id = get_sheet_id(
        service,
        spreadsheet_id,
        range_name
    )

    request_body = {
        "requests": [
            {
                "deleteDimension": {
                    "range": {
                        "sheetId": sheet_id,
                        "dimension": "ROWS",
                        "startIndex": row_index,
                        "endIndex": row_index + 1
                    }
                }
            }
        ]
    }

    (
        service.spreadsheets()
        .batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=request_body
        )
        .execute()
    )

    return {
        "success": True,
        "deletedRowIndex": row_index
    }


def format_header_bold(
    access_token,
    refresh_token,
    client_id,
    client_secret,
    scopes,
    spreadsheet_id,
    range_name
):
    service = get_service(
        access_token,
        refresh_token,
        client_id,
        client_secret,
        scopes
    )

    sheet_id = get_sheet_id(
        service,
        spreadsheet_id,
        range_name
    )

    request_body = {
        "requests": [
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 0,
                        "endRowIndex": 1
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "textFormat": {
                                "bold": True
                            }
                        }
                    },
                    "fields": (
                        "userEnteredFormat."
                        "textFormat.bold"
                    )
                }
            }
        ]
    }

    (
        service.spreadsheets()
        .batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=request_body
        )
        .execute()
    )

    return {
        "success": True,
        "message": "Header formatted in bold"
    }


def verify_sheet(
    access_token,
    refresh_token,
    client_id,
    client_secret,
    scopes,
    spreadsheet_id,
    range_name,
    expected_values
):
    actual_values = read_sheet(
        access_token=access_token,
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        scopes=scopes,
        spreadsheet_id=spreadsheet_id,
        range_name=range_name
    )

    if not expected_values:
        return {
            "success": True,
            "verified": True
        }

    if len(actual_values) < len(expected_values):
        return {
            "success": True,
            "verified": False
        }

    for row_index, expected_row in enumerate(
        expected_values
    ):
        actual_row = actual_values[row_index]

        if len(actual_row) < len(expected_row):
            return {
                "success": True,
                "verified": False
            }

        if actual_row[:len(expected_row)] != expected_row:
            return {
                "success": True,
                "verified": False
            }

    return {
        "success": True,
        "verified": True
    }