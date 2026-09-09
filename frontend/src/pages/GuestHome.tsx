import { useEffect, useState } from "react";
import AppShell from "../layouts/AppShell";
import { api } from "../services/api";

const STATUS_STYLE: Record<string, string> = {
  pending: "text-slate-400",
  assigned: "text-amber-400",
  in_progress: "text-amber-400",
  completed: "text-emerald-400",
};

export default function GuestHome() {
  const [services, setServices] = useState<any[]>([]);
  const [recs, setRecs] = useState<any[]>([]);
  const [requests, setRequests] = useState<any[]>([]);
  const [requestText, setRequestText] = useState("");
  const [reviewText, setReviewText] = useState("");
  const [reviewResult, setReviewResult] = useState<any>(null);
  const [submitting, setSubmitting] = useState(false);

  async function load() {
    const [s, r, req] = await Promise.all([
      api.guestServices(),
      api.guestRecommendations(),
      api.guestRequests(),
    ]);
    setServices(s);
    setRecs(r);
    setRequests(req);
  }

  useEffect(() => {
    load();
  }, []);

  async function submitRequest(e: React.FormEvent) {
    e.preventDefault();
    if (!requestText.trim()) return;
    setSubmitting(true);
    try {
      await api.createGuestRequest(requestText);
      setRequestText("");
      await load();
    } finally {
      setSubmitting(false);
    }
  }

  async function submitReview(e: React.FormEvent) {
    e.preventDefault();
    if (!reviewText.trim()) return;
    const res = await api.submitReview(reviewText);
    setReviewResult(res);
    setReviewText("");
  }

  return (
    <AppShell>
      <div className="mb-8">
        <h1 className="font-display text-2xl">Welcome to Azure Valley Resort</h1>
        <p className="text-sm text-slate-500 mt-1">Browse services, submit requests, and share feedback.</p>
      </div>

      {recs.length > 0 && (
        <section className="mb-8">
          <h2 className="text-sm text-slate-500 mb-3">Recommended for you</h2>
          <div className="grid sm:grid-cols-2 gap-4">
            {recs.map((r, i) => (
              <div key={i} className="glass-card rounded-xl p-5">
                <p className="font-medium text-slate-100">{r.title}</p>
                <p className="text-xs text-slate-500 mt-1">{r.reason}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="mb-8">
        <h2 className="text-sm text-slate-500 mb-3">Resort Services</h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {services.map((s) => (
            <div key={s.id} className="glass-card rounded-xl p-5">
              <p className="font-medium text-slate-100">{s.name}</p>
              <p className="text-xs text-slate-500 mt-1">{s.description}</p>
            </div>
          ))}
        </div>
      </section>

      <div className="grid lg:grid-cols-2 gap-6">
        <section className="glass-card rounded-xl p-6">
          <h2 className="font-display text-lg mb-3">Submit a Request</h2>
          <form onSubmit={submitRequest} className="space-y-3">
            <textarea
              value={requestText}
              onChange={(e) => setRequestText(e.target.value)}
              placeholder="e.g. Please send extra towels to my room."
              className="w-full bg-charcoal-800 border border-white/10 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-amber-500/60"
              rows={3}
            />
            <button
              type="submit"
              disabled={submitting}
              className="text-xs px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-charcoal-950 font-medium transition disabled:opacity-60"
            >
              {submitting ? "Sending…" : "Submit Request"}
            </button>
          </form>

          {requests.length > 0 && (
            <div className="mt-5 space-y-2">
              {requests.map((r) => (
                <div key={r.id} className="flex items-center justify-between text-sm border-t border-white/5 pt-2">
                  <span className="text-slate-300">{r.text}</span>
                  <span className={`text-xs capitalize ${STATUS_STYLE[r.status] || "text-slate-400"}`}>
                    {r.status.replace("_", " ")}
                  </span>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="glass-card rounded-xl p-6">
          <h2 className="font-display text-lg mb-3">Give Feedback</h2>
          <form onSubmit={submitReview} className="space-y-3">
            <textarea
              value={reviewText}
              onChange={(e) => setReviewText(e.target.value)}
              placeholder="Tell us about your stay…"
              className="w-full bg-charcoal-800 border border-white/10 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-amber-500/60"
              rows={3}
            />
            <button
              type="submit"
              className="text-xs px-4 py-2 rounded-lg border border-white/10 text-slate-300 hover:border-amber-500/50 transition"
            >
              Submit Feedback
            </button>
          </form>
          {reviewResult && (
            <p className="text-xs text-slate-500 mt-3">
              Thanks! Detected sentiment: <span className="text-amber-400 capitalize">{reviewResult.sentiment_label}</span>{" "}
              ({reviewResult.sentiment_score})
            </p>
          )}
        </section>
      </div>
    </AppShell>
  );
}
