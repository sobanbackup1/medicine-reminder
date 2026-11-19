import { useEffect, useState } from 'react';
import { Box, Card, CardContent, Typography, CircularProgress, Chip, Alert } from '@mui/material';
import { api } from '@/api';

export default function TodayStatusPage() {
  const [today, setToday] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    api.getAdminToday()
      .then(setToday)
      .catch(() => setError('Could not load today\'s status.'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center' }}><CircularProgress /></Box>;
  if (error) return <Alert severity="error">{error}</Alert>;

  const statusColor = today.status === 'taken' ? '#2e7d32' : today.status === 'missed' ? '#d32f2f' : today.status === 'forgot' ? '#757575' : '#ed6c02';

  return (
    <Box>
      <Typography variant="h5" sx={{ fontWeight: 700, mb: 3 }}>Today's Status</Typography>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            {new Date(today.log_date).toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
          </Typography>
          <Chip label={today.status} sx={{ bgcolor: statusColor, color: '#fff', fontWeight: 700, textTransform: 'capitalize' }} />
          <Typography variant="body1" sx={{ color: 'text.secondary' }}>
            Action time: {today.action_timestamp ? new Date(today.action_timestamp).toLocaleString('en-US') : 'Not yet recorded'}
          </Typography>
          <Typography variant="body2" sx={{ color: 'text.secondary', mt: 1 }}>
            Created: {new Date(today.created_at).toLocaleString('en-US')}
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}
