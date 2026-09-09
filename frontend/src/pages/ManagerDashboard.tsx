import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import AppShell from "../layouts/AppShell";
import KpiCard from "../components/KpiCard";
import SeverityBadge from "../components/SeverityBadge";
import { api } from "../services/api";
import { useRealtime } from "../hooks/useRealtime";

function fmtInr(n: number) {
  return "₹" + Math.round(n).toLocaleString("en-IN");
}

export default function ManagerDashboard() {
  const [summary, setSummary] = useState<any>(null);
  const [attention, setAttention] = useState<any[]>([]);
  const [forecast, setForecast] = useState<any>(null);
  const [impact, setImpact] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    try {
      const [s, a, f, i] = await Promise.all([
        api.dashboardSummary(),
        api.attention(),
        api.occupancyForecast(),
        api.impact(),
      ]);
      setSummary(s);
      setAttention(a);
      setForecast(f);
      setImpact(i);
    } catch (e: any) {
      setError(e.message || "Failed to load dashboard");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  useRealtime((msg) => {
    if (["alert", "task_update", "recommendation_update"].includes(msg.type)) {
      load();
    }
  });

  if (loading) {
    return (
      <AppShell>
        <div className="grid grid-cols-6 gap-4 animate-pulse">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="glass-card rounded-xl h-24" />
          ))}
        </div>
      </AppShell>
    );
  }

  if (error) {
    return (
      <AppShell>
        <div className="glass-card rounded-xl p-6 text-red-400 text-sm">{error}</div>
      </AppShell>
    );
  }

  const chartData = [
    ...forecast.history.slice(-7).map((h: any) => ({ label: h.date.slice(5), value: h.occupancy_pct, kind: "actual" })),
    ...forecast.forecast.map((f: any) => ({ label: f.date.slice(5), value: f.occupancy_pct, kind: "forecast" })),
  ];

  const score = summary.resort_intelligence_score;

  return (
    <AppShell>
      {/* Hero: what needs my attention */}
      <section className="mb-8">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-display text-xl">What Needs My Attention?</h2>
          <Link to="/manager/ai-command-center" className="text-xs text-amber-400 hover:underline">
            Open AI Command Center →
          </Link>
        </div>
        <div className="glass-card rounded-xl divide-y divide-white/5">
          {attention.length === 0 && (
            <p className="p-5 text-sm text-slate-500">All clear — no active alerts right now.</p>
          )}
          {attention.map((a) => (
            <div key={a.id} className="flex items-center justify-between px-5 py-3.5">
              <div className="flex items-center gap-3">
                <SeverityBadge severity={a.severity} />
                <span className="text-sm text-slate-200">{a.message}</span>
              </div>
              <span className="text-[11px] text-slate-600 uppercase tracking-wide">{a.source_module}</span>
            </div>
          ))}
        </div>
      </section>

      {/* KPIs */}
      <section className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
        <KpiCard label="Occupancy" value={`${summary.kpis.occupancy_pct}%`} />
        <KpiCard label="Today's Revenue" value={fmtInr(summary.kpis.todays_revenue)} />
        <KpiCard label="Active Alerts" value={String(summary.kpis.active_alerts)} />
        <KpiCard label="Staff Utilization" value={`${summary.kpis.staff_utilization_pct}%`} />
        <KpiCard label="Guest Satisfaction" value={`${summary.kpis.guest_satisfaction}/5`} />
        <KpiCard label="Inventory Risk" value={`${summary.kpis.inventory_risk_pct}%`} />
      </section>

      <div className="grid lg:grid-cols-3 gap-6 mb-8">
        {/* Resort Intelligence Score */}
        <div className="glass-card rounded-xl p-6 lg:col-span-1">
          <p className="text-xs text-slate-400 mb-1">Resort Intelligence Score</p>
          <p className="font-display text-5xl text-amber-400">{score.overall}<span className="text-lg text-slate-500">/100</span></p>
          <div className="mt-5 space-y-2.5">
            {[
              ["Operations", score.operations],
              ["Guest Experience", score.guest_experience],
              ["Maintenance", score.maintenance],
              ["Inventory", score.inventory],
              ["Revenue", score.revenue],
            ].map(([label, val]) => (
              <div key={label as string}>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-400">{label}</span>
                  <span className="text-slate-300">{val}</span>
                </div>
                <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-amber-600 to-amber-400 rounded-full"
                    style={{ width: `${val}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Occupancy forecast chart */}
        <div className="glass-card rounded-xl p-6 lg:col-span-2">
          <div className="flex items-center justify-between mb-1">
            <p className="text-xs text-slate-400">Next 7 Days Forecast</p>
          </div>
          <p className="font-display text-lg mb-4">Occupancy Forecast</p>
          <div style={{ width: "100%", height: 220 }}>
            <ResponsiveContainer>
              <LineChart data={chartData}>
                <CartesianGrid stroke="#242830" vertical={false} />
                <XAxis dataKey="label" stroke="#5b6472" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="#5b6472" fontSize={11} tickLine={false} axisLine={false} domain={[40, 100]} />
                <Tooltip
                  contentStyle={{ background: "#1A1E24", border: "1px solid #333944", borderRadius: 8, fontSize: 12 }}
                  labelStyle={{ color: "#94a3b8" }}
                />
                <Line type="monotone" dataKey="value" stroke="#E5A430" strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <p className="text-xs text-slate-500 mt-3">
            <span className="text-amber-400">AI Insight — </span>
            {forecast.insight}
          </p>
        </div>
      </div>

      {/* Impact dashboard */}
      <section>
        <h2 className="font-display text-xl mb-3">Impact This Session</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <KpiCard label="Potential Failures Prevented" value={String(impact.prevented_failures)} />
          <KpiCard label="Tasks Auto-Created from AI" value={String(impact.tasks_automated)} />
          <KpiCard label="Tasks Completed" value={String(impact.completed_tasks)} />
        </div>
        <p className="text-xs text-slate-600 mt-3">{impact.note}</p>
      </section>
    </AppShell>
  );
}
