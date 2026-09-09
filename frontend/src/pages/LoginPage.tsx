import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

const DEMO_ACCOUNTS = [
  { role: "Manager", email: "manager@resortiq.demo", desc: "Full operational + AI command center access" },
  { role: "Staff", email: "staff@resortiq.demo", desc: "Task queue for maintenance & housekeeping" },
  { role: "Guest", email: "guest@resortiq.demo", desc: "Services, requests & personalized picks" },
];

export default function LoginPage() {
  const [email, setEmail] = useState("manager@resortiq.demo");
  const [password, setPassword] = useState("demo1234");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const user = await login(email, password);
      navigate(`/${user.role}`);
    } catch (err: any) {
      setError(err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-4xl grid md:grid-cols-2 gap-0 rounded-2xl overflow-hidden glass-card shadow-glow">
        <div className="p-10 hidden md:flex flex-col justify-between bg-gradient-to-br from-charcoal-800 to-charcoal-900 border-r border-white/5">
          <div>
            <p className="text-amber-400 text-sm tracking-wide">Azure Valley Resort</p>
            <h1 className="font-display text-4xl mt-3 leading-tight">ResortIQ</h1>
            <p className="text-slate-400 mt-4 text-sm leading-relaxed">
              An AI decision and action layer for resort operations — prediction, explanation,
              recommendation, and outcome, in one closed loop.
            </p>
          </div>
          <div className="space-y-3 mt-10">
            {DEMO_ACCOUNTS.map((a) => (
              <button
                key={a.email}
                type="button"
                onClick={() => {
                  setEmail(a.email);
                  setPassword("demo1234");
                }}
                className="w-full text-left px-4 py-3 rounded-lg border border-white/10 hover:border-amber-500/50 hover:bg-white/5 transition"
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">{a.role}</span>
                  <span className="text-xs text-slate-500">{a.email}</span>
                </div>
                <p className="text-xs text-slate-500 mt-1">{a.desc}</p>
              </button>
            ))}
          </div>
        </div>

        <div className="p-10 flex flex-col justify-center">
          <h2 className="font-display text-2xl mb-1">Sign in</h2>
          <p className="text-slate-500 text-sm mb-6">Use a demo account or your credentials.</p>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs text-slate-400">Email</label>
              <input
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 w-full bg-charcoal-800 border border-white/10 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-amber-500/60"
                type="email"
                required
              />
            </div>
            <div>
              <label className="text-xs text-slate-400">Password</label>
              <input
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 w-full bg-charcoal-800 border border-white/10 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-amber-500/60"
                type="password"
                required
              />
            </div>
            {error && <p className="text-sm text-red-400">{error}</p>}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-amber-500 hover:bg-amber-400 text-charcoal-950 font-medium rounded-lg py-2.5 text-sm transition disabled:opacity-60"
            >
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>
          <p className="text-xs text-slate-600 mt-6">Demo password for all accounts: demo1234</p>
        </div>
      </div>
    </div>
  );
}
