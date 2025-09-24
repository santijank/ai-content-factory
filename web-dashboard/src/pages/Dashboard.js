import React, { useEffect, useState } from 'react';
import { 
  Grid, 
  Card, 
  CardContent, 
  Typography, 
  Box,
  LinearProgress,
  Button,
  Chip,
  Avatar,
  IconButton
} from '@mui/material';
import { 
  TrendingUp, 
  Lightbulb, 
  VideoLibrary, 
  AttachMoney,
  PlayArrow,
  Refresh,
  AutoAwesome,
  Schedule,
  Visibility,
  ThumbUp
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { useAppStore } from '../store/appStore';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';

const Dashboard = () => {
  const { 
    dashboardData, 
    updateDashboardData,
    trends,
    opportunities,
    contentQueue,
    loading,
    setLoading 
  } = useAppStore();

  const [revenueData, setRevenueData] = useState([]);
  const [trendsData, setTrendsData] = useState([]);

  useEffect(() => {
    loadDashboardData();
    generateChartData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      updateDashboardData({
        trendsCount: 47,
        opportunitiesCount: 23,
        contentCount: 156,
        todayRevenue: 8450,
        weeklyRevenue: 52300,
        monthlyRevenue: 198750,
        totalViews: 2450000,
        totalLikes: 89500,
        conversionRate: 3.2,
        avgContentCost: 125
      });
    } catch (error) {
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const generateChartData = () => {
    // Revenue chart data
    const revenueChart = Array.from({ length: 7 }, (_, i) => ({
      day: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][i],
      revenue: Math.floor(Math.random() * 10000) + 5000,
      content: Math.floor(Math.random() * 20) + 10
    }));
    setRevenueData(revenueChart);

    // Trends performance data
    const trendsChart = Array.from({ length: 12 }, (_, i) => ({
      hour: `${(i + 8) % 24}:00`,
      trends: Math.floor(Math.random() * 50) + 20,
      opportunities: Math.floor(Math.random() * 30) + 10
    }));
    setTrendsData(trendsChart);
  };

  const statsCards = [
    {
      title: "Today's Revenue",
      value: `฿${dashboardData.todayRevenue?.toLocaleString() || '0'}`,
      change: '+23%',
      icon: <AttachMoney />,
      color: '#10B981',
      bgColor: '#10B98110'
    },
    {
      title: 'Active Trends',
      value: dashboardData.trendsCount || '0',
      change: '+8 new',
      icon: <TrendingUp />,
      color: '#F59E0B',
      bgColor: '#F59E0B10'
    },
    {
      title: 'Opportunities',
      value: dashboardData.opportunitiesCount || '0',
      change: '+15 today',
      icon: <Lightbulb />,
      color: '#EF4444',
      bgColor: '#EF444410'
    },
    {
      title: 'Content Created',
      value: dashboardData.contentCount || '0',
      change: '+12 this week',
      icon: <VideoLibrary />,
      color: '#3B82F6',
      bgColor: '#3B82F610'
    }
  ];

  const quickActions = [
    {
      title: 'Generate Content',
      description: 'AI-powered content creation',
      icon: <AutoAwesome />,
      color: '#EC4899',
      action: () => toast.success('Content generation started!')
    },
    {
      title: 'Schedule Posts',
      description: 'Auto-schedule to platforms',
      icon: <Schedule />,
      color: '#06B6D4',
      action: () => toast.success('Scheduling interface opened!')
    },
    {
      title: 'Analyze Trends',
      description: 'Deep trend analysis',
      icon: <TrendingUp />,
      color: '#8B5CF6',
      action: () => toast.success('Trend analysis running!')
    }
  ];

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 600, mb: 1 }}>
            Dashboard
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Monitor your AI content factory performance
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={loadDashboardData}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<PlayArrow />}
            sx={{ bgcolor: '#10B981', '&:hover': { bgcolor: '#059669' } }}
          >
            Start AI Factory
          </Button>
        </Box>
      </Box>

      {loading && <LinearProgress sx={{ mb: 3 }} />}

      <Grid container spacing={3}>
        {/* Stats Cards */}
        {statsCards.map((card, index) => (
          <Grid item xs={12} sm={6} lg={3} key={card.title}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card sx={{ 
                background: 'linear-gradient(135deg, #1E293B 0%, #334155 100%)',
                border: '1px solid #334155',
                position: 'relative',
                overflow: 'hidden'
              }}>
                <Box
                  sx={{
                    position: 'absolute',
                    top: 0,
                    right: 0,
                    width: 100,
                    height: 100,
                    background: card.bgColor,
                    borderRadius: '50%',
                    transform: 'translate(30%, -30%)'
                  }}
                />
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Box>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        {card.title}
                      </Typography>
                      <Typography variant="h4" sx={{ fontWeight: 600, mb: 1 }}>
                        {card.value}
                      </Typography>
                      <Chip 
                        label={card.change} 
                        size="small" 
                        sx={{ 
                          bgcolor: `${card.color}20`,
                          color: card.color,
                          fontWeight: 600
                        }} 
                      />
                    </Box>
                    <Avatar sx={{ bgcolor: card.color, width: 56, height: 56 }}>
                      {card.icon}
                    </Avatar>
                  </Box>
                </CardContent>
              </Card>
            </motion.div>
          </Grid>
        ))}

        {/* Revenue Chart */}
        <Grid item xs={12} lg={8}>
          <Card sx={{ background: 'linear-gradient(135deg, #1E293B 0%, #334155 100%)', border: '1px solid #334155' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Revenue & Content Performance
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={revenueData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="day" stroke="#CBD5E1" />
                  <YAxis stroke="#CBD5E1" />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#1E293B', 
                      border: '1px solid #334155',
                      borderRadius: '8px'
                    }} 
                  />
                  <Line 
                    type="monotone" 
                    dataKey="revenue" 
                    stroke="#10B981" 
                    strokeWidth={3}
                    dot={{ fill: '#10B981', strokeWidth: 2, r: 6 }}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="content" 
                    stroke="#3B82F6" 
                    strokeWidth={2}
                    dot={{ fill: '#3B82F6', strokeWidth: 2, r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12} lg={4}>
          <Card sx={{ background: 'linear-gradient(135deg, #1E293B 0%, #334155 100%)', border: '1px solid #334155' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {quickActions.map((action, index) => (
                  <motion.div
                    key={action.title}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                  >
                    <Card 
                      sx={{ 
                        bgcolor: '#0F172A', 
                        cursor: 'pointer',
                        transition: 'all 0.2s ease',
                        '&:hover': {
                          transform: 'translateY(-2px)',
                          boxShadow: `0 8px 25px ${action.color}20`
                        }
                      }}
                      onClick={action.action}
                    >
                      <CardContent sx={{ py: 2 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                          <Avatar sx={{ bgcolor: action.color, width: 40, height: 40 }}>
                            {action.icon}
                          </Avatar>
                          <Box>
                            <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                              {action.title}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {action.description}
                            </Typography>
                          </Box>
                        </Box>
                      </CardContent>
                    </Card>
                  </motion.div>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Live Trends */}
        <Grid item xs={12} md={6}>
          <Card sx={{ background: 'linear-gradient(135deg, #1E293B 0%, #334155 100%)', border: '1px solid #334155' }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">
                  Live Trends Monitor
                </Typography>
                <IconButton size="small" sx={{ color: '#10B981' }}>
                  <Refresh />
                </IconButton>
              </Box>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={trendsData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="hour" stroke="#CBD5E1" />
                  <YAxis stroke="#CBD5E1" />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#1E293B', 
                      border: '1px solid #334155',
                      borderRadius: '8px'
                    }} 
                  />
                  <Bar dataKey="trends" fill="#F59E0B" radius={4} />
                  <Bar dataKey="opportunities" fill="#EF4444" radius={4} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Content Queue Status */}
        <Grid item xs={12} md={6}>
          <Card sx={{ background: 'linear-gradient(135deg, #1E293B 0%, #334155 100%)', border: '1px solid #334155' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Content Production Queue
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {contentQueue.length > 0 ? (
                  contentQueue.slice(0, 4).map((item, index) => (
                    <Box key={item.id} sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Avatar sx={{ 
                        bgcolor: item.status === 'completed' ? '#10B981' : 
                                item.status === 'processing' ? '#F59E0B' : '#6B7280',
                        width: 32,
                        height: 32
                      }}>
                        {item.status === 'completed' ? <VideoLibrary /> : 
                         item.status === 'processing' ? <AutoAwesome /> : <Schedule />}
                      </Avatar>
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {item.title || `Content Item #${index + 1}`}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {item.status} • {new Date(item.createdAt).toLocaleTimeString()}
                        </Typography>
                      </Box>
                      <Chip 
                        label={item.status}
                        size="small"
                        sx={{
                          bgcolor: item.status === 'completed' ? '#10B98120' : 
                                  item.status === 'processing' ? '#F59E0B20' : '#6B728020',
                          color: item.status === 'completed' ? '#10B981' : 
                                item.status === 'processing' ? '#F59E0B' : '#6B7280'
                        }}
                      />
                    </Box>
                  ))
                ) : (
                  <Box sx={{ textAlign: 'center', py: 4 }}>
                    <Typography variant="body2" color="text.secondary">
                      No content in queue
                    </Typography>
                    <Button 
                      variant="outlined" 
                      size="small" 
                      sx={{ mt: 2 }}
                      startIcon={<AutoAwesome />}
                    >
                      Create Content
                    </Button>
                  </Box>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Platform Performance */}
        <Grid item xs={12}>
          <Card sx={{ background: 'linear-gradient(135deg, #1E293B 0%, #334155 100%)', border: '1px solid #334155' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Platform Performance Overview
              </Typography>
              <Grid container spacing={3}>
                <Grid item xs={12} sm={6} md={3}>
                  <Card sx={{ bgcolor: '#0F172A' }}>
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Avatar sx={{ bgcolor: '#FF0000', width: 48, height: 48, mx: 'auto', mb: 2 }}>
                        YT
                      </Avatar>
                      <Typography variant="h6">1.2M</Typography>
                      <Typography variant="caption" color="text.secondary">Views</Typography>
                      <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mt: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <Visibility fontSize="small" />
                          <Typography variant="caption">85K</Typography>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <ThumbUp fontSize="small" />
                          <Typography variant="caption">12K</Typography>
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card sx={{ bgcolor: '#0F172A' }}>
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Avatar sx={{ bgcolor: '#000000', width: 48, height: 48, mx: 'auto', mb: 2 }}>
                        TT
                      </Avatar>
                      <Typography variant="h6">890K</Typography>
                      <Typography variant="caption" color="text.secondary">Views</Typography>
                      <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mt: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <Visibility fontSize="small" />
                          <Typography variant="caption">67K</Typography>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <ThumbUp fontSize="small" />
                          <Typography variant="caption">9.5K</Typography>
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card sx={{ bgcolor: '#0F172A' }}>
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Avatar sx={{ bgcolor: '#E4405F', width: 48, height: 48, mx: 'auto', mb: 2 }}>
                        IG
                      </Avatar>
                      <Typography variant="h6">245K</Typography>
                      <Typography variant="caption" color="text.secondary">Views</Typography>
                      <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mt: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <Visibility fontSize="small" />
                          <Typography variant="caption">23K</Typography>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <ThumbUp fontSize="small" />
                          <Typography variant="caption">3.2K</Typography>
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card sx={{ bgcolor: '#0F172A' }}>
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Avatar sx={{ bgcolor: '#1877F2', width: 48, height: 48, mx: 'auto', mb: 2 }}>
                        FB
                      </Avatar>
                      <Typography variant="h6">156K</Typography>
                      <Typography variant="caption" color="text.secondary">Views</Typography>
                      <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mt: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <Visibility fontSize="small" />
                          <Typography variant="caption">18K</Typography>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <ThumbUp fontSize="small" />
                          <Typography variant="caption">2.1K</Typography>
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;