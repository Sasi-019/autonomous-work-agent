import json
import os

from agent.planner import (
    plan_next_action,
    generate_final_answer,
)

from agent.executor import execute_tool
from database import SessionLocal

from models import (
    Connection,
    Approval,
    ToolActivity,
)

from tools.google_resources import resolve_spreadsheet


GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")


# ============================================================
# GOOGLE SCOPES
# ============================================================

# Gmail + Google Sheets are both supported.
# Browser does not need Google OAuth.

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",

    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]


SHEETS_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]


# ============================================================
# APPROVAL ACTIONS
# ============================================================

APPROVAL_ACTIONS = {
    # Google Sheets
    "update_sheet",
    "append_rows",
    "clear_range",
    "delete_row",
    "delete_column",
    "format_header_bold",

    # Gmail
    "send_email",
    "trash_email",
}


# ============================================================
# WORKSPACE TOOLS
# ============================================================

WORKSPACE_TOOLS = {

    "gmail": [
        "search_emails",
        "read_email",
        "create_draft",
        "send_email",
        "trash_email",
    ],

    "sheets": [
        "read_sheet",
        "update_sheet",
        "append_rows",
        "clear_range",
        "delete_column",
        "delete_row",
        "format_header_bold",
        "verify_sheet",
    ],

    "browser": [
        "open_website",
        "type_text",
        "click_element",
        "search_web",
    ],
}


# ============================================================
# HELPERS
# ============================================================

def safe_arguments(arguments):
    blocked = {
        "access_token",
        "refresh_token",
        "client_secret",
        "client_id",
        "scopes",
    }

    return {
        key: value
        for key, value in arguments.items()
        if key not in blocked
    }


def create_approval(
    db,
    user_id,
    task_id,
    service,
    action,
    arguments,
):
    approval = Approval(
        service=service,
        action=action,
        details=json.dumps(
            safe_arguments(arguments),
            default=str,
        ),
        status="pending",
        user_id=user_id,
        task_id=task_id,
    )

    db.add(approval)
    db.commit()
    db.refresh(approval)

    return approval


def save_activity(
    db,
    user_id,
    task_id,
    tool,
    result,
):
    activity = ToolActivity(
        task_id=task_id,
        tool=tool,
        result=json.dumps(
            result,
            default=str,
        ),
        user_id=user_id,
    )

    db.add(activity)
    db.commit()


# ============================================================
# AGENT
# ============================================================

