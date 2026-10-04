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
import { InsightsPage } from "./features/insights/InsightsPage";
import { NotificationsPage } from "./features/notifications/NotificationsPage";
import { PreferencesPage } from "./features/preferences/PreferencesPage";
import { OnboardingPage } from "./features/profile/OnboardingPage";
import { TransactionsPage } from "./features/transactions/TransactionsPage";

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/auth/social-callback" element={<SocialCallbackPage />} />
        <Route element={<ProtectedRoute />}>
          <Route path="/onboarding" element={<OnboardingPage />} />
          <Route element={<AppLayout />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/transactions" element={<TransactionsPage />} />
            <Route path="/budgets" element={<BudgetsPage />} />
            <Route path="/insights" element={<InsightsPage />} />
            <Route path="/goals" element={<GoalsPage />} />
            <Route path="/notifications" element={<NotificationsPage />} />
            <Route path="/settings" element={<PreferencesPage />} />
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}

export default App;
