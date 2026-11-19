import { useEffect, useState } from 'react';
import { Box, Typography, Card, CardContent, Tabs, Tab, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Chip } from '@mui/material';
import { api } from '@/api';

export default function LogsPage() {
  const [tab, setTab] = useState(0);
  const [reminders, setReminders] = useState<any[]>([]);
  const [emergencies, setEmergencies] = useState<any[]>([]);
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.getReminderLogs(), api.getEmergencyLogs(), api.getEventLogs()])
      .then(([r, e, ev]) => { setReminders(r); setEmergencies(e); setEvents(ev); })
      .finally(() => setLoading(false));
  }, []);

  const renderTable = (rows: any[], columns: string[], keys: string[]) => (
    <TableContainer component={Paper}>
      <Table size="small">
        <TableHead>
          <TableRow>
            {columns.map((c) => <TableCell key={c} sx={{ fontWeight: 700 }}>{c}</TableCell>)}
          </TableRow>
        </TableHead>
        <TableBody>
          {rows.map((r) => (
            <TableRow key={r.id}>
              {keys.map((k) => (
                <TableCell key={k}>
                  {k === 'success' ? (
                    <Chip label={r[k] ? 'Success' : 'Failed'} size="small" color={r[k] ? 'success' : 'error'} />
                  ) : k === 'sent_at' || k === 'created_at' ? (
                    new Date(r[k]).toLocaleString('en-US')
                  ) : (
                    r[k] ?? '—'
                  )}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );

  return (
    <Box>
      <Typography variant="h5" sx={{ fontWeight: 700, mb: 3 }}>Notification Logs</Typography>
      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label={`Reminders (${reminders.length})`} />
        <Tab label={`Emergency (${emergencies.length})`} />
        <Tab label={`Events (${events.length})`} />
      </Tabs>
      <Card>
        <CardContent>
          {tab === 0 && renderTable(reminders, ['ID', 'Date', 'Sent At', 'Success', 'Error'], ['id', 'log_date', 'sent_at', 'success', 'error_message'])}
          {tab === 1 && renderTable(emergencies, ['ID', 'Date', 'Sent At', 'Success', 'Error'], ['id', 'log_date', 'sent_at', 'success', 'error_message'])}
          {tab === 2 && renderTable(events, ['ID', 'Type', 'Message', 'Time'], ['id', 'event_type', 'message', 'created_at'])}
        </CardContent>
      </Card>
    </Box>
  );
}