def run_agent(
    goal,
    user_id,
    workspace,
    task_id=None,
    resource=None,
):
    workspace = workspace.lower().strip()

    # ========================================================
    # 1. WORKSPACE VALIDATION
    # ========================================================

    if workspace not in WORKSPACE_TOOLS:
        return {
            "status": "error",
            "message": (
                f"Unsupported workspace: {workspace}"
            ),
        }

    db = SessionLocal()

    try:

        # ====================================================
        # 2. GOOGLE CONNECTION
        # ====================================================

        connection = None

        if workspace in {
            "gmail",
            "sheets",
        }:

            connection = (
                db.query(Connection)
                .filter(
                    Connection.user_id == user_id,
                    Connection.service == "google",
                    Connection.status == "connected",
                )
                .first()
            )

            if not connection:

                return {
                    "status": "needs_input",
                    "message": (
                        "Please connect your Google "
                        "account before using this workspace."
                    ),
                }

        # ====================================================
        # 3. GOOGLE SHEETS RESOURCE
        # ====================================================

        spreadsheet_id = None
        spreadsheet_name = None

        if workspace == "sheets":

            if not resource:

                return {
                    "status": "needs_input",
                    "message": (
                        "Please provide a Google Sheet URL "
                        "or spreadsheet ID."
                    ),
                }

            try:

                resolved = resolve_spreadsheet(
                    resource=resource,
                    access_token=connection.access_token,
                    refresh_token=connection.refresh_token,
                    client_id=GOOGLE_CLIENT_ID,
                    client_secret=GOOGLE_CLIENT_SECRET,
                    scopes=SHEETS_SCOPES,
                )

            except Exception as exc:

                return {
                    "status": "error",
                    "message": str(exc),
                }

            spreadsheet_id = resolved[
                "spreadsheet_id"
            ]

            spreadsheet_name = resolved.get(
                "name",
                "Google Sheet",
            )

        # ====================================================
        # 4. AGENT PLANNING LOOP
        # ====================================================

        previous_result = None

        for step in range(1, 8):

            plan = plan_next_action(
                goal=goal,
                available_tools=WORKSPACE_TOOLS[
                    workspace
                ],
                previous_result=previous_result,
                spreadsheet_id=spreadsheet_id,
            )

            tool_name = plan.get("tool")

            arguments = (
                plan.get("arguments")
                or {}
            )

            reason = plan.get(
                "reason"
            )

            planner_message = plan.get(
                "message"
            )

            # ------------------------------------------------
            # NEEDS INPUT
            # ------------------------------------------------

            if reason == "needs_input":

                return {
                    "status": "needs_input",
                    "message": (
                        planner_message
                        or "The agent needs more information."
                    ),
                }

            # ------------------------------------------------
            # COMPLETED
            # ------------------------------------------------

            if (
                tool_name is None
                and reason == "completed"
            ):

                final_answer = (
                    generate_final_answer(
                        goal,
                        previous_result,
                    )
                )

                return {
                    "status": "completed",
                    "message": final_answer,
                    "result": previous_result,
                }

            # ------------------------------------------------
            # INVALID PLANNER RESPONSE
            # ------------------------------------------------

            if tool_name is None:

                return {
                    "status": "error",
                    "message": (
                        "The planner did not provide "
                        "a valid next action."
                    ),
                }

            # ------------------------------------------------
            # TOOL SECURITY
            # ------------------------------------------------

            if (
                tool_name
                not in WORKSPACE_TOOLS[workspace]
            ):

                return {
                    "status": "error",
                    "message": (
                        f"Tool '{tool_name}' is not allowed "
                        f"in {workspace}."
                    ),
                }

            # =================================================
            # GOOGLE SHEETS
            # =================================================

            if workspace == "sheets":

                arguments[
                    "spreadsheet_id"
                ] = spreadsheet_id

                # ---------------------------------------------
                # MUTATION → HUMAN APPROVAL
                # ---------------------------------------------

                if (
                    tool_name
                    in APPROVAL_ACTIONS
                ):

                    approval = create_approval(
                        db=db,
                        user_id=user_id,
                        task_id=task_id,
                        service="google_sheets",
                        action=tool_name,
                        arguments=arguments,
                    )

                    return {
                        "status": "approval_required",
                        "message": (
                            "The agent needs your "
                            "approval before modifying "
                            "the spreadsheet."
                        ),
                        "approval_id": approval.id,
                        "action": tool_name,
                        "details": safe_arguments(
                            arguments
                        ),
                        "spreadsheet": (
                            spreadsheet_name
                        ),
                    }

                # ---------------------------------------------
                # READ / VERIFY
                # ---------------------------------------------

                tool_arguments = {
                    **arguments,

                    "access_token": (
                        connection.access_token
                    ),
                    "refresh_token": (
                        connection.refresh_token
                    ),
                    "client_id": (
                        GOOGLE_CLIENT_ID
                    ),
                    "client_secret": (
                        GOOGLE_CLIENT_SECRET
                    ),
                    "scopes": SHEETS_SCOPES,
                }

                result = execute_tool(
                    tool_name,
                    tool_arguments,
                )

            # =================================================
            # GMAIL
            # =================================================

            elif workspace == "gmail":

                # ---------------------------------------------
                # MUTATION → HUMAN APPROVAL
                # ---------------------------------------------

                if (
                    tool_name
                    in APPROVAL_ACTIONS
                ):

                    approval = create_approval(
                        db=db,
                        user_id=user_id,
                        task_id=task_id,
                        service="gmail",
                        action=tool_name,
                        arguments=arguments,
                    )

                    return {
                        "status": "approval_required",
                        "message": (
                            "The agent needs your "
                            "approval before performing "
                            "this Gmail action."
                        ),
                        "approval_id": approval.id,
                        "action": tool_name,
                        "details": safe_arguments(
                            arguments
                        ),
                    }

                # ---------------------------------------------
                # READ / NON-DESTRUCTIVE
                # ---------------------------------------------

                tool_arguments = {
    **arguments,
    "access_token": connection.access_token,
    "refresh_token": connection.refresh_token,
    "client_id": GOOGLE_CLIENT_ID,
    "client_secret": GOOGLE_CLIENT_SECRET,
}

                result = execute_tool(
                    tool_name,
                    tool_arguments,
                )

            # =================================================
            # BROWSER
            # =================================================

            elif workspace == "browser":

                # Browser does not use Google OAuth.

                result = execute_tool(
                    tool_name,
                    arguments,
                )

            # =================================================
            # SAVE ACTIVITY
            # =================================================

            save_activity(
                db=db,
                user_id=user_id,
                task_id=task_id,
                tool=tool_name,
                result=result,
            )

            previous_result = result

            # =================================================
            # TOOL FAILURE
            # =================================================

            if (
                isinstance(result, dict)
                and result.get("success") is False
            ):

                return {
                    "status": "failed",
                    "message": result.get(
                        "message",
                        "Tool execution failed.",
                    ),
                    "result": result,
                }

        # ====================================================
        # MAX STEPS
        # ====================================================

        return {
            "status": "failed",
            "message": (
                "The agent reached its maximum "
                "number of planning steps without "
                "completing the requested task."
            ),
            "result": previous_result,
        }

    except Exception as exc:

        return {
            "status": "error",
            "message": str(exc),
        }

    finally:

        db.close()