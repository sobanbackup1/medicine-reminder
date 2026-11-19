import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Card, CardContent, Grid, Typography, CircularProgress, Button } from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';
import WarningIcon from '@mui/icons-material/Warning';
import ScheduleIcon from '@mui/icons-material/Schedule';
import { api } from '@/api';

export default function DashboardPage() {
  const [stats, setStats] = useState<any>(null);
  const [today, setToday] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([api.getStatistics(), api.getAdminToday()])
      .then(([s, t]) => { setStats(s); setToday(t); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center' }}><CircularProgress /></Box>;

  const statusColor = today?.status === 'taken' ? '#2e7d32' : today?.status === 'missed' ? '#d32f2f' : today?.status === 'forgot' ? '#757575' : '#ed6c02';

  const cards = [
    { label: "Today's Status", value: today?.status || '—', icon: <ScheduleIcon />, color: statusColor },
    { label: 'Current Streak', value: `${stats?.current_streak || 0} days`, icon: <CheckCircleIcon />, color: '#1976d2' },
    { label: 'Adherence', value: `${stats?.adherence_percentage || 0}%`, icon: <CheckCircleIcon />, color: '#2e7d32' },
    { label: 'Total Taken', value: stats?.total_taken || 0, icon: <CheckCircleIcon />, color: '#2e7d32' },
    { label: 'Total Missed', value: stats?.total_missed || 0, icon: <CancelIcon />, color: '#d32f2f' },
    { label: 'Total Forgot', value: stats?.total_forgot || 0, icon: <WarningIcon />, color: '#757575' },
  ];

  return (
    <Box>
      <Typography variant="h5" sx={{ fontWeight: 700, mb: 3 }}>Dashboard Overview</Typography>
      <Grid container spacing={3}>
        {cards.map((c) => (
          <Grid size={{ xs: 12, sm: 6, md: 4 }} key={c.label}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <Box sx={{ color: c.color }}>{c.icon}</Box>
                  <Typography variant="body2" sx={{ color: 'text.secondary' }}>{c.label}</Typography>
                </Box>
                <Typography variant="h4" sx={{ fontWeight: 700, color: c.color, textTransform: 'capitalize' }}>
                  {c.value}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
      <Box sx={{ mt: 3 }}>
        <Button variant="outlined" onClick={() => navigate('/admin/dashboard/statistics')}>View Full Statistics</Button>
      </Box>
    </Box>
  );
}
