import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import "./index.css";
import { AuthProvider, useAuth } from "./hooks/useAuth";
import LoginPage from "./pages/LoginPage";
import ManagerDashboard from "./pages/ManagerDashboard";
import AICommandCenter from "./pages/AICommandCenter";
import MaintenancePage from "./pages/MaintenancePage";
import InventoryPage from "./pages/InventoryPage";
import StaffPage from "./pages/StaffPage";
import RevenuePage from "./pages/RevenuePage";
import GuestsAnalyticsPage from "./pages/GuestsAnalyticsPage";
import StaffDashboard from "./pages/StaffDashboard";
import GuestHome from "./pages/GuestHome";

function ProtectedRoute({ role, children }: { role: string; children: React.ReactNode }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== role) return <Navigate to={`/${user.role}`} replace />;
  return <>{children}</>;
}

function RootRedirect() {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return <Navigate to={`/${user.role}`} replace />;
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<RootRedirect />} />
          <Route
            path="/manager"
            element={
              <ProtectedRoute role="manager">
                <ManagerDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/manager/ai-command-center"
            element={
              <ProtectedRoute role="manager">
                <AICommandCenter />
              </ProtectedRoute>
            }
          />
          <Route
            path="/manager/maintenance"
            element={
              <ProtectedRoute role="manager">
                <MaintenancePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/manager/inventory"
            element={
              <ProtectedRoute role="manager">
                <InventoryPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/manager/staff"
            element={
              <ProtectedRoute role="manager">
                <StaffPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/manager/revenue"
            element={
              <ProtectedRoute role="manager">
                <RevenuePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/manager/guests"
            element={
              <ProtectedRoute role="manager">
                <GuestsAnalyticsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/staff"
            element={
              <ProtectedRoute role="staff">
                <StaffDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/guest"
            element={
              <ProtectedRoute role="guest">
                <GuestHome />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
