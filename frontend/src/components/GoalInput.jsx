import { useState } from "react";

function GoalInput({ onTaskCreated }) {
  const [workspace, setWorkspace] = useState("browser");
  const [goal, setGoal] = useState("");
  const [resource, setResource] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleStartTask() {
    if (!goal.trim()) {
      setError("Please enter a task.");
      return;
    }

    if (workspace === "sheets" && !resource.trim()) {
      setError(
        "Please enter a Google Sheet URL or sheet name."
      );
      return;
    }

    const token = localStorage.getItem(
      "access_token"
    );

    if (!token) {
      setError(
        "You are not logged in. Please login again."
      );
      return;
    }

    try {
      setLoading(true);
      setError("");

      const response = await fetch(
        "https://autonomous-work-agent.onrender.com/tasks",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            workspace,
            goal,
            resource:
              resource.trim() || null,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            data.message ||
            "Task failed."
        );
      }

      onTaskCreated(data);

      setGoal("");

      if (workspace === "sheets") {
        setResource("");
      }
    } catch (error) {
      console.error(
        "Task creation error:",
        error
      );

      setError(
        error.message ||
          "Unable to create task."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
      <div className="mb-6">
        <p className="text-sm font-semibold text-amber-600">
          AUTONOMOUS TASK
        </p>

        <h2 className="text-xl font-semibold text-slate-900 mt-1">
          What do you want me to do?
        </h2>

        <p className="text-sm text-slate-500 mt-1">
          The agent plans the required actions and
          asks for approval before risky changes.
        </p>
      </div>

      <div className="space-y-5">
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-2">
            Workspace
          </label>

          <select
            value={workspace}
            onChange={(event) =>
              setWorkspace(event.target.value)
            }
            className="w-full border border-slate-300 rounded-xl px-4 py-3 bg-white outline-none focus:ring-2 focus:ring-amber-400"
          >
            <option value="browser">
              Browser
            </option>

            <option value="gmail">
              Gmail
            </option>

            <option value="sheets">
              Google Sheets
            </option>
          </select>
        </div>

        {workspace === "sheets" && (
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-2">
              Google Sheet
            </label>

            <input
              value={resource}
              onChange={(event) =>
                setResource(event.target.value)
              }
              placeholder="Paste Sheet URL or enter sheet name"
              className="w-full border border-slate-300 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-amber-400"
            />

            <p className="text-xs text-slate-500 mt-2">
              Example: https://docs.google.com/spreadsheets/d/...
              or simply "Student Marks"
            </p>
          </div>
        )}

        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-2">
            What should the agent do?
          </label>

          <textarea
            value={goal}
            onChange={(event) =>
              setGoal(event.target.value)
            }
            placeholder={
              workspace === "browser"
                ? "Example: Search Google for machine learning"
                : workspace === "sheets"
                ? "Example: Add a column named Excellent"
                : "Example: Read my recent emails and summarize them"
            }
            rows={4}
            className="w-full border border-slate-300 rounded-xl px-4 py-3 outline-none resize-none focus:ring-2 focus:ring-amber-400"
          />
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-4 text-sm">
            {error}
          </div>
        )}

        <button
          type="button"
          onClick={handleStartTask}
          disabled={loading}
          className="bg-amber-500 hover:bg-amber-600 disabled:bg-slate-400 text-slate-950 font-semibold px-6 py-3 rounded-xl transition"
        >
          {loading
            ? "Agent is working..."
            : "Start Task"}
        </button>
      </div>
    </section>
  );
}

export default GoalInput;