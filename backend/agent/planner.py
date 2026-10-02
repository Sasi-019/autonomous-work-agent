import json

from agent.llm import ask_llm


def plan_next_action(
    goal,
    available_tools,
    previous_result=None,
    spreadsheet_id=None,
):
    """
    Decide the next action for the autonomous agent.

    The planner decides WHAT should happen next.
    The application remains responsible for:
    - injecting the real spreadsheet ID
    - authentication
    - authorization
    - human approval
    - tool execution
    """

    spreadsheet_context = (
        spreadsheet_id
        if spreadsheet_id
        else "NOT_AVAILABLE"
    )

    prompt = f"""
You are the planning brain of an autonomous work agent.

USER GOAL:
{goal}

AVAILABLE TOOLS:
{json.dumps(available_tools)}

PREVIOUS TOOL RESULT:
{json.dumps(previous_result, default=str)}

GOOGLE SHEETS CONTEXT:
The application supplied this real spreadsheet ID:

{spreadsheet_context}

============================================================
STRICT RULES
============================================================

1. Choose ONLY a tool from AVAILABLE TOOLS.

2. Return ONLY valid JSON.

3. Never invent, guess, replace, or generate a spreadsheet ID.

4. If a Sheets action is required, use EXACTLY:

{spreadsheet_context}

5. Never use:
- "SPREADSHEET_ID"
- "<SPREADSHEET_ID>"
- "USE_PROVIDED_SPREADSHEET_ID"
- "your spreadsheet id"
- fake/example IDs

6. If the goal requires another action after the previous
   tool result, return the NEXT tool.

7. If the goal is actually completed, return:

{{
  "tool": null,
  "arguments": {{}},
  "reason": "completed",
  "message": "Task completed."
}}

8. If information from the user is genuinely required, return:

{{
  "tool": null,
  "arguments": {{}},
  "reason": "needs_input",
  "message": "Explain exactly what information is required."
}}

9. Otherwise return:

{{
  "tool": "tool_name",
  "arguments": {{}},
  "reason": "continue",
  "message": "Why this action is the next step."
}}

============================================================
SHEETS TOOLS
============================================================

read_sheet:
{{
  "spreadsheet_id": "{spreadsheet_context}",
  "range_name": "Sheet1!A1:ZZ1000"
}}

update_sheet:
{{
  "spreadsheet_id": "{spreadsheet_context}",
  "range_name": "Sheet1!C2",
  "values": [["Yes"]]
}}

append_rows:
{{
  "spreadsheet_id": "{spreadsheet_context}",
  "range_name": "Sheet1!A:Z",
  "values": [["Name", "Email", "Status"]]
}}

clear_range:
{{
  "spreadsheet_id": "{spreadsheet_context}",
  "range_name": "Sheet1!A1:E10"
}}

delete_row:
{{
  "spreadsheet_id": "{spreadsheet_context}",
  "range_name": "Sheet1!A5:E5",
  "row_index": 4
}}

delete_column:
{{
  "spreadsheet_id": "{spreadsheet_context}",
  "range_name": "Sheet1!C:C",
  "column_index": 2
}}

format_header_bold:
{{
  "spreadsheet_id": "{spreadsheet_context}",
  "range_name": "Sheet1!A1:E1"
}}

verify_sheet:
{{
  "spreadsheet_id": "{spreadsheet_context}",
  "range_name": "Sheet1!A1:E10",
  "expected_values": [["Name", "Email"]]
}}

============================================================
GMAIL TOOLS
============================================================

search_emails:
{{
  "query": "from:someone@example.com"
}}

read_email:
{{
  "message_id": "MESSAGE_ID"
}}

create_draft:
{{
  "to": "person@example.com",
  "subject": "Subject",
  "body": "Email body"
}}

send_email:
{{
  "to": "person@example.com",
  "subject": "Subject",
  "body": "Email body"
}}

trash_email:
{{
  "message_id": "MESSAGE_ID"
}}

Gmail rules:

- search_emails = read-only
- read_email = read-only
- create_draft = reversible
- send_email = requires human approval
- trash_email = requires human approval

============================================================
BROWSER TOOLS
============================================================

open_website:
{{
  "url": "https://example.com"
}}

type_text:
{{
  "url": "https://example.com",
  "target": "Search",
  "text": "example text",
  "submit": true
}}

click_element:
{{
  "url": "https://example.com",
  "target": "Search"
}}

search_web:
{{
  "query": "machine learning"
}}

============================================================
BROWSER IMPORTANT RULE
============================================================

For a goal such as:

"Search Google for IIIT Surat"

use:

{{
  "tool": "search_web",
  "arguments": {{
    "query": "IIIT Surat"
  }},
  "reason": "continue",
  "message": "Search Google for IIIT Surat."
}}

Do NOT manually use:
type_text with target "Search"
for Google searches when search_web is available.

The search_web tool performs the complete Google search.

============================================================
MULTI-STEP TASKS
============================================================

The agent must not declare completion merely because a website
was opened.

Example:

USER:
"Search Google for IIIT Surat"

Correct sequence:

1. search_web
2. inspect the result
3. if successful, completed

Example:

USER:
"Open Google and search for machine learning"

Correct sequence:

1. search_web
2. verify successful navigation/search
3. completed

Example:

USER:
"Find emails from Alice"

Correct sequence:

1. search_emails
2. inspect result
3. completed if the requested information was found

Example:

USER:
"Read the latest email from Alice"

Correct sequence:

1. search_emails
2. identify the required message
3. read_email
4. completed

============================================================
GOOGLE SHEETS MULTI-STEP RULE
============================================================

For a request such as:

"Add a column at the end and mark every person Excellent"

FIRST use:

read_sheet

Then inspect the actual result.

Determine:
- existing columns
- actual last used column
- next available column
- header row
- relevant person/data rows

Then use update_sheet.

Do NOT assume the sheet ends at column E.

Do NOT overwrite existing columns.

After a mutation, use verify_sheet when possible.

============================================================
FINAL JSON
============================================================

Return exactly one JSON object.

Required fields:

- tool
- arguments
- reason
- message
"""

    response = ask_llm(prompt)

    if not response:
        raise ValueError(
            "LLM returned an empty response."
        )

    start = response.find("{")
    end = response.rfind("}") + 1

    if start == -1 or end <= start:
        raise ValueError(
            "LLM did not return valid JSON."
        )

    try:
        result = json.loads(
            response[start:end]
        )
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"LLM returned invalid JSON: {exc}"
        ) from exc

    if not isinstance(result, dict):
        raise ValueError(
            "Planner response must be a JSON object."
        )

    tool_name = result.get("tool")

    arguments = result.get(
        "arguments",
        {},
    )

    reason = result.get(
        "reason",
        "continue",
    )

    message = result.get(
        "message",
        "",
    )

    if arguments is None:
        arguments = {}

    if not isinstance(arguments, dict):
        raise ValueError(
            "Planner arguments must be a JSON object."
        )

    valid_reasons = {
        "completed",
        "needs_input",
        "continue",
    }

    if reason not in valid_reasons:
        raise ValueError(
            f"Planner returned invalid reason: {reason}"
        )

    if (
        tool_name is not None
        and tool_name not in available_tools
    ):
        raise ValueError(
            f"Planner selected unavailable tool: "
            f"{tool_name}"
        )

    return {
        "tool": tool_name,
        "arguments": arguments,
        "reason": reason,
        "message": message,
    }


def generate_final_answer(
    goal,
    previous_result,
):
    prompt = f"""
The user's goal was:

{goal}

The final tool result was:

{json.dumps(previous_result, default=str)}

Give a short confirmation of what was actually completed.

IMPORTANT:

Do not claim that an action was completed if the tool result
indicates failure.

If the tool result indicates failure, clearly state that the
action failed.
"""

    return ask_llm(prompt)