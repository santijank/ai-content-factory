// src/pages/Analytics.js
import React from 'react';
import { Box, Typography, Card, CardContent, Grid } from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const Analytics = () => {
  const data = [
    { name: 'YouTube', views: 4000, revenue: 2400 },
    { name: 'TikTok', views: 3000, revenue: 1398 },
    { name: 'Instagram', views: 2000, revenue: 9800 },
    { name: 'Facebook', views: 2780, revenue: 3908 }
  ];

  const pieData = [
    { name: 'Educational', value: 400, color: '#3B82F6' },
    { name: 'Entertainment', value: 300, color: '#EC4899' },
    { name: 'Lifestyle', value: 300, color: '#10B981' },
    { name: 'News', value: 200, color: '#F59E0B' }
  ];

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 600, mb: 1 }}>
        Analytics Dashboard
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Performance insights and metrics
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card sx={{ background: 'linear-gradient(135deg, #1E293B 0%, #334155 100%)', border: '1px solid #334155' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Platform Performance
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="name" stroke="#CBD5E1" />
                  <YAxis stroke="#CBD5E1" />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#1E293B', 
                      border: '1px solid #334155',
                      borderRadius: '8px'
                    }} 
                  />
                  <Bar dataKey="views" fill="#3B82F6" radius={4} />
                  <Bar dataKey="revenue" fill="#10B981" radius={4} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ background: 'linear-gradient(135deg, #1E293B 0%, #334155 100%)', border: '1px solid #334155' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Content Types
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

// src/pages/Settings.js
import React, { useState } from 'react';
import { 
  Box, 
  Typography, 
  Card, 
  CardContent, 
  Grid, 
  TextField, 
  Switch, 
  FormControlLabel,
  Button,
  Divider,
  Select,
  MenuItem,
  FormControl,
  InputLabel
} from '@mui/material';
import { Save, Refresh } from '@mui/icons-material';
import { useAppStore } from '../store/appStore';
import toast from 'react-hot-toast';

const Settings = () => {
  const { user, updateUserSettings } = useAppStore();
  const [settings, setSettings] = useState({
    name: user.name,
    tier: user.tier,
    activePlatforms: user.activePlatforms,
    autoRefresh: true,
    notifications: true,
    darkMode: true,
    language: 'en'
  });

  const handleSave = () => {
    updateUserSettings(settings);
    toast.success('Settings saved successfully!');
  };

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 600, mb: 1 }}>
        Settings
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Customize your AI Content Factory experience
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card sx={{ background: 'linear-gradient(135deg, #1E293B 0%, #334155 100%)', border: '1px solid #334155' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Account Settings
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                <TextField
                  label="Display Name"
                  value={settings.name}
                  onChange={(e) => setSettings({ ...settings, name: e.target.value })}
                  fullWidth
                />
                <FormControl fullWidth>
                  <InputLabel>Quality Tier</InputLabel>
                  <Select
                    value={settings.tier}
                    onChange={(e) => setSettings({ ...settings, tier: e.target.value })}
                  >
                    <MenuItem value="BUDGET">Budget</MenuItem>
                    <MenuItem value="BALANCED">Balanced</MenuItem>
                    <MenuItem value="PREMIUM">Premium</MenuItem>
                  </Select>
                </FormControl>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card sx={{ background: 'linear-gradient(135deg, #1E293B 0%, #334155 100%)', border: '1px solid #334155' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Preferences
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.autoRefresh}
                      onChange={(e) => setSettings({ ...settings, autoRefresh: e.target.checked })}
                    />
                  }
                  label="Auto Refresh Trends"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.notifications}
                      onChange={(e) => setSettings({ ...settings, notifications: e.target.checked })}
                    />
                  }
                  label="Push Notifications"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.darkMode}
                      onChange={(e) => setSettings({ ...settings, darkMode: e.target.checked })}
                    />
                  }
                  label="Dark Mode"
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Box sx={{ mt: 4, display: 'flex', gap: 2 }}>
        <Button
          variant="contained"
          startIcon={<Save />}
          onClick={handleSave}
          sx={{ bgcolor: '#10B981', '&:hover': { bgcolor: '#059669' } }}
        >
          Save Changes
        </Button>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
        >
          Reset to Defaults
        </Button>
      </Box>
    </Box>
  );
};

export { Analytics, Settings };