import inspect
from concurrent.futures import ThreadPoolExecutor

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
        # Run synchronous tools in a separate worker thread.
        #
        # This is important for browser automation because
        # Playwright's Sync API cannot run inside the asyncio
        # event loop used by FastAPI.
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                tool,
                **arguments
            )

            result = future.result()

        # If a tool itself returns a coroutine, execute it
        # outside the current event loop.
        if inspect.iscoroutine(result):
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    _run_coroutine,
                    result
                )

                result = future.result()

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


def _run_coroutine(coroutine):
    import asyncio

    return asyncio.run(coroutine)