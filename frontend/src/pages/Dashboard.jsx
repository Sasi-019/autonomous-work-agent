import { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";
import GoalInput from "../components/GoalInput";
import TaskList from "../components/TaskList";

function Dashboard() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);

  async function fetchTasks() {
    const token = localStorage.getItem(
      "access_token"
    );

    if (!token) {
      window.location.href = "/login";
      return;
    }

    try {
      const response = await fetch(
        "https://autonomous-work-agent.onrender.com/tasks",
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.status === 401) {
        localStorage.removeItem(
          "access_token"
        );

        window.location.href = "/login";
        return;
      }

      const data = await response.json();

      setTasks(
        Array.isArray(data) ? data : []
      );
    } catch (error) {
      console.error(
        "Task loading error:",
        error
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchTasks();
  }, []);

  function handleTaskCreated(newTask) {
    setTasks((currentTasks) => [
      newTask,
      ...currentTasks,
    ]);
  }

  return (
    <div className="min-h-screen bg-slate-100 flex">
      <Sidebar />

      <main className="flex-1 p-8">
        <header className="mb-8">
          <p className="text-sm text-amber-600 font-semibold">
            WORKSPACE
          </p>

          <h1 className="text-3xl font-bold text-slate-900 mt-1">
            Dashboard
          </h1>

          <p className="text-slate-500 mt-2">
            Give your AI agent a goal and let it
            handle the work.
          </p>
        </header>

        <GoalInput
          onTaskCreated={handleTaskCreated}
        />

        <div className="mt-8">
          {loading ? (
            <div className="bg-white rounded-2xl p-6">
              Loading tasks...
            </div>
          ) : (
            <TaskList tasks={tasks} />
          )}
        </div>
      </main>
    </div>
  );
}

export default Dashboard;