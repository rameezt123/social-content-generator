import React, { useState } from 'react';
import { Container, Typography, Button, TextField, Box, Grid, Paper, CircularProgress, Alert, Accordion, AccordionSummary, AccordionDetails } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'; // Use environment variable or fallback to localhost
console.log('API_URL:', API_URL); // Debug: log the API URL being used

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
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState('');

  const handleFileChange = (e) => {
    setPdf(e.target.files[0]);
    setFilename('');
    setContent({ instagram: '', twitter: '', blog: '', podcast: '' });
    setSummary(null);
    setError('');
  };

  const handleUpload = async () => {
    if (!pdf) return;
    setLoading(true);
    setError('');
    const formData = new FormData();
    formData.append('file', pdf);
    try {
      console.log('Attempting to upload to:', `${API_URL}/upload`); // Debug: log the upload URL
      const res = await fetch(`${API_URL}/upload`, {
        method: 'POST',
        body: formData
      });
      console.log('Upload response status:', res.status); // Debug: log response status
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.error || 'Upload failed');
      }
      const data = await res.json();
      setFilename(data.filename);
    } catch (err) {
      console.error('Upload error:', err); // Debug: log the full error
      setError(`Upload failed: ${err.message}`);
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
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.error || 'Generation failed');
      }
      const data = await res.json();
      setContent({
        instagram: data.instagram || '',
        twitter: data.twitter || '',
        blog: data.blog || '',
        podcast: data.podcast || ''
      });
      setSummary(data.summary || null);
    } catch (err) {
      setError(`Generation failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleContentChange = (field, value) => {
    setContent((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom align="center">Social Content Generator</Typography>
      
      <Paper sx={{ p: 3, mb: 4 }}>
        <Box display="flex" alignItems="center" gap={2} flexWrap="wrap">
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
          {pdf && <Typography variant="body2">{pdf.name}</Typography>}
          <Button 
            variant="contained" 
            color="primary" 
            onClick={handleUpload} 
            disabled={!pdf || loading}
          >
            {loading ? <CircularProgress size={24} /> : 'Upload'}
          </Button>
          <Button 
            variant="contained" 
            color="success" 
            onClick={handleGenerate} 
            disabled={!filename || loading}
          >
            {loading ? <CircularProgress size={24} /> : 'Generate Content'}
          </Button>
        </Box>
        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}
      </Paper>

      {summary && (
        <Paper sx={{ p: 3, mb: 4 }}>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Article Summary</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle1" fontWeight="bold">Title:</Typography>
                  <Typography variant="body2" sx={{ mb: 2 }}>{summary.title || 'N/A'}</Typography>
                  
                  <Typography variant="subtitle1" fontWeight="bold">Authors:</Typography>
                  <Typography variant="body2" sx={{ mb: 2 }}>{summary.authors || 'N/A'}</Typography>
                  
                  <Typography variant="subtitle1" fontWeight="bold">Main Findings:</Typography>
                  <Typography variant="body2" sx={{ mb: 2 }}>{summary.main_findings || 'N/A'}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle1" fontWeight="bold">Key Points:</Typography>
                  <Typography variant="body2" sx={{ mb: 2 }}>{summary.key_points || 'N/A'}</Typography>
                  
                  <Typography variant="subtitle1" fontWeight="bold">Conclusions:</Typography>
                  <Typography variant="body2" sx={{ mb: 2 }}>{summary.conclusions || 'N/A'}</Typography>
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>
        </Paper>
      )}

      <Grid container spacing={3}>
        {['instagram', 'twitter', 'blog', 'podcast'].map((type) => (
          <Grid item xs={12} md={6} key={type}>
            <Paper sx={{ p: 2, minHeight: 300 }}>
              <Typography variant="h6" gutterBottom textTransform="capitalize">
                {type === 'instagram' ? 'Instagram Carousel' : 
                 type === 'twitter' ? 'Twitter Thread' : 
                 type === 'blog' ? 'Blog Post' : 'Podcast Script'}
              </Typography>
              <TextField
                multiline
                minRows={10}
                fullWidth
                value={content[type]}
                onChange={e => handleContentChange(type, e.target.value)}
                variant="outlined"
                placeholder={`Generated ${type} content will appear here...`}
              />
            </Paper>
          </Grid>
        ))}
      </Grid>
    </Container>
  );
}

export default App;
