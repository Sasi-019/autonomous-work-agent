import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

function Login() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleLogin(event) {
    event.preventDefault();

    setError("");

    if (!email.trim() || !password) {
      setError("Please enter your email and password.");
      return;
    }

    try {
      setLoading(true);

      const response = await fetch(
        "http://127.0.0.1:8000/login",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            email: email.trim().toLowerCase(),
            password: password,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            data.message ||
            "Login failed. Please check your credentials."
        );
      }

      /*
       * Store the JWT using ONE consistent key.
       * The rest of the application uses access_token.
       */
      localStorage.setItem(
        "access_token",
        data.access_token
      );

      /*
       * Remove the old token key if it exists.
       */
      localStorage.removeItem("token");

      /*
       * Store user information if the backend provides it.
       */
      if (data.user) {
        if (data.user.id !== undefined) {
          localStorage.setItem(
            "user_id",
            String(data.user.id)
          );
        }

        if (data.user.email) {
          localStorage.setItem(
            "user_email",
            data.user.email
          );
        }
      }

      /*
       * If the backend returns user_id/email directly,
       * support that format too.
       */
      if (
        data.user_id !== undefined &&
        !localStorage.getItem("user_id")
      ) {
        localStorage.setItem(
          "user_id",
          String(data.user_id)
        );
      }

      if (
        data.email &&
        !localStorage.getItem("user_email")
      ) {
        localStorage.setItem(
          "user_email",
          data.email
        );
      }

      /*
       * Login successful.
       */
      navigate("/dashboard", {
        replace: true,
      });
    } catch (error) {
      console.error("Login error:", error);

      setError(
        error.message ||
          "Unable to connect to the backend."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center px-4">
      <div className="w-full max-w-md">

        {/* Brand */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white">
            Autonomous
          </h1>

          <h1 className="text-3xl font-bold text-amber-400">
            Work Agent
          </h1>

          <p className="text-slate-400 mt-3">
            AI-powered task automation
          </p>
        </div>

        {/* Login card */}
        <div className="bg-white rounded-2xl shadow-xl p-8">

          <h2 className="text-2xl font-bold text-slate-900">
            Welcome back
          </h2>

          <p className="text-slate-500 mt-2 mb-6">
            Sign in to continue to your workspace.
          </p>

          {/* Error */}
          {error && (
            <div className="mb-5 bg-red-50 border border-red-200 text-red-700 rounded-xl p-4">
              <p className="font-medium">
                Login failed
              </p>

              <p className="text-sm mt-1">
                {error}
              </p>
            </div>
          )}

          <form
            onSubmit={handleLogin}
            className="space-y-5"
          >

            {/* Email */}
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-slate-700 mb-2"
              >
                Email
              </label>

              <input
                id="email"
                type="email"
                value={email}
                onChange={(event) =>
                  setEmail(event.target.value)
                }
                placeholder="you@example.com"
                autoComplete="email"
                disabled={loading}
                className="w-full px-4 py-3 border border-slate-300 rounded-xl outline-none focus:ring-2 focus:ring-amber-400 focus:border-amber-400 disabled:bg-slate-100"
              />
            </div>

            {/* Password */}
            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-slate-700 mb-2"
              >
                Password
              </label>

              <input
                id="password"
                type="password"
                value={password}
                onChange={(event) =>
                  setPassword(event.target.value)
                }
                placeholder="Enter your password"
                autoComplete="current-password"
                disabled={loading}
                className="w-full px-4 py-3 border border-slate-300 rounded-xl outline-none focus:ring-2 focus:ring-amber-400 focus:border-amber-400 disabled:bg-slate-100"
              />
            </div>

            {/* Login button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-amber-500 hover:bg-amber-600 disabled:bg-slate-400 text-slate-950 font-bold py-3 rounded-xl transition"
            >
              {loading
                ? "Signing in..."
                : "Sign in"}
            </button>

          </form>

          {/* Register */}
          <div className="text-center mt-6">
            <p className="text-sm text-slate-500">
              Don't have an account?{" "}
              <Link
                to="/register"
                className="text-amber-600 hover:text-amber-700 font-semibold"
              >
                Create an account
              </Link>
            </p>
          </div>

        </div>

        <p className="text-center text-xs text-slate-600 mt-6">
          Secure AI Workspace
        </p>

      </div>
    </div>
  );
}

export default Login;