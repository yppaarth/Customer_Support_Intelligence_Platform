import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "../components/Layout";
import { getToken } from "../lib/api";
import { AnalyticsPage } from "../pages/AnalyticsPage";
import { EscalationsPage } from "../pages/EscalationsPage";
import { EvaluationsPage } from "../pages/EvaluationsPage";
import { KnowledgePage } from "../pages/KnowledgePage";
import { LoginPage } from "../pages/LoginPage";
import { NotFoundPage } from "../pages/NotFoundPage";
import { TicketDetailPage } from "../pages/TicketDetailPage";
import { TicketsPage } from "../pages/TicketsPage";
import { UsersPage } from "../pages/UsersPage";

function Protected() {
  return getToken() ? <Layout /> : <Navigate to="/login" replace />;
}

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<Protected />}>
        <Route path="/" element={<Navigate to="/tickets" replace />} />
        <Route path="/tickets" element={<TicketsPage />} />
        <Route path="/tickets/:ticketId" element={<TicketDetailPage />} />
        <Route path="/knowledge" element={<KnowledgePage />} />
        <Route path="/escalations" element={<EscalationsPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="/evaluations" element={<EvaluationsPage />} />
        <Route path="/users" element={<UsersPage />} />
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
