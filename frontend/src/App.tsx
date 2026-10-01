import { Navigate, Route, Routes } from "react-router";

import { AppLayout } from "./components/AppLayout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { AuthProvider } from "./features/auth/AuthContext";
import { LoginPage } from "./features/auth/LoginPage";
import { RegisterPage } from "./features/auth/RegisterPage";
import { SocialCallbackPage } from "./features/auth/SocialCallbackPage";
import { BudgetsPage } from "./features/budgets/BudgetsPage";
import { DashboardPage } from "./features/dashboard/DashboardPage";
import { GoalsPage } from "./features/goals/GoalsPage";
import { ImportsPage } from "./features/imports/ImportsPage";
import { InsightsPage } from "./features/insights/InsightsPage";
import { PreferencesPage } from "./features/preferences/PreferencesPage";
import { TransactionsPage } from "./features/transactions/TransactionsPage";
import { TrashPage } from "./features/transactions/TrashPage";

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/auth/social-callback" element={<SocialCallbackPage />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/transactions" element={<TransactionsPage />} />
            <Route path="/trash" element={<TrashPage />} />
            <Route path="/imports" element={<ImportsPage />} />
            <Route path="/budgets" element={<BudgetsPage />} />
            <Route path="/insights" element={<InsightsPage />} />
            <Route path="/goals" element={<GoalsPage />} />
            <Route path="/settings" element={<PreferencesPage />} />
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}

export default App;
