import React, { useState } from 'react';
import {
  Box,
  Button,
  TextField,
  Typography,
  Paper,
  CircularProgress,
  Alert,
} from '@mui/material';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000';

function ReportViewer() {
  const [stockName, setStockName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [reportUrl, setReportUrl] = useState(null);
  const [generationStatus, setGenerationStatus] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setReportUrl(null);
    setGenerationStatus('Starting report generation...');

    try {
      const response = await axios.post(`${API_BASE_URL}/generate-report`, {
        stock_name: stockName,
      });

      console.log('API Response:', response.data); // Debug log

      if (response.data.path) {
        const fullReportUrl = `${API_BASE_URL}${response.data.path}?t=${Date.now()}`; // Prevent caching
        console.log('Final Report URL:', fullReportUrl); // Debug log
        setReportUrl(fullReportUrl);
        setGenerationStatus('Report generated successfully!');
      } else {
        throw new Error('No report path in response');
      }
    } catch (err) {
      console.error('Error details:', err); // Debug log
      setError(
        err.response?.data?.error || 
        err.message || 
        'An error occurred while generating the report'
      );
      setGenerationStatus('');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box className="report_viewer" sx={{ py: 4, mt: 4, mx: 5 }}>  {/* Top margin: 4, Horizontal margin: 3 */}

    {/* <Box sx={{ py: 4 }}> */}
      <Typography variant="h4" component="h1" gutterBottom>
        Stock Analysis Report Generator
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <form onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label="Stock Name"
            value={stockName}
            onChange={(e) => setStockName(e.target.value)}
            disabled={loading}
            required
            sx={{ mb: 2 }}
          />
          <Button
            type="submit"
            variant="contained"
            disabled={loading || !stockName}
            sx={{ mr: 2 }}
          >
            {loading ? 'Generating...' : 'Generate Report'}
          </Button>
        </form>
      </Paper>

      {loading && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <CircularProgress size={24} />
          <Typography>{generationStatus}</Typography>
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {reportUrl && (
        <Box>
          <Alert severity="success" sx={{ mb: 2 }}>
            Report generated successfully!
          </Alert>
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Report URL: {reportUrl}
            </Typography>
          </Box>
          <iframe
            src={reportUrl}
            title="Generated Report"
            style={{
              width: '100%',
              height: '800px',
              border: '1px solid #ccc',
              borderRadius: '4px',
            }}
          />
        </Box>
      )}
    </Box>
  );
}

export default ReportViewer;