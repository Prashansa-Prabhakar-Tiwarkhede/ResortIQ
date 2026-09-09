import { useEffect, useState } from "react";
import AppShell from "../layouts/AppShell";
import { api } from "../services/api";

const STATUS_COLOR: Record<string, string> = {
  CRITICAL: "text-red-400",
  HIGH: "text-orange-400",
  MEDIUM: "text-amber-400",
  LOW: "text-emerald-400",
};

export default function InventoryPage() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [toast, setToast] = useState("");

  async function load() {
    const data = await api.inventoryForecast();
    setItems(data);
    setLoading(false);
  }

  useEffect(() => {
    load();
  }, []);

  async function approve(recId: number) {
    setBusyId(recId);
    try {
      const res = await api.approveRecommendation(recId);
      setToast(`Reorder approved — stock increased by ${res.restocked_by}.`);
      await load();
    } catch (e: any) {
      setToast(e.message);
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
        <h1 className="font-display text-2xl">Inventory Intelligence</h1>
        <p className="text-sm text-slate-500 mt-1">Predicted usage, days remaining, and reorder recommendations.</p>
      </div>

      {toast && (
        <div className="fixed top-6 right-6 z-50 bg-charcoal-800 border border-amber-500/30 rounded-lg px-4 py-3 text-sm shadow-lg">
          {toast}
        </div>
      )}

      {loading ? (
        <p className="text-sm text-slate-500">Loading…</p>
      ) : (
        <div className="glass-card rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500 border-b border-white/5">
                <th className="px-5 py-3 font-normal">Item</th>
                <th className="px-5 py-3 font-normal">Current Stock</th>
                <th className="px-5 py-3 font-normal">Predicted Usage</th>
                <th className="px-5 py-3 font-normal">Days Remaining</th>
                <th className="px-5 py-3 font-normal">Status</th>
                <th className="px-5 py-3 font-normal">Action</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id} className="border-b border-white/5 last:border-0">
                  <td className="px-5 py-3.5">
                    <p className="text-slate-100">{item.name}</p>
                    {item.recommendation && (
                      <p className="text-xs text-slate-500 mt-0.5">{item.recommendation.description}</p>
                    )}
                  </td>
                  <td className="px-5 py-3.5 text-slate-300">{item.current_stock}{item.unit}</td>
                  <td className="px-5 py-3.5 text-slate-300">{item.predicted_daily_usage}{item.unit}/day</td>
                  <td className="px-5 py-3.5 text-slate-300">{item.days_remaining}</td>
                  <td className={`px-5 py-3.5 font-medium ${STATUS_COLOR[item.status] || "text-slate-400"}`}>
                    {item.status}
                  </td>
                  <td className="px-5 py-3.5">
                    {item.recommendation && item.recommendation.status === "pending" ? (
                      <div className="flex gap-2">
                        <button
                          onClick={() => approve(item.recommendation.id)}
                          disabled={busyId === item.recommendation.id}
                          className="text-xs px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-charcoal-950 font-medium transition disabled:opacity-60"
                        >
                          Approve Reorder
                        </button>
                        <button
                          onClick={() => reject(item.recommendation.id)}
                          disabled={busyId === item.recommendation.id}
                          className="text-xs px-3 py-1.5 rounded-lg border border-white/10 text-slate-400 hover:text-slate-200 transition disabled:opacity-60"
                        >
                          Ignore
                        </button>
                      </div>
                    ) : item.recommendation ? (
                      <span className="text-xs text-emerald-400 capitalize">{item.recommendation.status}</span>
                    ) : (
                      <span className="text-xs text-slate-600">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </AppShell>
  );
}
