import { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";

function History() {
  const [history, setHistory] =
    useState([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  useEffect(() => {
    async function loadHistory() {
      const token = localStorage.getItem(
        "access_token"
      );

      if (!token) {
        window.location.href = "/login";
        return;
      }

      try {
        const response = await fetch(
          "https://autonomous-work-agent.onrender.com/history",
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        const data = await response.json();

        if (!response.ok) {
          throw new Error(
            data.detail ||
              "Unable to load history."
          );
        }

        setHistory(
          Array.isArray(data)
            ? data
            : []
        );
      } catch (error) {
        setError(error.message);
      } finally {
        setLoading(false);
      }
    }

    loadHistory();
  }, []);

  return (
    <div className="min-h-screen bg-slate-100 flex">
      <Sidebar />

      <main className="flex-1 p-8">
        <div className="max-w-5xl">
          <h1 className="text-3xl font-bold text-slate-900">
            History
          </h1>

          <p className="text-slate-500 mt-2 mb-8">
            View actions performed by your agent.
          </p>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-4">
              {error}
            </div>
          )}

          {loading ? (
            <div className="bg-white rounded-2xl p-6">
              Loading history...
            </div>
          ) : history.length === 0 ? (
            <div className="bg-white rounded-2xl border border-slate-200 p-8">
              <h2 className="text-xl font-semibold">
                No activity yet
              </h2>

              <p className="text-slate-500 mt-2">
                Tool activity will appear here after
                your agent starts working.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {history.map((item) => (
                <div
                  key={item.id}
                  className="bg-white rounded-2xl border border-slate-200 p-5"
                >
                  <div className="flex justify-between">
                    <div>
                      <p className="text-xs text-slate-400">
                        TASK #{item.task_id}
                      </p>

                      <h2 className="font-semibold mt-1">
                        {item.tool}
                      </h2>
                    </div>

                    <span className="text-xs text-slate-400">
                      Activity #{item.id}
                    </span>
                  </div>

                  <pre className="mt-4 bg-slate-50 rounded-xl p-4 text-xs whitespace-pre-wrap overflow-auto">
                    {(() => {
                      try {
                        return JSON.stringify(
                          JSON.parse(
                            item.result || "{}"
                          ),
                          null,
                          2
                        );
                      } catch {
                        return item.result;
                      }
                    })()}
                  </pre>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default History;