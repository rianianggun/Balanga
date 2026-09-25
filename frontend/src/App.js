import { useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import LoginPage from "./pages/LoginPage";
import AdminDashboard from "./pages/AdminDashboard";
import PerangkatDashboard from "./pages/PerangkatDashboard";
import VerifikatorDashboard from "./pages/VerifikatorDashboard";
import PenilaiDashboard from "./pages/PenilaiDashboard";
import VerifikatorReviewPage from "./pages/VerifikatorReviewPage";
import { Toaster } from "./components/ui/sonner";
import { FilePreviewHost } from "./components/FilePreviewHost";

function Dashboard() {
  const { user } = useAuth();
  if (user.role === "admin") return <AdminDashboard />;
  if (user.role === "perangkat") return <PerangkatDashboard />;
  if (user.role === "verifikator") return <VerifikatorDashboard />;
  if (user.role === "penilai") return <PenilaiDashboard />;
  return <div className="p-10 text-center">Peran tidak dikenal.</div>;
}

function VerifikasiRoute() {
  const { user } = useAuth();
  if (user.role !== "verifikator") return <Navigate to="/" replace />;
  return <VerifikatorReviewPage />;
}

function App() {
  useEffect(() => {
    document.title = "Balanga";
  }, []);
  return (
    <div className="App">
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/verifikasi/:sid"
              element={
                <ProtectedRoute>
                  <VerifikasiRoute />
                </ProtectedRoute>
              }
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
          <Toaster position="top-right" richColors />
          <FilePreviewHost />
        </BrowserRouter>
      </AuthProvider>
    </div>
  );
}

export default App;
