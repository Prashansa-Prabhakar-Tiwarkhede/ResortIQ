import { useEffect, useState } from "react";
import AppShell from "../layouts/AppShell";
import { api } from "../services/api";

export default function StaffPage() {
  const [depts, setDepts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [toast, setToast] = useState("");

  async function load() {
    const data = await api.staffingRecommendations();
    setDepts(data);
    setLoading(false);
  }

  useEffect(() => {
    load();
  }, []);

  async function approve(recId: number) {
    setBusyId(recId);
    try {
      await api.approveRecommendation(recId);
      setToast("Staffing change logged.");
      await load();
    } finally {
      setBusyId(null);
      setTimeout(() => setToast(""), 3000);
    }
  }

  async function reject(recId: number) {
    setBusyId(recId);
    try {
      await api.rejectRecommendation(recId);
      await load();
    } finally {
      setBusyId(null);
    }
  }

  return (
    <AppShell>
      <div className="mb-6">
        <h1 className="font-display text-2xl">Staff Optimization</h1>
        <p className="text-sm text-slate-500 mt-1">Required headcount vs. current roster, by department.</p>
      </div>

      {toast && (
        <div className="fixed top-6 right-6 z-50 bg-charcoal-800 border border-amber-500/30 rounded-lg px-4 py-3 text-sm shadow-lg">
          {toast}
        </div>
      )}

      {loading ? (
        <p className="text-sm text-slate-500">Loading…</p>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {depts.map((d) => (
            <div key={d.department} className="glass-card rounded-xl p-5">
              <p className="font-medium text-slate-100">{d.department}</p>
              <div className="flex items-baseline gap-2 mt-2">
                <span className="font-display text-3xl">{d.current_staff}</span>
                <span className="text-sm text-slate-500">/ {d.required_staff} required</span>
              </div>
              <div className="h-1.5 rounded-full bg-white/5 overflow-hidden mt-3">
                <div
                  className={`h-full rounded-full ${d.gap > 0 ? "bg-orange-400" : "bg-emerald-400"}`}
                  style={{ width: `${Math.min(100, (d.current_staff / Math.max(d.required_staff, 1)) * 100)}%` }}
                />
              </div>
              <p className="text-xs text-slate-500 mt-3">{d.explanation}</p>
              {d.recommendation && d.recommendation.status === "pending" && (
                <div className="flex gap-2 mt-4">
                  <button
                    onClick={() => approve(d.recommendation.id)}
                    disabled={busyId === d.recommendation.id}
                    className="text-xs px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-charcoal-950 font-medium transition disabled:opacity-60"
                  >
                    Approve
                  </button>
                  <button
                    onClick={() => reject(d.recommendation.id)}
                    disabled={busyId === d.recommendation.id}
                    className="text-xs px-3 py-1.5 rounded-lg border border-white/10 text-slate-400 hover:text-slate-200 transition disabled:opacity-60"
                  >
                    Ignore
                  </button>
                </div>
              )}
              {d.recommendation && d.recommendation.status !== "pending" && (
                <p className="text-xs text-emerald-400 mt-4 capitalize">{d.recommendation.status}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </AppShell>
  );
}
