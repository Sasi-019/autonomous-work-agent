import { useState } from "react";
import Sidebar from "../components/Sidebar";

function Tasks() {
  const [workspace, setWorkspace] =
    useState("browser");

  const [goal, setGoal] = useState("");
  const [resource, setResource] = useState("");

  const [loading, setLoading] =
    useState(false);

  const [result, setResult] =
    useState(null);

  const [error, setError] =
    useState("");

  const runTask = async (event) => {
    event.preventDefault();

    if (!goal.trim()) {
      setError("Please enter a task.");
      return;
    }

    if (
      workspace === "sheets" &&
      !resource.trim()
    ) {
      setError(
        "Please provide a Google Sheet URL or name."
      );
      return;
    }

    const token = localStorage.getItem(
      "access_token"
    );

    if (!token) {
      setError(
        "You are not logged in."
      );
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/tasks",
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

      setResult(data);
    } catch (error) {
      setError(
        error.message ||
          "Task execution failed."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-100 flex">
      <Sidebar />

      <main className="flex-1 p-8">
        <div className="max-w-4xl">
          <h1 className="text-3xl font-bold text-slate-900">
            Tasks
          </h1>

          <p className="text-slate-500 mt-2 mb-8">
            Give the autonomous agent a goal.
          </p>

          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
            <form
              onSubmit={runTask}
              className="space-y-6"
            >
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">
                  Workspace
                </label>

                <select
                  value={workspace}
                  onChange={(event) => {
                    setWorkspace(
                      event.target.value
                    );
                    setResource("");
                  }}
                  className="w-full border border-slate-300 rounded-xl px-4 py-3 bg-white"
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
                      setResource(
                        event.target.value
                      )
                    }
                    placeholder="Paste Google Sheet URL or enter sheet name"
                    className="w-full border border-slate-300 rounded-xl px-4 py-3"
                  />

                  <p className="text-xs text-slate-500 mt-2">
                    The agent will resolve the spreadsheet
                    using your connected Google account.
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
                      ? "Search Google for machine learning"
                      : workspace === "sheets"
                      ? "Add a column named Excellent"
                      : "Read my recent emails"
                  }
                  rows={5}
                  className="w-full border border-slate-300 rounded-xl px-4 py-3 resize-none"
                />
              </div>

              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-4">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="bg-amber-500 hover:bg-amber-600 disabled:bg-slate-400 text-slate-950 font-semibold px-6 py-3 rounded-xl"
              >
                {loading
                  ? "Agent is working..."
                  : "Run Task"}
              </button>
            </form>
          </div>

          {result && (
            <div className="mt-6 bg-white rounded-2xl border border-slate-200 p-6">
              <h2 className="text-xl font-bold">
                Agent Result
              </h2>

              <div className="mt-5 space-y-3 text-sm">
                <p>
                  <strong>Status:</strong>{" "}
                  {result.status}
                </p>

                <p>
                  <strong>Workspace:</strong>{" "}
                  {result.workspace ||
                    workspace}
                </p>

                {result.resource && (
                  <p className="break-all">
                    <strong>Resource:</strong>{" "}
                    {result.resource}
                  </p>
                )}

                {result.message && (
                  <div className="bg-slate-50 rounded-xl p-4">
                    <strong>Message</strong>

                    <p className="mt-1 text-slate-700">
                      {result.message}
                    </p>
                  </div>
                )}

                {result.approval_id && (
                  <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
                    <p className="font-semibold text-amber-800">
                      Approval Required
                    </p>

                    <p className="text-amber-700 mt-1">
                      Open the Approvals page to
                      review this action.
                    </p>
                  </div>
                )}

                {result.matches && (
                  <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
                    <p className="font-semibold">
                      Multiple spreadsheets found
                    </p>

                    <p className="text-sm mt-1">
                      Use the spreadsheet URL to
                      select the exact file.
                    </p>

                    <div className="mt-3 space-y-2">
                      {result.matches.map(
                        (item) => (
                          <div
                            key={item.id}
                            className="bg-white rounded-lg p-3"
                          >
                            <p className="font-medium">
                              {item.name}
                            </p>

                            <p className="text-xs text-slate-500 break-all">
                              {item.url}
                            </p>
                          </div>
                        )
                      )}
                    </div>
                  </div>
                )}

                {result.result && (
                  <pre className="bg-slate-950 text-slate-100 rounded-xl p-4 overflow-auto text-xs">
                    {typeof result.result ===
                    "string"
                      ? result.result
                      : JSON.stringify(
                          result.result,
                          null,
                          2
                        )}
                  </pre>
                )}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default Tasks;