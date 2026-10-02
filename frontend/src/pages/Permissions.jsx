import { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";

const permissionGroups = [
  {
    service: "browser",
    title: "Browser",
    actions: [
      "open_website",
      "type_text",
      "click_element",
      "search_web",
    ],
  },
  {
    service: "gmail",
    title: "Gmail",
    actions: [
      "search_emails",
      "read_email",
      "create_draft",
      "send_email",
      "trash_email",
    ],
  },
  {
    service: "google_sheets",
    title: "Google Sheets",
    actions: [
      "read_sheet",
      "update_sheet",
      "append_rows",
      "clear_range",
      "delete_row",
      "delete_column",
      "format_header_bold",
    ],
  },
];

function Permissions() {
  const [permissions, setPermissions] =
    useState([]);

  const [loading, setLoading] =
    useState(true);

  const [saving, setSaving] =
    useState("");

  const [error, setError] =
    useState("");

  async function loadPermissions() {
    const token = localStorage.getItem(
      "access_token"
    );

    if (!token) {
      window.location.href = "/login";
      return;
    }

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/permissions",
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
            "Unable to load permissions."
        );
      }

      setPermissions(
        Array.isArray(data) ? data : []
      );
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadPermissions();
  }, []);

  function isAllowed(
    service,
    action
  ) {
    return permissions.some(
      (permission) =>
        permission.service === service &&
        permission.action === action &&
        permission.allowed
    );
  }

  async function togglePermission(
    service,
    action
  ) {
    const token = localStorage.getItem(
      "access_token"
    );

    const key = `${service}:${action}`;

    try {
      setSaving(key);
      setError("");

      const allowed = !isAllowed(
        service,
        action
      );

      const response = await fetch(
        "http://127.0.0.1:8000/permissions",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            service,
            action,
            allowed: allowed ? 1 : 0,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Unable to update permission."
        );
      }

      await loadPermissions();
    } catch (error) {
      setError(error.message);
    } finally {
      setSaving("");
    }
  }

  return (
    <div className="min-h-screen bg-slate-100 flex">
      <Sidebar />

      <main className="flex-1 p-8">
        <div className="max-w-5xl">
          <h1 className="text-3xl font-bold text-slate-900">
            Permissions
          </h1>

          <p className="text-slate-500 mt-2 mb-8">
            Control which actions the autonomous
            agent is allowed to request.
          </p>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-4 mb-6">
              {error}
            </div>
          )}

          {loading ? (
            <div className="bg-white rounded-2xl p-6">
              Loading permissions...
            </div>
          ) : (
            <div className="space-y-6">
              {permissionGroups.map(
                (group) => (
                  <section
                    key={group.service}
                    className="bg-white rounded-2xl border border-slate-200 p-6"
                  >
                    <h2 className="text-xl font-semibold">
                      {group.title}
                    </h2>

                    <div className="mt-5 divide-y">
                      {group.actions.map(
                        (action) => {
                          const key = `${group.service}:${action}`;

                          const allowed =
                            isAllowed(
                              group.service,
                              action
                            );

                          return (
                            <div
                              key={action}
                              className="py-4 flex items-center justify-between gap-4"
                            >
                              <div>
                                <p className="font-medium">
                                  {action}
                                </p>

                                <p className="text-xs text-slate-500 mt-1">
                                  {allowed
                                    ? "Allowed"
                                    : "Not allowed"}
                                </p>
                              </div>

                              <button
                                type="button"
                                disabled={
                                  saving === key
                                }
                                onClick={() =>
                                  togglePermission(
                                    group.service,
                                    action
                                  )
                                }
                                className={`px-4 py-2 rounded-lg text-sm font-semibold ${
                                  allowed
                                    ? "bg-green-100 text-green-700"
                                    : "bg-slate-100 text-slate-600"
                                }`}
                              >
                                {saving === key
                                  ? "Saving..."
                                  : allowed
                                  ? "Allowed"
                                  : "Allow"}
                              </button>
                            </div>
                          );
                        }
                      )}
                    </div>
                  </section>
                )
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default Permissions;