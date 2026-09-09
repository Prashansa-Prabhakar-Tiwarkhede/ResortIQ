import { useEffect, useState } from "react";
import AppShell from "../layouts/AppShell";
import { api } from "../services/api";

function fmtInr(n: number) {
  return "₹" + Math.round(n).toLocaleString("en-IN");
}

export default function RevenuePage() {
  const [rows, setRows] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [toast, setToast] = useState("");

  async function load() {
    const data = await api.revenueRecommendations();
    setRows(data);
    setLoading(false);
  }

  useEffect(() => {
    load();
  }, []);

  async function approve(recId: number) {
    setBusyId(recId);
    try {
      const res = await api.approveRecommendation(recId);
      setToast(`Pricing applied to ${res.rooms_updated} ${res.room_type} rooms.`);
      await load();
    } finally {
      setBusyId(null);
      setTimeout(() => setToast(""), 4000);
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
        <h1 className="font-display text-2xl">Revenue Intelligence</h1>
        <p className="text-sm text-slate-500 mt-1">Demand-based pricing recommendations by room type.</p>
      </div>

      {toast && (
        <div className="fixed top-6 right-6 z-50 bg-charcoal-800 border border-amber-500/30 rounded-lg px-4 py-3 text-sm shadow-lg">
          {toast}
        </div>
      )}

      {loading ? (
        <p className="text-sm text-slate-500">Loading…</p>
      ) : (
        <div className="grid sm:grid-cols-2 gap-4">
          {rows.map((r) => (
            <div key={r.room_type} className="glass-card rounded-xl p-6">
              <div className="flex items-center justify-between">
                <p className="font-medium text-slate-100">{r.room_type}</p>
                <span className={`text-xs font-medium ${r.adjustment_pct > 0 ? "text-emerald-400" : "text-red-400"}`}>
                  {r.adjustment_pct > 0 ? "+" : ""}{r.adjustment_pct}%
                </span>
              </div>
              <div className="flex items-baseline gap-2 mt-2">
                <span className="text-sm text-slate-500 line-through">{fmtInr(r.current_price)}</span>
                <span className="font-display text-2xl text-amber-400">{fmtInr(r.recommended_price)}</span>
              </div>
              <div className="grid grid-cols-2 gap-3 mt-4 text-sm">
                <div>
                  <p className="text-xs text-slate-500">Expected occupancy</p>
                  <p className="text-slate-200">{r.expected_occupancy}%</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Revenue impact</p>
                  <p className="text-slate-200">{r.expected_revenue_impact_pct > 0 ? "+" : ""}{r.expected_revenue_impact_pct}%</p>
                </div>
              </div>
              <p className="text-xs text-slate-500 mt-4">{r.explanation}</p>
              {r.recommendation && r.recommendation.status === "pending" && (
                <div className="flex gap-2 mt-4">
                  <button
                    onClick={() => approve(r.recommendation.id)}
                    disabled={busyId === r.recommendation.id}
                    className="text-xs px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-charcoal-950 font-medium transition disabled:opacity-60"
                  >
                    Apply Recommendation
                  </button>
                  <button
                    onClick={() => reject(r.recommendation.id)}
                    disabled={busyId === r.recommendation.id}
                    className="text-xs px-3 py-1.5 rounded-lg border border-white/10 text-slate-400 hover:text-slate-200 transition disabled:opacity-60"
                  >
                    Ignore
                  </button>
                </div>
              )}
              {r.recommendation && r.recommendation.status !== "pending" && (
                <p className="text-xs text-emerald-400 mt-4 capitalize">{r.recommendation.status}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </AppShell>
  );
}
