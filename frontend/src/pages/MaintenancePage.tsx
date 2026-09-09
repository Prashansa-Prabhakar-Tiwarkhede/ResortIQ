import { useEffect, useState } from "react";
import AppShell from "../layouts/AppShell";
import SeverityBadge from "../components/SeverityBadge";
import { api } from "../services/api";

const STATUS_COLOR: Record<string, string> = {
  CRITICAL: "text-red-400",
  HIGH: "text-orange-400",
  MEDIUM: "text-amber-400",
  LOW: "text-emerald-400",
};

export default function MaintenancePage() {
  const [risks, setRisks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<number | null>(null);

  useEffect(() => {
    api.maintenanceRisks().then((data) => {
      setRisks(data);
      setLoading(false);
    });
  }, []);

  return (
    <AppShell>
      <div className="mb-6">
        <h1 className="font-display text-2xl">Predictive Maintenance</h1>
        <p className="text-sm text-slate-500 mt-1">Failure risk across all monitored equipment, ranked highest first.</p>
      </div>

      {loading ? (
        <p className="text-sm text-slate-500">Loading…</p>
      ) : (
        <div className="glass-card rounded-xl divide-y divide-white/5">
          {risks.map((r) => (
            <div key={r.prediction_id}>
              <button
                onClick={() => setExpanded(expanded === r.prediction_id ? null : r.prediction_id)}
                className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-white/[0.02] transition"
              >
                <div className="flex items-center gap-4">
                  <span className={`font-display text-lg w-14 ${STATUS_COLOR[r.status]}`}>{r.risk_score}%</span>
                  <div>
                    <p className="text-slate-100 text-sm">{r.equipment_name}</p>
                    <p className="text-xs text-slate-500">{r.location}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {r.recommendation && <SeverityBadge severity={r.recommendation.severity} />}
                  <span className={`text-xs font-medium ${STATUS_COLOR[r.status]}`}>{r.status}</span>
                </div>
              </button>
              {expanded === r.prediction_id && (
                <div className="px-5 pb-4 text-sm">
                  <p className="text-slate-400">
                    <span className="text-slate-600">Confidence: </span>
                    {r.confidence}%
                  </p>
                  <p className="text-slate-300 mt-1">{r.explanation}</p>
                  {r.recommendation && (
                    <p className="text-slate-500 mt-2 text-xs">
                      Recommendation: {r.recommendation.description} — go to the AI Command Center to approve.
                    </p>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </AppShell>
  );
}
