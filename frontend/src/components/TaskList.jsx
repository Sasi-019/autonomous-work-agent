function TaskList({ tasks }) {
  return (
    <section>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-slate-900">
          Recent Tasks
        </h2>

        <span className="text-sm text-slate-500">
          {tasks.length} task
          {tasks.length !== 1 ? "s" : ""}
        </span>
      </div>

      {tasks.length === 0 ? (
        <div className="bg-white border border-dashed border-slate-300 rounded-2xl p-8 text-center">
          <p className="text-slate-500">
            No tasks yet.
          </p>

          <p className="text-sm text-slate-400 mt-1">
            Create your first autonomous task above.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {tasks.map((task) => (
            <div
              key={task.id}
              className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm"
            >
              <div className="flex justify-between items-start gap-4">
                <div className="min-w-0">
                  <p className="text-xs text-slate-400">
                    TASK #{task.id}
                  </p>

                  <h3 className="font-semibold text-slate-900 mt-1">
                    {task.goal}
                  </h3>

                  <p className="text-xs text-slate-500 mt-2">
                    Workspace: {task.workspace}
                  </p>

                  {task.resource && (
                    <p className="text-xs text-slate-500 mt-1 break-all">
                      Resource: {task.resource}
                    </p>
                  )}
                </div>

                <span
                  className={`shrink-0 text-xs font-semibold px-3 py-1 rounded-full ${
                    task.status === "completed"
                      ? "bg-green-100 text-green-700"
                      : task.status ===
                        "waiting_approval"
                      ? "bg-amber-100 text-amber-700"
                      : task.status === "failed"
                      ? "bg-red-100 text-red-700"
                      : "bg-slate-100 text-slate-700"
                  }`}
                >
                  {task.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

export default TaskList;