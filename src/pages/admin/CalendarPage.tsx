import { useEffect, useState } from 'react';
import {
  Box, Typography, Paper, CircularProgress, Dialog, DialogTitle,
  DialogContent, DialogActions, Button, Chip, Divider,
} from '@mui/material';
import { api } from '@/api';

const statusColor: Record<string, string> = {
  taken: '#2e7d32',
  forgot: '#f9a825',
  missed: '#d32f2f',
  pending: '#bdbdbd',
};

const statusBg: Record<string, string> = {
  taken: '#c8e6c9',
  forgot: '#fff9c4',
  missed: '#ffcdd2',
  pending: '#e0e0e0',
};

export default function CalendarPage() {
  const [days, setDays] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<any>(null);
  const [reminders, setReminders] = useState<any[]>([]);
  const [emergencies, setEmergencies] = useState<any[]>([]);

  useEffect(() => {
    api.getCalendar(3).then(setDays).finally(() => setLoading(false));
  }, []);

  const openDay = async (day: any) => {
    setSelected(day);
    setReminders([]);
    setEmergencies([]);
    // The calendar endpoint returns date + status; we don't have per-day logs
    // here, so we show what we have.
  };

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center' }}><CircularProgress /></Box>;

  // Group days into weeks for display
  const weeks: any[][] = [];
  let week: any[] = [];
  const first = days[0];
  if (first) {
    const startDow = new Date(first.log_date).getDay();
    for (let i = 0; i < startDow; i++) week.push(null);
  }
  days.forEach((d) => {
    week.push(d);
    if (week.length === 7) { weeks.push(week); week = []; }
  });
  if (week.length) weeks.push(week);

  return (
    <Box>
      <Typography variant="h5" sx={{ fontWeight: 700, mb: 3 }}>Calendar (Last 3 Months)</Typography>
      <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
        {[
          { label: 'Taken', c: statusBg.taken },
          { label: 'Forgot', c: statusBg.forgot },
          { label: 'Missed', c: statusBg.missed },
          { label: 'Future', c: statusBg.pending },
        ].map((l) => (
          <Box key={l.label} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box sx={{ width: 16, height: 16, borderRadius: 1, bgcolor: l.c }} />
            <Typography variant="body2">{l.label}</Typography>
          </Box>
        ))}
      </Box>
      <Paper sx={{ p: 2, overflowX: 'auto' }}>
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 0.5, minWidth: 490 }}>
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((d) => (
            <Box key={d} sx={{ textAlign: 'center', pb: 1 }}>
              <Typography variant="caption" sx={{ fontWeight: 600 }}>{d}</Typography>
            </Box>
          ))}
          {weeks.flat().map((d, i) => (
            <Box key={i}>
              {d ? (
                <Box
                  onClick={() => openDay(d)}
                  sx={{
                    aspectRatio: '1',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    borderRadius: 1,
                    cursor: 'pointer',
                    bgcolor: d.status ? statusBg[d.status] : '#f5f5f5',
                    border: '1px solid #e0e0e0',
                    transition: 'transform 0.15s, box-shadow 0.15s',
                    '&:hover': { transform: 'scale(1.08)', boxShadow: 2 },
                  }}
                >
                  <Typography variant="caption" sx={{ fontWeight: 600 }}>
                    {new Date(d.log_date).getDate()}
                  </Typography>
                </Box>
              ) : (
                <Box sx={{ aspectRatio: '1' }} />
              )}
            </Box>
          ))}
        </Box>
      </Paper>

      <Dialog open={!!selected} onClose={() => setSelected(null)} maxWidth="sm" fullWidth>

        <DialogTitle>
          {selected ? new Date(selected.log_date).toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }) : ''}
        </DialogTitle>
        <DialogContent>
          {selected && (
            <>
              <Chip
                label={selected.status || 'No record'}
                sx={{
                  bgcolor: selected.status ? statusColor[selected.status] : '#bdbdbd',
                  color: '#fff',
                  fontWeight: 700,
                  textTransform: 'capitalize',
                  mb: 2,
                }}
              />
              <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                Action time: {selected.action_timestamp ? new Date(selected.action_timestamp).toLocaleString('en-US') : '—'}
              </Typography>
              <Divider sx={{ my: 2 }} />
              <Typography variant="subtitle2">Reminder History</Typography>
              {reminders.length === 0 ? (
                <Typography variant="body2" sx={{ color: 'text.secondary' }}>No reminders recorded for this day.</Typography>
              ) : (
                reminders.map((r) => (
                  <Typography key={r.id} variant="body2">
                    {new Date(r.sent_at).toLocaleTimeString('en-US')} — {r.success ? '✓ Sent' : `✗ ${r.error_message}`}
                  </Typography>
                ))
              )}
              <Divider sx={{ my: 2 }} />
              <Typography variant="subtitle2">Emergency Notification</Typography>
              {emergencies.length === 0 ? (
                <Typography variant="body2" sx={{ color: 'text.secondary' }}>No emergency notification sent.</Typography>
              ) : (
                emergencies.map((e) => (
                  <Typography key={e.id} variant="body2">
                    {new Date(e.sent_at).toLocaleTimeString('en-US')} — {e.success ? '✓ Sent' : `✗ ${e.error_message}`}
                  </Typography>
                ))
              )}
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelected(null)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
