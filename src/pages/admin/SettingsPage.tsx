import { useEffect, useState } from 'react';
import { Box, Typography, Card, CardContent, Grid, TextField, Button, Alert, CircularProgress, Divider } from '@mui/material';
import { api } from '@/api';

export default function SettingsPage() {
  const [settings, setSettings] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    api.getSettings().then(setSettings).finally(() => setLoading(false));
  }, []);

  const update = (field: string, value: string | number) => {
    setSettings({ ...settings, [field]: value });
  };

  const save = async () => {
    setSaving(true);
    setMsg('');
    try {
      const payload = { ...settings };
      ['patient_bark_key', 'emergency_bark_key', 'admin_password'].forEach((key) => {
        if (!payload[key]) delete payload[key];
      });
      const updated = await api.updateSettings(payload);
      setSettings(updated);
      setMsg('Settings saved successfully.');
    } catch {
      setMsg('Failed to save settings.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center' }}><CircularProgress /></Box>;

  const fields = [
    { key: 'medicine_name', label: 'Medicine Name', type: 'text' },
    { key: 'medication_time', label: 'Medication Time (HH:MM)', type: 'text' },
    { key: 'reminder_start_time', label: 'Reminder Start Time (HH:MM)', type: 'text' },
    { key: 'reminder_interval_minutes', label: 'Reminder Interval (minutes)', type: 'number' },
    { key: 'emergency_time', label: 'Emergency Notification Time (HH:MM)', type: 'text' },
    { key: 'patient_bark_key', label: 'Patient Bark API Key (leave blank to keep)', type: 'password' },
    { key: 'emergency_bark_key', label: 'Emergency Bark API Key (leave blank to keep)', type: 'password' },
    { key: 'notification_title', label: 'Notification Title', type: 'text' },
    { key: 'notification_body', label: 'Notification Message', type: 'text' },
    { key: 'website_url', label: 'Website URL', type: 'text' },
    { key: 'admin_password', label: 'Admin Password (leave blank to keep)', type: 'password' },
    { key: 'retention_days', label: 'Retention Days', type: 'number' },
  ];

  return (
    <Box>
      <Typography variant="h5" sx={{ fontWeight: 700, mb: 3 }}>Settings</Typography>
      <Card>
        <CardContent>
          <Grid container sx={{ spacing: 2 }}>
            {fields.map((f) => (
              <Grid size={{ xs: 12, sm: 6 }} key={f.key}>
                <TextField
                  fullWidth
                  label={f.label}
                  type={f.type === 'number' ? 'number' : f.type}
                  value={settings[f.key] ?? ''}
                  onChange={(e) => update(f.key, f.type === 'number' ? Number(e.target.value) : e.target.value)}
                  margin="normal"
                />
              </Grid>
            ))}
          </Grid>
          <Divider sx={{ my: 2 }} />
          {msg && <Alert severity={msg.includes('Failed') ? 'error' : 'success'} sx={{ mb: 2 }}>{msg}</Alert>}
          <Button variant="contained" size="large" onClick={save} disabled={saving}>
            {saving ? 'Saving...' : 'Save Settings'}
          </Button>
        </CardContent>
      </Card>
    </Box>
  );
}
