import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  Button,
  IconButton,
  TextField,
  InputAdornment,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  LinearProgress,
  Avatar,
  Fab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import {
  Search,
  FilterList,
  Refresh,
  TrendingUp,
  TrendingDown,
  WhatshotRounded,
  YouTube,
  Twitter,
  Reddit,
  Google,
  PlayArrow,
  Pause,
  AutoAwesome,
  Add
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { useAppStore } from '../store/appStore';
import toast from 'react-hot-toast';

const Trends = () => {
  const { trends, setTrends, selectedTrends, toggleTrendSelection, loading, setLoading } = useAppStore();
  const [searchTerm, setSearchTerm] = useState('');
  const [sourceFilter, setSourceFilter] = useState('all');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [sortBy, setSortBy] = useState('popularity');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);

  useEffect(() => {
    loadTrends();
    
    let interval;
    if (autoRefresh) {
      interval = setInterval(() => {
        loadTrends();
      }, 30000); // Refresh every 30 seconds
    }
    
    return () => interval && clearInterval(interval);
  }, [autoRefresh]);

  const loadTrends = async () => {
    setLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const mockTrends = [
        {
          id: 1,
          topic: 'AI Automation Tools 2025',
          keywords: ['AI', 'automation', 'tools', '2025'],
          source: 'youtube',
          category: 'technology',
          popularity: 95,
          growth_rate: 23.5,
          volume: 1250000,
          sentiment: 'positive',
          region: 'global',
          collected_at: new Date().toISOString(),
          description: 'Latest AI automation tools trending for business productivity'
        },
        {
          id: 2,
          topic: 'Sustainable Living Tips',
          keywords: ['sustainable', 'eco-friendly', 'green living'],
          source: 'google',
          category: 'lifestyle',
          popularity: 87,
          growth_rate: 18.2,
          volume: 890000,
          sentiment: 'positive',
          region: 'global',
          collected_at: new Date().toISOString(),
          description: 'Eco-friendly lifestyle trends and sustainable practices'
        },
        {
          id: 3,
          topic: 'Crypto Market Analysis',
          keywords: ['cryptocurrency', 'bitcoin', 'market', 'analysis'],
          source: 'twitter',
          category: 'finance',
          popularity: 92,
          growth_rate: -5.3,
          volume: 2100000,
          sentiment: 'mixed',
          region: 'global',
          collected_at: new Date().toISOString(),
          description: 'Current cryptocurrency market trends and analysis'
        },
        {
          id: 4,
          topic: 'Home Workout Routines',
          keywords: ['fitness', 'home workout', 'exercise'],
          source: 'youtube',
          category: 'health',
          popularity: 78,
          growth_rate: 12.8,
          volume: 650000,
          sentiment: 'positive',
          region: 'global',
          collected_at: new Date().toISOString(),
          description: 'Popular home fitness and workout content'
        },
        {
          id: 5,
          topic: 'Thai Street Food',
          keywords: ['thai food', 'street food', 'cooking'],
          source: 'youtube',
          category: 'food',
          popularity: 85,
          growth_rate: 28.7,
          volume: 420000,
          sentiment: 'positive',
          region: 'thailand',
          collected_at: new Date().toISOString(),
          description: 'Traditional Thai street food recipes and culture'
        },
        {
          id: 6,
          topic: 'Remote Work Productivity',
          keywords: ['remote work', 'productivity', 'work from home'],
          source: 'reddit',
          category: 'business',
          popularity: 82,
          growth_rate: 15.4,
          volume: 380000,
          sentiment: 'positive',
          region: 'global',
          collected_at: new Date().toISOString(),
          description: 'Tips and tools for remote work efficiency'
        }
      ];
      
      setTrends(mockTrends);
      toast.success('Trends updated successfully!');
    } catch (error) {
      toast.error('Failed to load trends');
    } finally {
      setLoading(false);
    }
  };

  const getSourceIcon = (source) => {
    switch (source) {
      case 'youtube': return <YouTube sx={{ color: '#FF0000' }} />;
      case 'twitter': return <Twitter sx={{ color: '#1DA1F2' }} />;
      case 'reddit': return <Reddit sx={{ color: '#FF4500' }} />;
      case 'google': return <Google sx={{ color: '#4285F4' }} />;
      default: return <TrendingUp />;
    }
  };

  const getGrowthIcon = (growth_rate) => {
    return growth_rate > 0 ? 
      <TrendingUp sx={{ color: '#10B981' }} /> : 
      <TrendingDown sx={{ color: '#EF4444' }} />;
  };

  const getSentimentColor = (sentiment) => {
    switch (sentiment) {
      case 'positive': return '#10B981';
      case 'negative': return '#EF4444';
      case 'mixed': return '#F59E0B';
      default: return '#6B7280';
    }
  };

  const filteredTrends = trends.filter(trend => {
    const matchesSearch = trend.topic.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         trend.keywords.some(k => k.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesSource = sourceFilter === 'all' || trend.source === sourceFilter;
    const matchesCategory = categoryFilter === 'all' || trend.category === categoryFilter;
    
    return matchesSearch && matchesSource && matchesCategory;
  }).sort((a, b) => {
    switch (sortBy) {
      case 'popularity': return b.popularity - a.popularity;
      case 'growth': return b.growth_rate - a.growth_rate;
      case 'volume': return b.volume - a.volume;
      case 'recent': return new Date(b.collected_at) - new Date(a.collected_at);
      default: return 0;
    }
  });

  const createOpportunityFromTrends = () => {
    if (selectedTrends.length === 0) {
      toast.error('Please select at least one trend');
      return;
    }
    
    toast.success(`Creating ${selectedTrends.length} content opportunities...`);
    setDialogOpen(false);
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 600, mb: 1 }}>
            Live Trends Monitor
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Real-time trend analysis across multiple platforms
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant={autoRefresh ? 'contained' : 'outlined'}
            startIcon={autoRefresh ? <Pause /> : <PlayArrow />}
            onClick={() => setAutoRefresh(!autoRefresh)}
            sx={{ bgcolor: autoRefresh ? '#10B981' : 'transparent' }}
          >
            {autoRefresh ? 'Auto Refresh ON' : 'Auto Refresh OFF'}
          </Button>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={loadTrends}
            disabled={loading}
          >
            Refresh Now
          </Button>
        </Box>
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 3, background: 'linear-gradient(135deg, #1E293B 0%, #334155 100%)', border: '1px solid #334155' }}>
        <CardContent>
          <Grid container spacing={3} alignItems="center">
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                placeholder="Search trends..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Search />
                    </InputAdornment>
                  ),
                }}
                sx={{ '& .MuiOutlinedInput-root': { bgcolor: '#0F172A' } }}
              />
            </Grid>
            <Grid item xs={12} md={2}>
              <FormControl fullWidth>
                <InputLabel>Source</InputLabel>
                <Select
                  value={sourceFilter}
                  onChange={(e) => setSourceFilter(e.target.value)}
                  sx={{ bgcolor: '#0F172A' }}
                >
                  <MenuItem value="all">All Sources</MenuItem>
                  <MenuItem value="youtube">YouTube</MenuItem>
                  <MenuItem value="google">Google</MenuItem>
                  <MenuItem value="twitter">Twitter</MenuItem>
                  <MenuItem value="reddit">Reddit</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={2}>
              <FormControl fullWidth>
                <InputLabel>Category</InputLabel>
                <Select
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                  sx={{ bgcolor: '#0F172A' }}
                >
                  <MenuItem value="all">All Categories</MenuItem>
                  <MenuItem value="technology">Technology</MenuItem>
                  <MenuItem value="lifestyle">Lifestyle</MenuItem>
                  <MenuItem value="finance">Finance</MenuItem>
                  <MenuItem value="health">Health</MenuItem>
                  <MenuItem value="food">Food</MenuItem>
                  <MenuItem value="business">Business</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={2}>
              <FormControl fullWidth>
                <InputLabel>Sort By</InputLabel>
                <Select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  sx={{ bgcolor: '#0F172A' }}
                >
                  <MenuItem value="popularity">Popularity</MenuItem>
                  <MenuItem value="growth">Growth Rate</MenuItem>
                  <MenuItem value="volume">Search Volume</MenuItem>
                  <MenuItem value="recent">Most Recent</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={2}>
              <Button
                fullWidth
                variant="contained"
                startIcon={<FilterList />}
                sx={{ bgcolor: '#3B82F6', height: 56 }}
              >
                Apply Filters
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {loading && <LinearProgress sx={{ mb: 3 }} />}

      {/* Selected Trends Summary */}
      {selectedTrends.length > 0 && (
        <Card sx={{ mb: 3, bgcolor: '#10B98110', border: '1px solid #10B981' }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="h6" sx={{ color: '#10B981' }}>
                {selectedTrends.length} trends selected for content creation
              </Typography>
              <Button
                variant="contained"
                startIcon={<AutoAwesome />}
                onClick={() => setDialogOpen(true)}
                sx={{ bgcolor: '#10B981', '&:hover': { bgcolor: '#059669' } }}
              >
                Generate Content Ideas
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Trends Grid */}
      <Grid container spacing={3}>
        <AnimatePresence>
          {filteredTrends.map((trend, index) => (
            <Grid item xs={12} md={6} lg={4} key={trend.id}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ delay: index * 0.05 }}
              >
                <Card
                  sx={{
                    background: selectedTrends.includes(trend.id) 
                      ? 'linear-gradient(135deg, #10B98120 0%, #059669 20 100%)'
                      : 'linear-gradient(135deg, #1E293B 0%, #334155 100%)',
                    border: selectedTrends.includes(trend.id) 
                      ? '2px solid #10B981' 
                      : '1px solid #334155',
                    cursor: 'pointer',
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: '0 12px 24px rgba(0,0,0,0.3)'
                    }
                  }}
                  onClick={() => toggleTrendSelection(trend.id)}
                >
                  <CardContent>
                    {/* Header */}
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {getSourceIcon(trend.source)}
                        <Chip 
                          label={trend.source.toUpperCase()} 
                          size="small"
                          sx={{ 
                            bgcolor: '#334155',
                            color: '#F1F5F9',
                            fontWeight: 600
                          }}
                        />
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {getGrowthIcon(trend.growth_rate)}
                        <Typography 
                          variant="body2" 
                          sx={{ 
                            color: trend.growth_rate > 0 ? '#10B981' : '#EF4444',
                            fontWeight: 600 
                          }}
                        >
                          {trend.growth_rate > 0 ? '+' : ''}{trend.growth_rate.toFixed(1)}%
                        </Typography>
                      </Box>
                    </Box>

                    {/* Topic */}
                    <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                      {trend.topic}
                    </Typography>
                    
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {trend.description}
                    </Typography>

                    {/* Keywords */}
                    <Box sx={{ mb: 2 }}>
                      {trend.keywords.slice(0, 3).map((keyword, idx) => (
                        <Chip
                          key={idx}
                          label={keyword}
                          size="small"
                          sx={{
                            mr: 0.5,
                            mb: 0.5,
                            bgcolor: '#0F172A',
                            color: '#CBD5E1'
                          }}
                        />
                      ))}
                      {trend.keywords.length > 3 && (
                        <Chip
                          label={`+${trend.keywords.length - 3} more`}
                          size="small"
                          sx={{
                            bgcolor: '#3B82F6',
                            color: 'white'
                          }}
                        />
                      )}
                    </Box>

                    {/* Metrics */}
                    <Grid container spacing={2}>
                      <Grid item xs={6}>
                        <Box>
                          <Typography variant="caption" color="text.secondary">
                            Popularity
                          </Typography>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <LinearProgress
                              variant="determinate"
                              value={trend.popularity}
                              sx={{
                                flex: 1,
                                height: 6,
                                borderRadius: 3,
                                '& .MuiLinearProgress-bar': {
                                  bgcolor: trend.popularity > 80 ? '#10B981' : 
                                          trend.popularity > 60 ? '#F59E0B' : '#EF4444'
                                }
                              }}
                            />
                            <Typography variant="caption" sx={{ fontWeight: 600 }}>
                              {trend.popularity}
                            </Typography>
                          </Box>
                        </Box>
                      </Grid>
                      <Grid item xs={6}>
                        <Box>
                          <Typography variant="caption" color="text.secondary">
                            Search Volume
                          </Typography>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            {(trend.volume / 1000).toFixed(0)}K
                          </Typography>
                        </Box>
                      </Grid>
                    </Grid>

                    {/* Footer */}
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Avatar
                          sx={{
                            bgcolor: getSentimentColor(trend.sentiment),
                            width: 20,
                            height: 20
                          }}
                        >
                          <WhatshotRounded fontSize="small" />
                        </Avatar>
                        <Typography variant="caption" sx={{ textTransform: 'capitalize' }}>
                          {trend.sentiment}
                        </Typography>
                      </Box>
                      <Typography variant="caption" color="text.secondary">
                        {new Date(trend.collected_at).toLocaleTimeString()}
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              </motion.div>
            </Grid>
          ))}
        </AnimatePresence>
      </Grid>

      {/* Empty State */}
      {filteredTrends.length === 0 && !loading && (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No trends found
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Try adjusting your filters or search terms
          </Typography>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={loadTrends}
          >
            Refresh Trends
          </Button>
        </Box>
      )}

      {/* Floating Action Button */}
      <Fab
        color="primary"
        sx={{
          position: 'fixed',
          bottom: 24,
          right: 24,
          bgcolor: '#10B981',
          '&:hover': { bgcolor: '#059669' }
        }}
        onClick={() => setDialogOpen(true)}
        disabled={selectedTrends.length === 0}
      >
        <AutoAwesome />
      </Fab>

      {/* Content Generation Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            bgcolor: '#1E293B',
            border: '1px solid #334155'
          }
        }}
      >
        <DialogTitle>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Generate Content Opportunities
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Create content ideas from {selectedTrends.length} selected trends
          </Typography>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ py: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Selected Trends:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 3 }}>
              {selectedTrends.map(trendId => {
                const trend = trends.find(t => t.id === trendId);
                return trend ? (
                  <Chip
                    key={trendId}
                    label={trend.topic}
                    onDelete={() => toggleTrendSelection(trendId)}
                    sx={{ bgcolor: '#334155' }}
                  />
                ) : null;
              })}
            </Box>

            <Typography variant="subtitle2" gutterBottom>
              Content Generation Options:
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <Card sx={{ bgcolor: '#0F172A', cursor: 'pointer', '&:hover': { bgcolor: '#1E293B' } }}>
                  <CardContent>
                    <Typography variant="subtitle2" gutterBottom>
                      Quick Content Ideas
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Generate basic content angles and titles
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Card sx={{ bgcolor: '#0F172A', cursor: 'pointer', '&:hover': { bgcolor: '#1E293B' } }}>
                  <CardContent>
                    <Typography variant="subtitle2" gutterBottom>
                      Advanced Analysis
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Deep trend analysis with competition research
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>
            Cancel
          </Button>
          <Button 
            variant="contained" 
            onClick={createOpportunityFromTrends}
            startIcon={<AutoAwesome />}
            sx={{ bgcolor: '#10B981', '&:hover': { bgcolor: '#059669' } }}
          >
            Generate Opportunities
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Trends;