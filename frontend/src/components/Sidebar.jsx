import { NavLink, useNavigate } from "react-router-dom";

function Sidebar() {
  const navigate = useNavigate();

  const links = [
    {
      path: "/dashboard",
      label: "Dashboard",
    },
    {
      path: "/tasks",
      label: "Tasks",
    },
    {
      path: "/connections",
      label: "Connections",
    },
    {
      path: "/permissions",
      label: "Permissions",
    },
    {
      path: "/approvals",
      label: "Approvals",
    },
    {
      path: "/history",
      label: "History",
    },
  ];

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user_id");
    localStorage.removeItem("user_email");

    navigate("/login");
  };

  return (
    <aside className="w-64 min-h-screen bg-slate-950 text-white p-6 flex flex-col">
      <div className="mb-10">
        <h2 className="text-xl font-bold">
          Autonomous
        </h2>

        <h2 className="text-xl font-bold text-amber-400">
          Work Agent
        </h2>

        <p className="text-xs text-slate-400 mt-2">
          AI-powered task automation
        </p>
      </div>

      <nav className="space-y-2 flex-1">
        {links.map((link) => (
          <NavLink
            key={link.path}
            to={link.path}
            className={({ isActive }) =>
              `block px-4 py-3 rounded-lg transition ${
                isActive
                  ? "bg-amber-500 text-slate-950 font-semibold"
                  : "text-slate-300 hover:bg-slate-800"
              }`
            }
          >
            {link.label}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-slate-800 pt-5">
        <p className="text-xs text-slate-500 mb-3">
          {localStorage.getItem("user_email") || "Signed in"}
        </p>

        <button
          type="button"
          onClick={logout}
          className="w-full text-left px-4 py-3 rounded-lg text-red-300 hover:bg-red-950/40"
        >
          Sign out
        </button>

        <p className="text-xs text-slate-600 mt-5">
          Secure AI Workspace
        </p>
      </div>
    </aside>
  );
}

export default Sidebar;