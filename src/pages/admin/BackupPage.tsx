import { useEffect, useState } from 'react';
import { Box, Typography, Card, CardContent, Button, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Chip, Alert, CircularProgress } from '@mui/material';
import { api } from '@/api';

export default function BackupPage() {
  const [backups, setBackups] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [msg, setMsg] = useState('');

  const load = () => {
    setLoading(true);
    api.listBackups().then(setBackups).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const create = async () => {
    setCreating(true);
    setMsg('');
    try {
      const res = await api.createBackup();
      setMsg(res.success ? `Backup created: ${res.filename}` : 'Backup failed.');
      load();
    } catch {
      setMsg('Backup failed.');
    } finally {
      setCreating(false);
    }
  };

  return (
    <Box>
      <Typography variant="h5" sx={{ fontWeight: 700, mb: 3 }}>Backup</Typography>
      {msg && <Alert severity={msg.includes('failed') ? 'error' : 'success'} sx={{ mb: 2 }}>{msg}</Alert>}
      <Button variant="contained" size="large" onClick={create} disabled={creating} sx={{ mb: 3 }}>
        {creating ? 'Creating...' : 'Create Backup Now'}
      </Button>
      {loading ? (
        <CircularProgress />
      ) : (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Backup History</Typography>
            <TableContainer component={Paper}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 700 }}>Date</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Filename</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Size</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Download</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {backups.map((b) => (
                    <TableRow key={b.id}>
                      <TableCell>{new Date(b.created_at).toLocaleString('en-US')}</TableCell>
                      <TableCell>{b.filename}</TableCell>
                      <TableCell>{b.file_size ? `${(b.file_size / 1024).toFixed(1)} KB` : '—'}</TableCell>
                      <TableCell><Chip label={b.success ? 'Success' : 'Failed'} size="small" color={b.success ? 'success' : 'error'} /></TableCell>
                      <TableCell>
                        {b.success && (
                          <Button size="small" href={api.downloadBackupUrl(b.filename)} download>Download</Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                  {backups.length === 0 && (
                    <TableRow><TableCell colSpan={5} align="center">No backups yet.</TableCell></TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}
    </Box>
  );
}
