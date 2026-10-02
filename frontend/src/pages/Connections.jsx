import { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";

function Connections() {
  const [connections, setConnections] =
    useState([]);

  const [loading, setLoading] =
    useState(true);

  const [connecting, setConnecting] =
    useState(false);

  const [error, setError] =
    useState("");

  async function loadConnections() {
    const token = localStorage.getItem(
      "access_token"
    );

    if (!token) {
      window.location.href = "/login";
      return;
    }

    try {
      const response = await fetch(
        "https://autonomous-work-agent.onrender.com/connections",
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
            "Unable to load connections."
        );
      }

      setConnections(
        Array.isArray(data) ? data : []
      );
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadConnections();
  }, []);

  async function connectGoogle() {
    const token = localStorage.getItem(
      "access_token"
    );

    if (!token) {
      window.location.href = "/login";
      return;
    }

    try {
      setConnecting(true);
      setError("");

      const response = await fetch(
        "https://autonomous-work-agent.onrender.com/auth/google",
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
            "Google connection failed."
        );
      }

      window.location.href =
        data.authorization_url;
    } catch (error) {
      setError(error.message);
      setConnecting(false);
    }
  }

  const googleConnected =
    connections.some(
      (connection) =>
        connection.service === "google" &&
        connection.status === "connected"
    );

  return (
    <div className="min-h-screen bg-slate-100 flex">
      <Sidebar />

      <main className="flex-1 p-8">
        <div className="max-w-4xl">
          <h1 className="text-3xl font-bold text-slate-900">
            Connections
          </h1>

          <p className="text-slate-500 mt-2 mb-8">
            Connect the services your agent is
            allowed to use.
          </p>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-4 mb-6">
              {error}
            </div>
          )}

          <div className="bg-white rounded-2xl border border-slate-200 p-6">
            <div className="flex justify-between items-center gap-6">
              <div>
                <h2 className="text-xl font-semibold">
                  Google
                </h2>

                <p className="text-slate-500 text-sm mt-1">
                  Gmail and Google Sheets
                </p>
              </div>

              {loading ? (
                <span className="text-slate-400">
                  Checking...
                </span>
              ) : googleConnected ? (
                <span className="bg-green-100 text-green-700 px-4 py-2 rounded-lg font-semibold text-sm">
                  Connected
                </span>
              ) : (
                <button
                  type="button"
                  onClick={connectGoogle}
                  disabled={connecting}
                  className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-400 text-white px-5 py-3 rounded-xl font-semibold"
                >
                  {connecting
                    ? "Connecting..."
                    : "Connect Google"}
                </button>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default Connections;