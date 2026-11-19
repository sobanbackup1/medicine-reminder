import { useEffect, useState } from 'react';
import { Box, Card, CardContent, Grid, Typography, CircularProgress } from '@mui/material';
import { api } from '@/api';

export default function StatisticsPage() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getStatistics().then(setStats).finally(() => setLoading(false));
  }, []);

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center' }}><CircularProgress /></Box>;

  const cards = [
    { label: 'Current Streak', value: `${stats.current_streak} days` },
    { label: 'Longest Streak', value: `${stats.longest_streak} days` },
    { label: 'Adherence', value: `${stats.adherence_percentage}%` },
    { label: 'Total Taken', value: stats.total_taken },
    { label: 'Total Missed', value: stats.total_missed },
    { label: 'Total Forgotten', value: stats.total_forgot },
    { label: 'Avg Confirmation Time', value: stats.average_confirmation_minutes != null ? `${stats.average_confirmation_minutes} min` : '—' },
  ];

  return (
    <Box>
      <Typography variant="h5" sx={{ fontWeight: 700, mb: 3 }}>Statistics</Typography>
      <Grid container spacing={3}>
        {cards.map((c) => (
          <Grid size={{ xs: 12, sm: 6, md: 3 }} key={c.label}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="body2" gutterBottom sx={{ color: 'text.secondary' }}>{c.label}</Typography>
                <Typography variant="h4" sx={{ fontWeight: 700 }}>{c.value}</Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}
