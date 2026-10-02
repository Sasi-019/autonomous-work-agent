# Autonomous Work Agent

An AI-powered agent that helps users complete multi-step work across authorized applications by understanding a goal, planning actions, using available tools, verifying results, and requesting human approval before consequential actions.

# 💡 Project Overview

In everyday work, users often have to perform repetitive tasks across multiple applications.

For example, a user may need to:

- Check emails
- Find relevant information
- Open a spreadsheet
- Update specific rows or columns
- Send a follow-up email
- Track what has already been completed

Doing these tasks manually requires multiple application switches, copy-pasting information, and repeated actions.

### Our Solution

**Autonomous Work Agent** allows the user to give a goal in natural language instead of manually performing every step.

For example:

> "Check the relevant emails and update the corresponding rows in my Google Sheet."

The agent is designed to:

1. Understand the user's goal.
2. Break the goal into required steps.
3. Decide which tool or application is needed.
4. Execute the selected action.
5. Receive the result from the tool.
6. Update its task state.
7. Verify the progress.
8. Ask the user for approval before consequential actions.
9. Continue until the task is completed or human intervention is required.

The system is designed around the idea:

> **Give a goal → Agent plans → Agent acts → Agent verifies → Human approves important actions → Task completed**

---

# 🧩 How Our Application Works

The application follows a simple workflow.

```text
Login
   ↓
Connect Applications
   ↓
Authorize Permissions
   ↓
Give a Goal
   ↓
Agent Understands Goal
   ↓
Agent Plans Next Action
   ↓
Select Appropriate Tool
   ↓
Execute Action
   ↓
Verify Result
   ↓
Human Approval (if required)
   ↓
Complete Task
```
