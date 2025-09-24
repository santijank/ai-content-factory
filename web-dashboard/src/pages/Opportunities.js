import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  Button,
  Rating,
  LinearProgress,
  Avatar,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Tabs,
  Tab,
  Badge
} from '@mui/material';
import {
  Lightbulb,
  TrendingUp,
  AttachMoney,
  Schedule,
  Visibility,
  ThumbUp,
  Share,
  PlayArrow,
  Edit,
  Delete,
  Star,
  StarBorder,
  FilterList,
  Sort,
  AutoAwesome,
  VideoLibrary,
  PsychologyAlt,
  BusinessCenter,
  LocalFireDepartment
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { useAppStore } from '../store/appStore';
import toast from 'react-hot-toast';

const Opportunities = () => {
  const { 
    opportunities, 
    setOpportunities, 
    selectedOpportunities, 
    selectOpportunity,
    addToContentQueue,
    loading, 
    setLoading 
  } = useAppStore();
  
  const [tabValue, setTabValue] = useState(0);
  const [detailDialog, setDetailDialog] = useState(false);
  const [selectedOpportunity, setSelectedOpportunity] = useState(null);
  const [sortBy, setSortBy] = useState('roi');
  const [filterBy, setFilterBy] = useState('all');

  useEffect(() => {
    loadOpportunities();
  }, []);

  const loadOpportunities = async () => {
    setLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const mockOpportunities = [
        {
          id: 1,
          title: 'AI Automation Tutorial Series',
          trend_topic: 'AI Automation Tools 2025',
          suggested_angle: 'Step-by-step AI tool implementation for small businesses',
          content_type: 'educational',
          estimated_views: 125000,
          estimated_revenue: 2850,
          competition_level: 'medium',
          production_cost: 450,
          estimated_roi: 6.3,
          priority_score: 9.2,
          difficulty: 'medium',
          platforms: ['youtube', 'tiktok'],
          target_audience: 'entrepreneurs',
          content_pillars: ['tutorial', 'business', 'ai'],
          estimated_production_time: 120,
          viral_potential: 8.5,
          monetization_score: 9.1,
          created_at: new Date().toISOString(),
          status: 'pending',
          thumbnail_concept: 'Split screen showing manual vs AI-automated workflow',
          script_outline: [
            'Hook: Show 8-hour manual task vs 30-minute AI solution',
            'Problem: Small business overwhelmed by repetitive tasks',
            'Solution: Top 5 AI automation tools demonstration',
            'Implementation: Step-by-step setup guide',
            'Results: Real business case study with ROI numbers',
            'CTA: Free automation checklist download'
          ]
        },
        {
          id: 2,
          title: 'Sustainable Living Challenge',
          trend_topic: 'Sustainable Living Tips',
          suggested_angle: '30-day sustainable living transformation journey',
          content_type: 'lifestyle',
          estimated_views: 89000,
          estimated_revenue: 1650,
          competition_level: 'high',
          production_cost: 320,
          estimated_roi: 5.2,
          priority_score: 8.7,
          difficulty: 'easy',
          platforms: ['instagram', 'youtube'],
          target_audience: 'millennials',
          content_pillars: ['lifestyle', 'environment', 'challenge'],
          estimated_production_time: 90,
          viral_potential: 7.8,
          monetization_score: 6.2,
          created_at: new Date().toISOString(),
          status: 'pending',
          thumbnail_concept: 'Before/after lifestyle comparison with green elements',
          script_outline: [
            'Hook: Shocking environmental impact of daily habits',
            'Challenge: 30-day sustainable transformation',
            'Week 1: Home & Energy efficiency changes',
            'Week 2: Food & Shopping sustainable swaps',
            'Week 3: Transportation & Digital habits',
            'Week 4: Community impact & long-term commitment'
          ]
        },
        {
          id: 3,
          title: 'Crypto Trading Psychology',
          trend_topic: 'Crypto Market Analysis',
          suggested_angle: 'Understanding emotional trading mistakes and how to avoid them',
          content_type: 'educational',
          estimated_views: 156000,
          estimated_revenue: 3200,
          competition_level: 'high',
          production_cost: 280,
          estimated_roi: 11.4,
          priority_score: 9.5,
          difficulty: 'hard',
          platforms: ['youtube', 'tiktok'],
          target_audience: 'investors',
          content_pillars: ['finance', 'psychology', 'education'],
          estimated_production_time: 150,
          viral_potential: 9.2,
          monetization_score: 9.8,
          created_at: new Date().toISOString(),
          status: 'in_review',
          thumbnail_concept: 'Split brain showing emotional vs logical trading decisions',
          script_outline: [
            'Hook: $50K loss due to emotional trading mistake',
            'Problem: Why 95% of crypto traders lose money',
            'Psychology: Fear, greed, and FOMO explained',
            'Solutions: 5 psychological frameworks for better decisions',
            'Tools: Apps and techniques for emotional control',
            'Success: Testimonials from profitable traders'
          ]
        },
        {
          id: 4,
          title: 'Thai Street Food Secrets',
          trend_topic: 'Thai Street Food',
          suggested_angle: 'Authentic Thai street vendor reveals secret recipes',
          content_type: 'entertainment',
          estimated_views: 95000,
          estimated_revenue: 1890,
          competition_level: 'low',
          production_cost: 380,
          estimated_roi: 5.0,
          priority_score: 8.3,
          difficulty: 'medium',
          platforms: ['youtube', 'facebook'],
          target_audience: 'food_lovers',
          content_pillars: ['cooking', 'culture', 'authentic'],
          estimated_production_time: 180,
          viral_potential: 8.1,
          monetization_score: 7.3,
          created_at: new Date().toISOString(),
          status: 'selected',
          thumbnail_concept: 'Street vendor cooking with steam and vibrant colors',
          script_outline: [
            'Hook: 40-year street vendor\'s secret ingredient',
            'Story: Family recipes passed down 3 generations',
            'Cooking: 3 signature dishes step-by-step',
            'Secrets: Techniques not found in restaurants',
            'Culture: Stories behind each dish\'s origin',
            'CTA: Try recipes and share results'
          ]
        }
      ];
      
      setOpportunities(mockOpportunities);
      toast.success('Opportunities loaded successfully!');
    } catch (error) {
      toast.error('Failed to load opportunities');
    } finally {
      setLoading(false);
    }
  };

  const getCompetitionColor = (level) => {
    switch (level) {
      case 'low': return '#10B981';
      case 'medium': return '#F59E0B';
      case 'high': return '#EF4444';
      default: return '#6B7280';
    }
  };

  const getDifficultyIcon = (difficulty) => {
    switch (difficulty) {
      case 'easy': return <Star sx={{ color: '#10B981' }} />;
      case 'medium': return <Star sx={{ color: '#F59E0B' }} />;
      case 'hard': return <Star sx={{ color: '#EF4444' }} />;
      default: return <StarBorder />;
    }
  };

  const getPlatformIcon = (platform) => {
    switch (platform) {
      case 'youtube': return '🎥';
      case 'tiktok': return '🎵';
      case 'instagram': return '📸';
      case 'facebook': return '👥';
      default: return '📱';
    }
  };

  const handleCreateContent = (opportunity) => {
    addToContentQueue({
      opportunityId: opportunity.id,
      title: opportunity.title,
      type: opportunity.content_type,
      platforms: opportunity.platforms,
      estimatedCost: opportunity.production_cost,
      estimatedTime: opportunity.estimated_production_time
    });
    
    toast.success(`"${opportunity.title}" added to content queue!`);
  };

  const filteredOpportunities = opportunities.filter(opp => {
    if (tabValue === 0) return true; // All
    if (tabValue === 1) return opp.priority_score >= 9; // High Priority
    if (tabValue === 2) return opp.estimated_roi >= 8; // High ROI
    if (tabValue === 3) return opp.competition_level === 'low'; // Low Competition
    return true;
  }).sort((a, b) => {
    switch (sortBy) {
      case 'roi': return b.estimated_roi - a.estimated_roi;
      case 'priority': return b.priority_score - a.priority_score;
      case 'views': return b.estimated_views - a.estimated_views;
      case 'revenue': return b.estimated_revenue - a.estimated_revenue;
      default: return 0;
    }
  });

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 600, mb: 1 }}>
            Content Opportunities
          </Typography>
          <Typography variant="body1" color="text.secondary">
            AI-generated content ideas based on trending topics
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Sort By</InputLabel>
            <Select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              sx={{ bgcolor: '#1E293B' }}
            >
              <MenuItem value="roi">ROI Score</MenuItem>
              <MenuItem value="priority">Priority</MenuItem>
              <MenuItem value="views">Est. Views</MenuItem>
              <MenuItem value="revenue">Est. Revenue</MenuItem>
            </Select>
          </FormControl>
          <Button
            variant="contained"
            startIcon={<AutoAwesome />}
            sx={{ bgcolor: '#3B82F6', '&:hover': { bgcolor: '#1D4ED8' } }}
          >
            Generate More
          </Button>
        </Box>
      </Box>

      {/* Tabs */}
      <Card sx={{ mb: 3, background: 'linear-gradient(135deg, #1E293B 0%, #334155 100%)', border: '1px solid #334155' }}>
        <Tabs 
          value={tabValue} 
          onChange={(e, newValue) => setTabValue(newValue)}
          sx={{ 
            '& .MuiTab-root': { color: '#CBD5E1' },
            '& .Mui-selected': { color: '#3B82F6' }
          }}
        >
          <Tab 
            label={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Lightbulb />
                All Opportunities
                <Badge badgeContent={opportunities.length} color="primary" />
              </Box>
            } 
          />
          <Tab 
            label={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <LocalFireDepartment />
                High Priority
                <Badge badgeContent={opportunities.filter(o => o.priority_score >= 9).length} color="error" />
              </Box>
            } 
          />
          <Tab 
            label={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <AttachMoney />
                High ROI
                <Badge badgeContent={opportunities.filter(o => o.estimated_roi >= 8).length} color="success" />
              </Box>
            } 
          />
          <Tab 
            label={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <TrendingUp />
                Low Competition
                <Badge badgeContent={opportunities.filter(o => o.competition_level === 'low').length} color="warning" />
              </Box>
            } 
          />
        </Tabs>
      </Card>

      {loading && <LinearProgress sx={{ mb: 3 }} />}

      {/* Opportunities Grid */}
      <Grid container spacing={3}>
        <AnimatePresence>
          {filteredOpportunities.map((opportunity, index) => (
            <Grid item xs={12} lg={6} key={opportunity.id}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ delay: index * 0.05 }}
              >
                <Card
                  sx={{
                    background: 'linear-gradient(135deg, #1E293B 0%, #334155 100%)',
                    border: '1px solid #334155',
                    height: '100%',
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: '0 12px 24px rgba(0,0,0,0.3)'
                    }
                  }}
                >
                  <CardContent>
                    {/* Header */}
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                          {opportunity.title}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                          Based on: <em>{opportunity.trend_topic}</em>
                        </Typography>
                        <Chip
                          label={opportunity.content_type}
                          size="small"
                          sx={{
                            bgcolor: opportunity.content_type === 'educational' ? '#3B82F6' :
                                    opportunity.content_type === 'entertainment' ? '#EC4899' : '#10B981',
                            color: 'white',
                            textTransform: 'capitalize'
                          }}
                        />
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {getDifficultyIcon(opportunity.difficulty)}
                        <IconButton 
                          size="small"
                          onClick={() => {
                            setSelectedOpportunity(opportunity);
                            setDetailDialog(true);
                          }}
                        >
                          <Visibility />
                        </IconButton>
                      </Box>
                    </Box>

                    {/* Content Angle */}
                    <Typography variant="body2" sx={{ mb: 3, fontStyle: 'italic' }}>
                      "{opportunity.suggested_angle}"
                    </Typography>

                    {/* Metrics */}
                    <Grid container spacing={2} sx={{ mb: 3 }}>
                      <Grid item xs={6}>
                        <Box>
                          <Typography variant="caption" color="text.secondary">
                            ROI Score
                          </Typography>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Rating 
                              value={opportunity.estimated_roi / 2} 
                              readOnly 
                              size="small"
                              max={5}
                            />
                            <Typography variant="body2" sx={{ fontWeight: 600, color: '#10B981' }}>
                              {opportunity.estimated_roi.toFixed(1)}x
                            </Typography>
                          </Box>
                        </Box>
                      </Grid>
                      <Grid item xs={6}>
                        <Box>
                          <Typography variant="caption" color="text.secondary">
                            Priority Score
                          </Typography>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <LinearProgress
                              variant="determinate"
                              value={opportunity.priority_score * 10}
                              sx={{
                                flex: 1,
                                height: 6,
                                borderRadius: 3,
                                '& .MuiLinearProgress-bar': {
                                  bgcolor: opportunity.priority_score >= 9 ? '#EF4444' :
                                          opportunity.priority_score >= 7 ? '#F59E0B' : '#10B981'
                                }
                              }}
                            />
                            <Typography variant="caption" sx={{ fontWeight: 600 }}>
                              {opportunity.priority_score}/10
                            </Typography>
                          </Box>
                        </Box>
                      </Grid>
                    </Grid>

                    {/* Stats Row */}
                    <Grid container spacing={2} sx={{ mb: 3 }}>
                      <Grid item xs={3}>
                        <Box sx={{ textAlign: 'center' }}>
                          <Typography variant="h6" sx={{ color: '#3B82F6' }}>
                            {(opportunity.estimated_views / 1000).toFixed(0)}K
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Est. Views
                          </Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={3}>
                        <Box sx={{ textAlign: 'center' }}>
                          <Typography variant="h6" sx={{ color: '#10B981' }}>
                            ฿{opportunity.estimated_revenue.toLocaleString()}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Revenue
                          </Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={3}>
                        <Box sx={{ textAlign: 'center' }}>
                          <Typography variant="h6" sx={{ color: '#F59E0B' }}>
                            ฿{opportunity.production_cost}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Cost
                          </Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={3}>
                        <Box sx={{ textAlign: 'center' }}>
                          <Typography variant="h6" sx={{ color: '#8B5CF6' }}>
                            {opportunity.estimated_production_time}m
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Time
                          </Typography>
                        </Box>
                      </Grid>
                    </Grid>

                    {/* Platforms & Competition */}
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                      <Box>
                        <Typography variant="caption" color="text.secondary" gutterBottom>
                          Platforms
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 0.5 }}>
                          {opportunity.platforms.map(platform => (
                            <Chip
                              key={platform}
                              label={`${getPlatformIcon(platform)} ${platform}`}
                              size="small"
                              sx={{ bgcolor: '#334155', fontSize: '0.75rem' }}
                            />
                          ))}
                        </Box>
                      </Box>
                      <Box>
                        <Typography variant="caption" color="text.secondary" gutterBottom>
                          Competition
                        </Typography>
                        <Chip
                          label={opportunity.competition_level}
                          size="small"
                          sx={{
                            bgcolor: getCompetitionColor(opportunity.competition_level),
                            color: 'white',
                            textTransform: 'capitalize',
                            fontWeight: 600
                          }}
                        />
                      </Box>
                    </Box>

                    {/* Action Buttons */}
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <Button
                        variant="contained"
                        startIcon={<VideoLibrary />}
                        onClick={() => handleCreateContent(opportunity)}
                        sx={{
                          flex: 1,
                          bgcolor: '#10B981',
                          '&:hover': { bgcolor: '#059669' }
                        }}
                      >
                        Create Content
                      </Button>
                      <IconButton
                        sx={{ border: '1px solid #334155' }}
                        onClick={() => {
                          setSelectedOpportunity(opportunity);
                          setDetailDialog(true);
                        }}
                      >
                        <Edit />
                      </IconButton>
                    </Box>
                  </CardContent>
                </Card>
              </motion.div>
            </Grid>
          ))}
        </AnimatePresence>
      </Grid>

      {/* Detail Dialog */}
      <Dialog
        open={detailDialog}
        onClose={() => setDetailDialog(false)}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            bgcolor: '#1E293B',
            border: '1px solid #334155'
          }
        }}
      >
        {selectedOpportunity && (
          <>
            <DialogTitle>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {selectedOpportunity.title}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Content Opportunity Details
              </Typography>
            </DialogTitle>
            <DialogContent>
              <Box sx={{ py: 2 }}>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" gutterBottom>
                      Script Outline:
                    </Typography>
                    <Box sx={{ bgcolor: '#0F172A', p: 2, borderRadius: 2, mb: 3 }}>
                      {selectedOpportunity.script_outline.map((point, idx) => (
                        <Typography key={idx} variant="body2" sx={{ mb: 1 }}>
                          {idx + 1}. {point}
                        </Typography>
                      ))}
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" gutterBottom>
                      Thumbnail Concept:
                    </Typography>
                    <Box sx={{ bgcolor: '#0F172A', p: 2, borderRadius: 2, mb: 3 }}>
                      <Typography variant="body2">
                        {selectedOpportunity.thumbnail_concept}
                      </Typography>
                    </Box>
                    
                    <Typography variant="subtitle2" gutterBottom>
                      Performance Predictions:
                    </Typography>
                    <Box sx={{ bgcolor: '#0F172A', p: 2, borderRadius: 2 }}>
                      <Grid container spacing={2}>
                        <Grid item xs={6}>
                          <Typography variant="caption" color="text.secondary">
                            Viral Potential
                          </Typography>
                          <Typography variant="h6" color="#EC4899">
                            {selectedOpportunity.viral_potential}/10
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="caption" color="text.secondary">
                            Monetization Score
                          </Typography>
                          <Typography variant="h6" color="#10B981">
                            {selectedOpportunity.monetization_score}/10
                          </Typography>
                        </Grid>
                      </Grid>
                    </Box>
                  </Grid>
                </Grid>
              </Box>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setDetailDialog(false)}>
                Close
              </Button>
              <Button
                variant="contained"
                startIcon={<VideoLibrary />}
                onClick={() => {
                  handleCreateContent(selectedOpportunity);
                  setDetailDialog(false);
                }}
                sx={{ bgcolor: '#10B981', '&:hover': { bgcolor: '#059669' } }}
              >
                Create Content
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Box>
  );
};

export default Opportunities;