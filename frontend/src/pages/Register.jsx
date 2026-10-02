import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

function Register() {
  const navigate = useNavigate();

  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [confirmPassword, setConfirmPassword] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  async function handleRegister(event) {
    event.preventDefault();

    if (password !== confirmPassword) {
      setError(
        "Passwords do not match."
      );
      return;
    }

    if (password.length < 6) {
      setError(
        "Password must contain at least 6 characters."
      );
      return;
    }

    try {
      setLoading(true);
      setError("");

      const response = await fetch(
        "http://127.0.0.1:8000/register",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            email,
            password,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Registration failed."
        );
      }

      navigate("/login");
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center px-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-xl p-8">
        <h1 className="text-3xl font-bold text-center">
          Create Account
        </h1>

        <p className="text-slate-500 text-center mt-2 mb-8">
          Create your autonomous workspace
        </p>

        <form
          onSubmit={handleRegister}
          className="space-y-4"
        >
          <input
            type="email"
            required
            placeholder="Email"
            value={email}
            onChange={(event) =>
              setEmail(event.target.value)
            }
            className="w-full border border-slate-300 rounded-xl px-4 py-3"
          />

          <input
            type="password"
            required
            placeholder="Password"
            value={password}
            onChange={(event) =>
              setPassword(event.target.value)
            }
            className="w-full border border-slate-300 rounded-xl px-4 py-3"
          />

          <input
            type="password"
            required
            placeholder="Confirm password"
            value={confirmPassword}
            onChange={(event) =>
              setConfirmPassword(
                event.target.value
              )
            }
            className="w-full border border-slate-300 rounded-xl px-4 py-3"
          />

          {error && (
            <div className="bg-red-100 text-red-700 rounded-xl p-3 text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-amber-500 hover:bg-amber-600 disabled:bg-slate-400 font-semibold py-3 rounded-xl"
          >
            {loading
              ? "Creating..."
              : "Create Account"}
          </button>

          <p className="text-center text-sm text-slate-500">
            Already have an account?{" "}
            <Link
              to="/login"
              className="text-amber-600 font-semibold"
            >
              Sign in
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}

export default Register;