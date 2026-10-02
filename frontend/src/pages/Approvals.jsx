import { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";

function Approvals() {
  const [approvals, setApprovals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [processingId, setProcessingId] = useState(null);

  function getToken() {
    return localStorage.getItem("access_token");
  }

  async function loadApprovals() {
    const token = getToken();

    if (!token) {
      window.location.href = "/login";
      return;
    }

    try {
      setLoading(true);
      setError("");

      const response = await fetch(
        "https://autonomous-work-agent.onrender.com/approvals",
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Failed to load approvals."
        );
      }

      setApprovals(
        Array.isArray(data) ? data : []
      );
    } catch (error) {
      console.error(
        "Approvals loading error:",
        error
      );

      setError(
        error.message ||
          "Failed to load approvals."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadApprovals();
  }, []);

  async function decideApproval(
    approvalId,
    decision
  ) {
    const token = getToken();

    if (!token) {
      window.location.href = "/login";
      return;
    }

    try {
      setProcessingId(approvalId);
      setError("");

      const response = await fetch(
        `https://autonomous-work-agent.onrender.com/approvals/${approvalId}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            status: decision,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            data.message ||
            "Approval action failed."
        );
      }

      await loadApprovals();
    } catch (error) {
      console.error(
        "Approval decision error:",
        error
      );

      setError(
        error.message ||
          "Approval action failed."
      );
    } finally {
      setProcessingId(null);
    }
  }

  /*
   * Safely convert approval details into
   * something React can display.
   */
  function formatDetails(details) {
    if (
      details === null ||
      details === undefined
    ) {
      return "No details provided.";
    }

    // Already an object
    if (typeof details === "object") {
      return JSON.stringify(
        details,
        null,
        2
      );
    }

    // JSON stored as a string
    if (typeof details === "string") {
      try {
        const parsed = JSON.parse(details);

        if (
          parsed !== null &&
          typeof parsed === "object"
        ) {
          return JSON.stringify(
            parsed,
            null,
            2
          );
        }

        return String(parsed);
      } catch {
        return details;
      }
    }

    return String(details);
  }

  return (
    <div className="min-h-screen bg-slate-100 flex">
      <Sidebar />

      <main className="flex-1 p-8">
        <div className="max-w-5xl mx-auto">

          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-slate-900">
              Approvals
            </h1>

            <p className="text-slate-500 mt-2">
              Review actions before the agent performs
              potentially destructive changes.
            </p>
          </div>

          {/* Error */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-4 mb-6">
              <p className="font-semibold">
                Error
              </p>

              <p className="text-sm mt-1">
                {error}
              </p>
            </div>
          )}

          {/* Loading */}
          {loading ? (
            <div className="bg-white rounded-2xl border border-slate-200 p-8">
              <p className="text-slate-500">
                Loading approvals...
              </p>
            </div>
          ) : approvals.length === 0 ? (
            /* Empty state */
            <div className="bg-white rounded-2xl border border-slate-200 p-10 text-center">
              <div className="text-5xl mb-4">
                ✓
              </div>

              <h2 className="text-xl font-semibold text-slate-900">
                No pending approvals
              </h2>

              <p className="text-slate-500 mt-2">
                Actions requiring your approval will
                appear here.
              </p>

              <button
                type="button"
                onClick={loadApprovals}
                className="mt-6 bg-slate-900 hover:bg-slate-800 text-white px-5 py-2.5 rounded-lg font-medium"
              >
                Refresh
              </button>
            </div>
          ) : (
            /* Approval cards */
            <div className="space-y-5">

              {approvals.map((approval) => (
                <div
                  key={approval.id}
                  className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm"
                >

                  {/* Top section */}
                  <div className="flex justify-between gap-4">

                    <div>
                      <span className="inline-block bg-amber-100 text-amber-700 px-3 py-1 rounded-full text-sm font-medium">
                        Approval required
                      </span>

                      <h2 className="text-2xl font-semibold text-slate-900 mt-3">
                        {approval.action}
                      </h2>

                      <p className="text-slate-500 mt-1">
                        Service:{" "}
                        {approval.service}
                      </p>

                      {approval.task_id !==
                        null &&
                        approval.task_id !==
                          undefined && (
                          <p className="text-xs text-slate-400 mt-1">
                            Task #
                            {approval.task_id}
                          </p>
                        )}
                    </div>

                    <span className="text-slate-400">
                      #{approval.id}
                    </span>

                  </div>

                  {/* Details */}
                  <div className="mt-5 bg-slate-50 rounded-xl p-4 border border-slate-100">

                    <p className="font-semibold text-slate-700 mb-2">
                      Action details
                    </p>

                    <pre className="text-sm text-slate-600 whitespace-pre-wrap break-words overflow-x-auto">
                      {formatDetails(
                        approval.details
                      )}
                    </pre>

                  </div>

                  {/* Buttons */}
                  <div className="mt-5 flex flex-col sm:flex-row gap-3">

                    <button
                      type="button"
                      disabled={
                        processingId ===
                        approval.id
                      }
                      onClick={() =>
                        decideApproval(
                          approval.id,
                          "approved"
                        )
                      }
                      className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-slate-400 text-white font-semibold px-6 py-3 rounded-xl transition"
                    >
                      {processingId ===
                      approval.id
                        ? "Processing..."
                        : "✓ Approve"}
                    </button>

                    <button
                      type="button"
                      disabled={
                        processingId ===
                        approval.id
                      }
                      onClick={() =>
                        decideApproval(
                          approval.id,
                          "rejected"
                        )
                      }
                      className="flex-1 bg-red-600 hover:bg-red-700 disabled:bg-slate-400 text-white font-semibold px-6 py-3 rounded-xl transition"
                    >
                      {processingId ===
                      approval.id
                        ? "Processing..."
                        : "✕ Reject"}
                    </button>

                  </div>

                </div>
              ))}

            </div>
          )}

        </div>
      </main>
    </div>
  );
}

export default Approvals;