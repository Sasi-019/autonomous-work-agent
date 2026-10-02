from tools.sheets import (
    read_sheet,
    update_sheet,
    append_rows,
    clear_range,
    delete_column,
    delete_row,
    format_header_bold,
    verify_sheet
)

from tools.browser import (
    open_website,
    type_text,
    click_element,
    search_web
)

from tools.gmail import (
    search_emails,
    read_email,
    create_draft,
    send_email,
    trash_email
)


TOOLS = {
    "read_sheet": read_sheet,
    "update_sheet": update_sheet,
    "append_rows": append_rows,
    "clear_range": clear_range,
    "delete_column": delete_column,
    "delete_row": delete_row,
    "format_header_bold": format_header_bold,
    "verify_sheet": verify_sheet,

    "open_website": open_website,
    "type_text": type_text,
    "click_element": click_element,
    "search_web": search_web,

    "search_emails": search_emails,
    "read_email": read_email,
    "create_draft": create_draft,
    "send_email": send_email,
    "trash_email": trash_email,
}


def get_tool(tool_name):
    return TOOLS.get(tool_name)


def get_available_tools():
    return list(TOOLS.keys())