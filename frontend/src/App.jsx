import React, { useState } from 'react';
import { Container, Typography, Button, TextField, Box, Grid, Paper, CircularProgress } from '@mui/material';

const API_URL = 'http://localhost:8000'; // Adjust if backend runs elsewhere

function App() {
  const [pdf, setPdf] = useState(null);
  const [filename, setFilename] = useState('');
  const [loading, setLoading] = useState(false);
  const [content, setContent] = useState({
    instagram: '',
    twitter: '',
    blog: '',
    podcast: ''
  });
  const [error, setError] = useState('');

  const handleFileChange = (e) => {
    setPdf(e.target.files[0]);
    setFilename('');
    setContent({ instagram: '', twitter: '', blog: '', podcast: '' });
    setError('');
  };

  const handleUpload = async () => {
    if (!pdf) return;
    setLoading(true);
    setError('');
    const formData = new FormData();
    formData.append('file', pdf);
    try {
      const res = await fetch(`${API_URL}/upload`, {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      setFilename(data.filename);
    } catch (err) {
      setError('Upload failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    if (!filename) return;
    setLoading(true);
    setError('');
    const formData = new FormData();
    formData.append('filename', filename);
    try {
      const res = await fetch(`${API_URL}/generate`, {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      setContent(data);
    } catch (err) {
      setError('Generation failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleContentChange = (field, value) => {
    setContent((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom align="center">Social Content Generator</Typography>
      <Paper sx={{ p: 3, mb: 4 }}>
        <Box display="flex" alignItems="center" gap={2}>
          <input
            type="file"
            accept="application/pdf"
            onChange={handleFileChange}
            style={{ display: 'none' }}
            id="pdf-upload"
          />
          <label htmlFor="pdf-upload">
            <Button variant="contained" component="span">Upload PDF</Button>
          </label>
          {pdf && <Typography>{pdf.name}</Typography>}
          <Button variant="contained" color="primary" onClick={handleUpload} disabled={!pdf || loading}>
            {loading ? <CircularProgress size={24} /> : 'Upload'}
          </Button>
          <Button variant="contained" color="success" onClick={handleGenerate} disabled={!filename || loading}>
            {loading ? <CircularProgress size={24} /> : 'Generate'}
          </Button>
        </Box>
        {error && <Typography color="error" sx={{ mt: 2 }}>{error}</Typography>}
      </Paper>
      <Grid container spacing={3}>
        {['instagram', 'twitter', 'blog', 'podcast'].map((type) => (
          <Grid item xs={12} md={6} key={type}>
            <Paper sx={{ p: 2, minHeight: 220 }}>
              <Typography variant="h6" gutterBottom textTransform="capitalize">{type} Copy</Typography>
              <TextField
                multiline
                minRows={6}
                fullWidth
                value={content[type]}
                onChange={e => handleContentChange(type, e.target.value)}
                variant="outlined"
              />
            </Paper>
          </Grid>
        ))}
      </Grid>
      {/* Placeholder for image previews */}
      {/* <Box mt={4}><Typography variant="h6">Image Previews Coming Soon</Typography></Box> */}
    </Container>
  );
}

export default App;
