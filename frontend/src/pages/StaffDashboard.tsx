import { useEffect, useState } from "react";
import AppShell from "../layouts/AppShell";
import { api } from "../services/api";
import { useAuth } from "../hooks/useAuth";
import { useRealtime } from "../hooks/useRealtime";

const PRIORITY_LABEL: Record<string, string> = {
  critical: "CRITICAL",
  high: "HIGH PRIORITY",
  normal: "NORMAL",
  low: "LOW",
};

const PRIORITY_STYLE: Record<string, string> = {
  critical: "border-red-500/40 bg-red-500/5",
  high: "border-orange-500/40 bg-orange-500/5",
  normal: "border-white/10",
  low: "border-white/10",
};

function TaskCard({ task, onChanged }: { task: any; onChanged: () => void }) {
  const [notes, setNotes] = useState(task.notes || "");
  const [busy, setBusy] = useState(false);

  async function start() {
    setBusy(true);
    try {
      await api.updateTask(task.id, { status: "in_progress" });
      onChanged();
    } finally {
      setBusy(false);
    }
  }

  async function complete() {
    setBusy(true);
    try {
      await api.updateTask(task.id, { status: "completed", notes });
      onChanged();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className={`rounded-xl p-5 border glass-card ${PRIORITY_STYLE[task.priority] || PRIORITY_STYLE.normal}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-[11px] font-semibold tracking-wide text-amber-400">
          {PRIORITY_LABEL[task.priority] || task.priority.toUpperCase()}
        </span>
        <span className="text-[11px] text-slate-500 capitalize">{task.status.replace("_", " ")}</span>
      </div>
      <h3 className="font-medium text-slate-100">{task.title}</h3>
      {task.location && <p className="text-sm text-slate-400 mt-1">{task.location}</p>}
      {task.ai_source && (
        <p className="text-xs text-slate-500 mt-2">
          <span className="text-slate-600">Reason: </span>
          {task.ai_source}
        </p>
      )}
      <p className="text-sm text-slate-400 mt-2">{task.description}</p>

      {task.status !== "completed" && (
        <div className="mt-4 flex flex-col gap-2">
          {task.status !== "in_progress" ? (
            <button
              onClick={start}
              disabled={busy}
              className="text-xs px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-charcoal-950 font-medium transition disabled:opacity-60"
            >
              {busy ? "Working…" : "Start Task"}
            </button>
          ) : (
            <>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Completion notes (e.g. what was inspected/fixed)…"
                className="w-full bg-charcoal-800 border border-white/10 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-amber-500/60"
                rows={2}
              />
              <button
                onClick={complete}
                disabled={busy}
                className="text-xs px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-charcoal-950 font-medium transition disabled:opacity-60"
              >
                {busy ? "Working…" : "Complete Task"}
              </button>
            </>
          )}
        </div>
      )}
      {task.status === "completed" && task.notes && (
        <p className="text-xs text-emerald-400 mt-3">✓ {task.notes}</p>
      )}
    </div>
  );
}

export default function StaffDashboard() {
  const { user } = useAuth();
  const [tasks, setTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  async function load() {
    const data = await api.tasks();
    setTasks(data);
    setLoading(false);
  }

  useEffect(() => {
    load();
  }, []);

  useRealtime((msg) => {
    if (msg.type === "task_update") {
      load();
    }
  });

  const active = tasks.filter((t) => t.status !== "completed" && t.status !== "cancelled");
  const completed = tasks.filter((t) => t.status === "completed");

  return (
    <AppShell>
      <div className="mb-6">
        <h1 className="font-display text-2xl">Good morning, {user?.name?.split(" ")[0]}</h1>
        <p className="text-sm text-slate-500 mt-1">
          You have <span className="text-amber-400">{active.length}</span> active task{active.length !== 1 ? "s" : ""}.
        </p>
      </div>

      {loading && <p className="text-sm text-slate-500">Loading tasks…</p>}

      {!loading && (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {active.length === 0 && (
            <div className="glass-card rounded-xl p-6 text-sm text-slate-500 col-span-full">
              No active tasks right now. Nice work.
            </div>
          )}
          {active.map((t) => (
            <TaskCard key={t.id} task={t} onChanged={load} />
          ))}
        </div>
      )}

      {completed.length > 0 && (
        <div className="mt-10">
          <h2 className="text-sm text-slate-500 mb-3">Completed</h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 opacity-70">
            {completed.map((t) => (
              <TaskCard key={t.id} task={t} onChanged={load} />
            ))}
          </div>
        </div>
      )}
    </AppShell>
  );
}
