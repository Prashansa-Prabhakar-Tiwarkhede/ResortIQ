import { useEffect, useState } from "react";
import AppShell from "../layouts/AppShell";
import SeverityBadge from "../components/SeverityBadge";
import { api } from "../services/api";
import { useRealtime } from "../hooks/useRealtime";

export default function AICommandCenter() {
  const [recs, setRecs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState<number | null>(null);
  const [toast, setToast] = useState("");

  async function load() {
    try {
      const data = await api.recommendations();
      setRecs(data);
    } catch (e: any) {
      setError(e.message || "Failed to load recommendations");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  useRealtime((msg) => {
    if (msg.type === "recommendation_update") {
      load();
    }
  });

  async function approve(id: number) {
    setBusyId(id);
    try {
      const res = await api.approveRecommendation(id);
      setToast(`Task #${res.task_id} created and assigned to ${res.assigned_to || "an available staff member"}.`);
      await load();
    } catch (e: any) {
      setToast(e.message || "Failed to approve");
    } finally {
      setBusyId(null);
      setTimeout(() => setToast(""), 4000);
    }
  }

  async function reject(id: number) {
    setBusyId(id);
    try {
      await api.rejectRecommendation(id);
      await load();
    } catch (e: any) {
      setToast(e.message || "Failed to reject");
    } finally {
      setBusyId(null);
    }
  }

  const pending = recs.filter((r) => r.status === "pending");
  const decided = recs.filter((r) => r.status !== "pending");

  return (
    <AppShell>
      <div className="mb-6">
        <h1 className="font-display text-2xl">AI Command Center</h1>
        <p className="text-sm text-slate-500 mt-1">
          Every prediction, its explanation, and the recommended action — in one place.
        </p>
      </div>

      {toast && (
        <div className="fixed top-6 right-6 z-50 bg-charcoal-800 border border-amber-500/30 rounded-lg px-4 py-3 text-sm shadow-lg">
          {toast}
        </div>
      )}

      {loading && <p className="text-sm text-slate-500">Loading recommendations…</p>}
      {error && <p className="text-sm text-red-400">{error}</p>}

      {!loading && !error && (
        <>
          <div className="space-y-4 mb-10">
            {pending.length === 0 && (
              <div className="glass-card rounded-xl p-6 text-sm text-slate-500">
                No pending recommendations — the resort is running smoothly.
              </div>
            )}
            {pending.map((r) => (
              <div key={r.id} className="glass-card rounded-xl p-6">
                <div className="flex items-start justify-between gap-4 flex-wrap">
                  <div className="flex-1 min-w-[280px]">
                    <div className="flex items-center gap-2 mb-2">
                      <SeverityBadge severity={r.severity} />
                      {r.module && (
                        <span className="text-[11px] text-slate-500 uppercase tracking-wide">{r.module} module</span>
                      )}
                    </div>
                    <h3 className="font-medium text-slate-100">{r.title}</h3>
                    <div className="grid sm:grid-cols-2 gap-x-6 gap-y-1.5 mt-3 text-sm">
                      {r.risk_score != null && (
                        <p>
                          <span className="text-slate-500">Risk / Prediction: </span>
                          <span className="text-amber-400">{r.risk_score}%</span>
                          {r.confidence != null && (
                            <span className="text-slate-600"> · confidence {r.confidence}%</span>
                          )}
                        </p>
                      )}
                      <p className="sm:col-span-2">
                        <span className="text-slate-500">Why: </span>
                        <span className="text-slate-300">{r.explanation}</span>
                      </p>
                      <p className="sm:col-span-2">
                        <span className="text-slate-500">Recommended action: </span>
                        <span className="text-slate-300">{r.description}</span>
                      </p>
                      <p className="sm:col-span-2">
                        <span className="text-slate-500">Expected impact: </span>
                        <span className="text-slate-300">{r.expected_impact}</span>
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => approve(r.id)}
                      disabled={busyId === r.id}
                      className="text-xs px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-charcoal-950 font-medium transition disabled:opacity-60"
                    >
                      {busyId === r.id ? "Working…" : "Approve & Assign"}
                    </button>
                    <button
                      onClick={() => reject(r.id)}
                      disabled={busyId === r.id}
                      className="text-xs px-4 py-2 rounded-lg border border-white/10 text-slate-400 hover:text-slate-200 hover:border-white/20 transition disabled:opacity-60"
                    >
                      Reject
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {decided.length > 0 && (
            <div>
              <h2 className="text-sm text-slate-500 mb-3">Decided</h2>
              <div className="glass-card rounded-xl divide-y divide-white/5">
                {decided.map((r) => (
                  <div key={r.id} className="flex items-center justify-between px-5 py-3 text-sm">
                    <div className="flex items-center gap-3">
                      <SeverityBadge severity={r.severity} />
                      <span className="text-slate-300">{r.title}</span>
                    </div>
                    <span
                      className={`text-xs uppercase tracking-wide ${
                        r.status === "approved" ? "text-emerald-400" : "text-slate-500"
                      }`}
                    >
                      {r.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </AppShell>
  );
}
