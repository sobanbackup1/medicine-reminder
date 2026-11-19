import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, CssBaseline } from '@mui/material';
import theme from '@/theme';
import PatientPage from '@/pages/PatientPage';
import AdminLogin from '@/pages/AdminLogin';
import AdminLayout from '@/pages/admin/AdminLayout';
import DashboardPage from '@/pages/admin/DashboardPage';
import TodayStatusPage from '@/pages/admin/TodayStatusPage';
import CalendarPage from '@/pages/admin/CalendarPage';
import StatisticsPage from '@/pages/admin/StatisticsPage';
import LogsPage from '@/pages/admin/LogsPage';
import SettingsPage from '@/pages/admin/SettingsPage';
import BackupPage from '@/pages/admin/BackupPage';
import ExportPage from '@/pages/admin/ExportPage';

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<PatientPage />} />
          <Route path="/admin" element={<AdminLogin />} />
          <Route path="/admin/dashboard" element={<AdminLayout />}>
            <Route index element={<DashboardPage />} />
            <Route path="today" element={<TodayStatusPage />} />
            <Route path="calendar" element={<CalendarPage />} />
            <Route path="statistics" element={<StatisticsPage />} />
            <Route path="logs" element={<LogsPage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="backup" element={<BackupPage />} />
            <Route path="export" element={<ExportPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
