from agent.planner import plan_next_action


goal = "I want to read my Google Sheet."

available_tools = [
    "read_sheet",
    "update_sheet"
]

decision = plan_next_action(
    goal,
    available_tools
)

print("Agent decision:")
print(decision)