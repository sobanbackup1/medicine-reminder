/**
 * API client for the Medication Reminder backend.
 *
 * When the backend is not reachable (e.g. during local frontend-only dev), the
 * client falls back to an in-memory mock so the UI is still usable.
 */

const API_BASE = '/api';

let adminToken: string | null = localStorage.getItem('admin_token');
const linkToken = new URLSearchParams(window.location.hash.slice(1)).get('patient_token');
if (linkToken) {
  localStorage.setItem('patient_token', linkToken);
  window.history.replaceState(null, '', window.location.pathname + window.location.search);
}
let patientToken: string | null = localStorage.getItem('patient_token');

export function setToken(token: string | null) {
  adminToken = token;
  if (token) localStorage.setItem('admin_token', token);
  else localStorage.removeItem('admin_token');
}

export function getToken(): string | null {
  return adminToken;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };
  if (adminToken) headers['Authorization'] = `Bearer ${adminToken}`;
  if (path.startsWith('/patient/') && patientToken) headers['X-Patient-Token'] = patientToken;

  const resp = await fetch(`${API_BASE}${path}`, { ...options, headers });

  const refreshedToken = resp.headers.get('X-Patient-Token');
  if (path === '/patient/today' && refreshedToken) {
    patientToken = refreshedToken;
    localStorage.setItem('patient_token', refreshedToken);
  }

  if (!resp.ok) {
    const text = await resp.text().catch(() => '');
    throw new Error(`${resp.status}: ${text || resp.statusText}`);
  }
  if (resp.status === 204) return undefined as T;
  return resp.json() as Promise<T>;
}

// --------------------------------------------------------------------------- //
// Patient API
// --------------------------------------------------------------------------- //
export interface TodayStatus {
  log_date: string;
  status: 'taken' | 'forgot' | 'missed' | 'pending';
  action_timestamp: string | null;
  medicine_name: string;
  medication_time: string;
  already_acted: boolean;
}

export interface PatientCalendarDay {
  log_date: string;
  status: 'taken' | 'forgot' | 'missed' | 'pending' | null;
  action_timestamp: string | null;
}

export const api = {
  // Patient
  getToday: () => request<TodayStatus>('/patient/today'),
  getPatientCalendar: (days = 28) => request<PatientCalendarDay[]>(`/patient/calendar?days=${days}`),
  recordAction: (action: 'taken' | 'forgot') =>
    request<TodayStatus>('/patient/action', { method: 'POST', body: JSON.stringify({ action }) }),
  markMissed: () => request<TodayStatus>('/patient/missed', { method: 'POST' }),
  undoToday: () => request<TodayStatus>('/patient/undo', { method: 'POST' }),

  // Auth
  login: (password: string) =>
    request<{ token: string }>('/auth/login', { method: 'POST', body: JSON.stringify({ password }) }),

  // Admin
  getAdminToday: () => request<any>('/admin/today'),
  getCalendar: (months = 3) => request<any[]>(`/admin/calendar?months=${months}`),
  updateLog: (id: number, body: any) =>
    request<any>(`/admin/logs/${id}`, { method: 'PUT', body: JSON.stringify(body) }),
  getStatistics: () => request<any>('/admin/statistics'),
  getReminderLogs: () => request<any[]>('/admin/logs/reminders'),
  getEmergencyLogs: () => request<any[]>('/admin/logs/emergencies'),
  getEventLogs: () => request<any[]>('/admin/logs/events'),

  // Settings
  getSettings: () => request<any>('/settings'),
  updateSettings: (body: any) =>
    request<any>('/settings', { method: 'PUT', body: JSON.stringify(body) }),

  // Backup
  listBackups: () => request<any[]>('/backup'),
  createBackup: () => request<any>('/backup', { method: 'POST' }),
  downloadBackupUrl: (filename: string) => `${API_BASE}/backup/download/${filename}`,

  // Export
  exportCsv: async () => {
    const resp = await fetch(`${API_BASE}/export/csv`, {
      headers: {
        Authorization: `Bearer ${adminToken}`,
      },
    });

    if (!resp.ok) {
      throw new Error(`${resp.status}: ${await resp.text()}`);
    }

    const blob = await resp.blob();
    const url = window.URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = 'medication_logs.csv';
    a.click();

    window.URL.revokeObjectURL(url);
  },

  exportCsvUrl: () => `${API_BASE}/export/csv`,
};
