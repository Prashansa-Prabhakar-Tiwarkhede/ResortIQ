import { useEffect, useState } from "react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";
import AppShell from "../layouts/AppShell";
import { api } from "../services/api";

const SENTIMENT_COLORS: Record<string, string> = {
  Positive: "#34d399",
  Neutral: "#64748b",
  Negative: "#f87171",
};

const LABEL_STYLE: Record<string, string> = {
  positive: "text-emerald-400",
  neutral: "text-slate-400",
  negative: "text-red-400",
};

export default function GuestsAnalyticsPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.sentimentAnalytics().then((d) => {
      setData(d);
      setLoading(false);
    });
  }, []);

  if (loading || !data) {
    return (
      <AppShell>
        <p className="text-sm text-slate-500">Loading…</p>
      </AppShell>
    );
  }

  const pieData = [
    { name: "Positive", value: data.positive_pct },
    { name: "Neutral", value: data.neutral_pct },
    { name: "Negative", value: data.negative_pct },
  ];

  return (
    <AppShell>
      <div className="mb-6">
        <h1 className="font-display text-2xl">Guest Sentiment Analytics</h1>
        <p className="text-sm text-slate-500 mt-1">
          {data.total_reviews} review{data.total_reviews !== 1 ? "s" : ""} analyzed · average score {data.average_score}
        </p>
      </div>

      <div className="grid lg:grid-cols-3 gap-6 mb-8">
        <div className="glass-card rounded-xl p-6">
          <p className="text-xs text-slate-400 mb-2">Sentiment Breakdown</p>
          <div style={{ width: "100%", height: 220 }}>
            <ResponsiveContainer>
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" innerRadius={50} outerRadius={80} paddingAngle={2}>
                  {pieData.map((entry) => (
                    <Cell key={entry.name} fill={SENTIMENT_COLORS[entry.name]} stroke="none" />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: "#1A1E24", border: "1px solid #333944", borderRadius: 8, fontSize: 12 }}
                  formatter={(v: number) => `${v}%`}
                />
                <Legend wrapperStyle={{ fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="glass-card rounded-xl p-6 lg:col-span-2">
          <p className="text-xs text-slate-400 mb-4">Top Guest Issues</p>
          <div className="space-y-3">
            {data.top_issues.length === 0 && <p className="text-sm text-slate-500">No recurring issues detected.</p>}
            {data.top_issues.map((issue: any, i: number) => (
              <div key={issue.topic}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-slate-300">{i + 1}. {issue.topic}</span>
                  <span className="text-slate-500">{issue.pct}%</span>
                </div>
                <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-amber-600 to-amber-400 rounded-full" style={{ width: `${issue.pct}%` }} />
                </div>
              </div>
            ))}
          </div>
          <p className="text-xs text-amber-400 mt-5">AI Recommendation — {data.recommended_action}</p>
        </div>
      </div>

      <div>
        <h2 className="text-sm text-slate-500 mb-3">Recent Reviews</h2>
        <div className="glass-card rounded-xl divide-y divide-white/5">
          {data.recent_reviews.map((r: any) => (
            <div key={r.id} className="px-5 py-3.5">
              <div className="flex items-center justify-between">
                <span className={`text-xs font-medium capitalize ${LABEL_STYLE[r.sentiment_label]}`}>
                  {r.sentiment_label} ({r.sentiment_score})
                </span>
                <span className="text-[11px] text-slate-600">{r.topics}</span>
              </div>
              <p className="text-sm text-slate-300 mt-1">{r.text}</p>
            </div>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
