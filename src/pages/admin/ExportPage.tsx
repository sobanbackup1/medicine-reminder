import { Box, Typography, Card, CardContent, Button } from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import { api } from '@/api';

export default function ExportPage() {
  return (
    <Box>
      <Typography variant="h5" sx={{ fontWeight: 700, mb: 3 }}>Export Medication History</Typography>
      <Card>
        <CardContent>
          <Typography variant="body1" gutterBottom sx={{ color: 'text.secondary' }}>
            Download the full medication history as a CSV file. This includes all recorded days, their status, and timestamps.
          </Typography>
          <Button
          variant="contained"
          size="large"
          startIcon={<DownloadIcon />}
          onClick={() => api.exportCsv()}
          sx={{ mt: 2 }}
          >
            Download CSV
          </Button>
        </CardContent>
      </Card>
    </Box>
  );
}
