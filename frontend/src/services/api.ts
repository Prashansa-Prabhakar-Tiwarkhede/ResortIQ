const API_BASE = ((import.meta as any).env?.VITE_API_BASE || "http://localhost:8000").replace(/\/+$/, "");

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem("resortiq_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request(path: string, options: RequestInit = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...(options.headers || {}),
    },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  login: (email: string, password: string) =>
    request("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  dashboardSummary: () => request("/dashboard/summary"),
  attention: () => request("/dashboard/attention"),
  occupancyForecast: () => request("/dashboard/occupancy/forecast"),
  impact: () => request("/dashboard/impact"),
  maintenanceRisks: () => request("/maintenance/risks"),
  recommendations: () => request("/recommendations"),
  approveRecommendation: (id: number) => request(`/recommendations/${id}/approve`, { method: "POST" }),
  rejectRecommendation: (id: number) => request(`/recommendations/${id}/reject`, { method: "POST" }),
  tasks: (staffId?: number) => request(`/tasks${staffId ? `?staff_id=${staffId}` : ""}`),
  updateTask: (id: number, payload: { status?: string; notes?: string }) =>
    request(`/tasks/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  alerts: () => request("/alerts"),
  guestServices: () => request("/guest/services"),
  guestRecommendations: () => request("/guest/recommendations"),
  guestRequests: () => request("/guest/requests"),
  createGuestRequest: (text: string, category = "general") =>
    request("/guest/requests", { method: "POST", body: JSON.stringify({ text, category }) }),
  submitReview: (text: string) => request("/guest/reviews", { method: "POST", body: JSON.stringify({ text }) }),
  inventoryForecast: () => request("/inventory/forecast"),
  staffingRecommendations: () => request("/staff/recommendations"),
  revenueRecommendations: () => request("/revenue/recommendations"),
  sentimentAnalytics: () => request("/guest/sentiment"),
};
