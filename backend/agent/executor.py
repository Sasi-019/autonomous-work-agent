from tools.registry import get_tool


def execute_tool(
    tool_name: str,
    arguments: dict,
):
    if not tool_name:
        raise ValueError(
            "No tool name was provided."
        )

    if arguments is None:
        arguments = {}

    if not isinstance(arguments, dict):
        raise ValueError(
            "Tool arguments must be a dictionary."
        )

    tool = get_tool(tool_name)

    if tool is None:
        raise ValueError(
            f"Unknown tool: {tool_name}"
        )

    try:
        result = tool(**arguments)

        if result is None:
            return {
                "success": False,
                "message": (
                    f"Tool '{tool_name}' returned no result."
                ),
            }

        return result

    except Exception as exc:
        return {
            "success": False,
            "message": str(exc),
            "tool": tool_name,
        }