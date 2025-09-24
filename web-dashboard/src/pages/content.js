import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  Button,
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
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Tabs,
  Tab,
  Badge,
  Fab,
  Divider
} from '@mui/material';
import {
  VideoLibrary,
  AutoAwesome,
  Schedule,
  Upload,
  Edit,
  Delete,
  PlayArrow,
  Pause,
  CheckCircle,
  Error,
  Pending,
  CloudUpload,
  Visibility,
  Download,
  Share,
  Add,
  SmartDisplay,
  AudioFile,
  Image,
  Description,
  Settings,
  Timer
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { useAppStore } from '../store/appStore';
import toast from 'react-hot-toast';

const Content = () => {
  const { 
    contentQueue, 
    updateContentStatus,
    loading, 
    setLoading,
    user 
  } = useAppStore();
  
  const [tabValue, setTabValue] = useState(0);
  const [createDialog, setCreateDialog] = useState(false);
  const [viewDialog, setViewDialog] = useState(false);
  const [selectedContent, setSelectedContent] = useState(null);
  const [newContent, setNewContent] = useState({
    title: '',
    type: 'educational',
    platforms: [],
    priority: 'medium'
  });

  const contentSteps = [
    'Script Generation',
    'Visual Creation',
    'Audio Production',
    'Video Assembly',
    'Quality Review',
    'Platform Upload'
  ];

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return '#10B981';
      case 'processing': return '#F59E0B';
      case 'failed': return '#EF4444';
      case 'queued': return '#6B7280';
      case 'uploading': return '#3B82F6';
      default: return '#6B7280';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <CheckCircle sx={{ color: '#10B981' }} />;
      case 'processing': return <AutoAwesome sx={{ color: '#F59E0B' }} />;
      case 'failed': return <Error sx={{ color: '#EF4444' }} />;
      case 'queued': return <Pending sx={{ color: '#6B7280' }} />;
      case 'uploading': return <CloudUpload sx={{ color: '#3B82F6' }} />;
      default: return <Pending />;
    }
  };

  const getPlatformIcon = (platform) => {
    const icons = {
      youtube: '🎥',
      tiktok: '🎵',
      instagram: '📸',
      facebook: '👥'
    };
    return icons[platform] || '📱';
  };

  const mockContentQueue = [
    {
      id: 1,
      title: 'AI Automation Tutorial Series - Episode 1',
      type: 'educational',
      status: 'processing',
      progress: 65,
      platforms: ['youtube', 'tiktok'],
      estimatedTime: 120,
      elapsedTime: 78,
      currentStep: 2,
      priority: 'high',
      createdAt: new Date(Date.now() - 3600000).toISOString(),
      assets: {
        script: 'completed',
        visuals: 'processing',
        audio: 'queued',
        video: 'queued'
      },
      metrics: {
        scriptWords: 1250,
        visualsGenerated: 8,
        audioLength: 0,
        estimatedViews: 125000
      }
    },
    {
      id: 2,
      title: 'Thai Street Food Secrets - Pad Thai',
      type: 'entertainment',
      status: 'completed',
      progress: 100,
      platforms: ['youtube', 'facebook'],
      estimatedTime: 180,
      elapsedTime: 175,
      currentStep: 5,
      priority: 'medium',
      createdAt: new Date(Date.now() - 7200000).toISOString(),
      assets: {
        script: 'completed',
        visuals: 'completed',
        audio: 'completed',
        video: 'completed'
      },
      metrics: {
        scriptWords: 980,
        visualsGenerated: 12,
        audioLength: 420,
        estimatedViews: 95000
      }
    },
    {
      id: 3,
      title: 'Sustainable Living Challenge - Week 1',
      type: 'lifestyle',
      status: 'queued',
      progress: 0,
      platforms: ['instagram', 'tiktok'],
      estimatedTime: 90,
      elapsedTime: 0,
      currentStep: 0,
      priority: 'low',
      createdAt: new Date().toISOString(),
      assets: {
        script: 'queued',
        visuals: 'queued',
        audio: 'queued',
        video: 'queued'
      },
      metrics: {
        scriptWords: 0,
        visualsGenerated: 0,
        audioLength: 0,
        estimatedViews: 89000
      }
    }
  ];

  const handleCreateContent = () => {
    if (!newContent.title.trim()) {
      toast.error('Please enter a content title');
      return;
    }
    
    const contentItem = {
      id: Date.now(),
      ...newContent,
      status: 'queued',
      progress: 0,
      currentStep: 0,
      createdAt: new Date().toISOString(),
      estimatedTime: 120,
      elapsedTime: 0,
      assets: {
        script: 'queued',
        visuals: 'queued',
        audio: 'queued',
        video: 'queued'
      },
      metrics: {
        scriptWords: 0,
        visualsGenerated: 0,
        audioLength: 0,
        estimatedViews: 0
      }
    };
    
    toast.success('Content added to production queue!');
    setCreateDialog(false);
    setNewContent({ title: '', type: 'educational', platforms: [], priority: 'medium' });
  };

  const handleStartProduction = (contentId) => {
    updateContentStatus(contentId, 'processing');
    toast.success('Content production started!');
  };

  const handlePauseProduction = (contentId) => {
    updateContentStatus(contentId, 'queued');
    toast.info('Content production paused');
  };

  const filteredContent = mockContentQueue.filter(content => {
    if (tabValue === 0) return true; // All
    if (tabValue === 1) return content.status === 'processing'; // In Progress
    if (tabValue === 2) return content.status === 'completed'; // Completed
    if (tabValue === 3) return content.status === 'queued'; // Queue
    return true;
  });

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 600, mb: 1 }}>
            Content Studio
          </Typography>
          <Typography variant="body1" color="text.secondary">
            AI-powered content production pipeline
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Chip
            label={`${user.tier} Plan`}
            sx={{ 
              bgcolor: '#3B82F6',
              color: 'white',
              fontWeight: 600
            }}
          />
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => setCreateDialog(true)}
            sx={{ bgcolor: '#10B981', '&:hover': { bgcolor: '#059669' } }}
          >
            Create Content
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
                <VideoLibrary />
                All Content
                <Badge badgeContent={mockContentQueue.length} color="primary" />
              </Box>
            } 
          />
          <Tab 
            label={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <AutoAwesome />
                In Progress
                <Badge badgeContent={mockContentQueue.filter(c => c.status === 'processing').length} color="warning" />
              </Box>
            } 
          />
          <Tab 
            label={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CheckCircle />
                Completed
                <Badge badgeContent={mockContentQueue.filter(c => c.status === 'completed').length} color="success" />
              </Box>
            } 
          />
          <Tab 
            label={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Schedule />
                Queue
                <Badge badgeContent={mockContentQueue.filter(c => c.status === 'queued').length} color="default" />
              </Box>
            } 
          />
        </Tabs>
      </Card>

      {/* Content Grid */}
      <Grid container spacing={3}>
        <AnimatePresence>
          {filteredContent.map((content, index) => (
            <Grid item xs={12} key={content.id}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ delay: index * 0.05 }}
              >
                <Card
                  sx={{
                    background: 'linear-gradient(135deg, #1E293B 0%, #334155 100%)',
                    border: `1px solid ${getStatusColor(content.status)}20`,
                    borderLeft: `4px solid ${getStatusColor(content.status)}`,
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      transform: 'translateY(-2px)',
                      boxShadow: '0 8px 24px rgba(0,0,0,0.2)'
                    }
                  }}
                >
                  <CardContent>
                    <Grid container spacing={3}>
                      {/* Main Info */}
                      <Grid item xs={12} md={6}>
                        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2, mb: 2 }}>
                          <Avatar sx={{ bgcolor: getStatusColor(content.status) }}>
                            {getStatusIcon(content.status)}
                          </Avatar>
                          <Box sx={{ flex: 1 }}>
                            <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                              {content.title}
                            </Typography>
                            <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                              <Chip 
                                label={content.type} 
                                size="small" 
                                sx={{ 
                                  bgcolor: '#334155',
                                  textTransform: 'capitalize'
                                }} 
                              />
                              <Chip 
                                label={`${content.priority} priority`} 
                                size="small" 
                                sx={{ 
                                  bgcolor: content.priority === 'high' ? '#EF444420' :
                                          content.priority === 'medium' ? '#F59E0B20' : '#10B98120',
                                  color: content.priority === 'high' ? '#EF4444' :
                                         content.priority === 'medium' ? '#F59E0B' : '#10B981'
                                }} 
                              />
                            </Box>
                            <Box sx={{ display: 'flex', gap: 0.5 }}>
                              {content.platforms.map(platform => (
                                <Chip
                                  key={platform}
                                  label={`${getPlatformIcon(platform)} ${platform}`}
                                  size="small"
                                  sx={{ bgcolor: '#0F172A', fontSize: '0.75rem' }}
                                />
                              ))}
                            </Box>
                          </Box>
                        </Box>

                        {/* Progress Bar */}
                        <Box sx={{ mb: 2 }}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                            <Typography variant="body2" color="text.secondary">
                              Progress
                            </Typography>
                            <Typography variant="body2" sx={{ fontWeight: 600 }}>
                              {content.progress}%
                            </Typography>
                          </Box>
                          <LinearProgress
                            variant="determinate"
                            value={content.progress}
                            sx={{
                              height: 8,
                              borderRadius: 4,
                              bgcolor: '#334155',
                              '& .MuiLinearProgress-bar': {
                                bgcolor: getStatusColor(content.status),
                                borderRadius: 4
                              }
                            }}
                          />
                        </Box>

                        {/* Time Info */}
                        <Grid container spacing={2}>
                          <Grid item xs={6}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Timer fontSize="small" color="action" />
                              <Box>
                                <Typography variant="caption" color="text.secondary">
                                  Time Elapsed
                                </Typography>
                                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                                  {content.elapsedTime}m / {content.estimatedTime}m
                                </Typography>
                              </Box>
                            </Box>
                          </Grid>
                          <Grid item xs={6}>
                            <Box>
                              <Typography variant="caption" color="text.secondary">
                                Created
                              </Typography>
                              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                                {new Date(content.createdAt).toLocaleString()}
                              </Typography>
                            </Box>
                          </Grid>
                        </Grid>
                      </Grid>

                      {/* Production Steps */}
                      <Grid item xs={12} md={3}>
                        <Typography variant="subtitle2" gutterBottom>
                          Production Pipeline
                        </Typography>
                        <Box sx={{ bgcolor: '#0F172A', p: 2, borderRadius: 2 }}>
                          {contentSteps.map((step, stepIndex) => (
                            <Box 
                              key={step} 
                              sx={{ 
                                display: 'flex', 
                                alignItems: 'center', 
                                gap: 1, 
                                mb: stepIndex < contentSteps.length - 1 ? 1 : 0,
                                opacity: stepIndex <= content.currentStep ? 1 : 0.5
                              }}
                            >
                              <Avatar 
                                sx={{ 
                                  width: 20, 
                                  height: 20, 
                                  fontSize: '0.75rem',
                                  bgcolor: stepIndex < content.currentStep ? '#10B981' :
                                          stepIndex === content.currentStep ? '#F59E0B' : '#6B7280'
                                }}
                              >
                                {stepIndex < content.currentStep ? '✓' : stepIndex + 1}
                              </Avatar>
                              <Typography variant="caption">
                                {step}
                              </Typography>
                            </Box>
                          ))}
                        </Box>
                      </Grid>

                      {/* Assets Status */}
                      <Grid item xs={12} md={3}>
                        <Typography variant="subtitle2" gutterBottom>
                          Asset Status
                        </Typography>
                        <Grid container spacing={1}>
                          <Grid item xs={6}>
                            <Card sx={{ bgcolor: '#0F172A', textAlign: 'center', p: 1 }}>
                              <Description 
                                sx={{ 
                                  color: content.assets.script === 'completed' ? '#10B981' : 
                                        content.assets.script === 'processing' ? '#F59E0B' : '#6B7280'
                                }} 
                              />
                              <Typography variant="caption" display="block">
                                Script
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {content.metrics.scriptWords} words
                              </Typography>
                            </Card>
                          </Grid>
                          <Grid item xs={6}>
                            <Card sx={{ bgcolor: '#0F172A', textAlign: 'center', p: 1 }}>
                              <Image 
                                sx={{ 
                                  color: content.assets.visuals === 'completed' ? '#10B981' : 
                                        content.assets.visuals === 'processing' ? '#F59E0B' : '#6B7280'
                                }} 
                              />
                              <Typography variant="caption" display="block">
                                Visuals
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {content.metrics.visualsGenerated} images
                              </Typography>
                            </Card>
                          </Grid>
                          <Grid item xs={6}>
                            <Card sx={{ bgcolor: '#0F172A', textAlign: 'center', p: 1 }}>
                              <AudioFile 
                                sx={{ 
                                  color: content.assets.audio === 'completed' ? '#10B981' : 
                                        content.assets.audio === 'processing' ? '#F59E0B' : '#6B7280'
                                }} 
                              />
                              <Typography variant="caption" display="block">
                                Audio
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {content.metrics.audioLength}s
                              </Typography>
                            </Card>
                          </Grid>
                          <Grid item xs={6}>
                            <Card sx={{ bgcolor: '#0F172A', textAlign: 'center', p: 1 }}>
                              <SmartDisplay 
                                sx={{ 
                                  color: content.assets.video === 'completed' ? '#10B981' : 
                                        content.assets.video === 'processing' ? '#F59E0B' : '#6B7280'
                                }} 
                              />
                              <Typography variant="caption" display="block">
                                Video
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                Final
                              </Typography>
                            </Card>
                          </Grid>
                        </Grid>
                      </Grid>
                    </Grid>

                    <Divider sx={{ my: 2, borderColor: '#334155' }} />

                    {/* Action Buttons */}
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        {content.status === 'queued' && (
                          <Button
                            variant="contained"
                            startIcon={<PlayArrow />}
                            onClick={() => handleStartProduction(content.id)}
                            sx={{ bgcolor: '#10B981', '&:hover': { bgcolor: '#059669' } }}
                          >
                            Start Production
                          </Button>
                        )}
                        {content.status === 'processing' && (
                          <Button
                            variant="outlined"
                            startIcon={<Pause />}
                            onClick={() => handlePauseProduction(content.id)}
                          >
                            Pause
                          </Button>
                        )}
                        {content.status === 'completed' && (
                          <>
                            <Button
                              variant="contained"
                              startIcon={<Upload />}
                              sx={{ bgcolor: '#3B82F6', '&:hover': { bgcolor: '#1D4ED8' } }}
                            >
                              Upload to Platforms
                            </Button>
                            <Button
                              variant="outlined"
                              startIcon={<Download />}
                            >
                              Download
                            </Button>
                          </>
                        )}
                      </Box>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <IconButton 
                          onClick={() => {
                            setSelectedContent(content);
                            setViewDialog(true);
                          }}
                        >
                          <Visibility />
                        </IconButton>
                        <IconButton>
                          <Edit />
                        </IconButton>
                        <IconButton sx={{ color: '#EF4444' }}>
                          <Delete />
                        </IconButton>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </motion.div>
            </Grid>
          ))}
        </AnimatePresence>
      </Grid>

      {/* Empty State */}
      {filteredContent.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <VideoLibrary sx={{ fontSize: 64, color: '#6B7280', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No content in this category
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Create your first AI-generated content piece
          </Typography>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => setCreateDialog(true)}
            sx={{ bgcolor: '#10B981', '&:hover': { bgcolor: '#059669' } }}
          >
            Create Content
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
        onClick={() => setCreateDialog(true)}
      >
        <Add />
      </Fab>

      {/* Create Content Dialog */}
      <Dialog
        open={createDialog}
        onClose={() => setCreateDialog(false)}
        maxWidth="sm"
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
            Create New Content
          </Typography>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ py: 2 }}>
            <TextField
              fullWidth
              label="Content Title"
              value={newContent.title}
              onChange={(e) => setNewContent({ ...newContent, title: e.target.value })}
              sx={{ mb: 3 }}
            />
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Content Type</InputLabel>
                  <Select
                    value={newContent.type}
                    onChange={(e) => setNewContent({ ...newContent, type: e.target.value })}
                  >
                    <MenuItem value="educational">Educational</MenuItem>
                    <MenuItem value="entertainment">Entertainment</MenuItem>
                    <MenuItem value="lifestyle">Lifestyle</MenuItem>
                    <MenuItem value="news">News</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Priority</InputLabel>
                  <Select
                    value={newContent.priority}
                    onChange={(e) => setNewContent({ ...newContent, priority: e.target.value })}
                  >
                    <MenuItem value="low">Low</MenuItem>
                    <MenuItem value="medium">Medium</MenuItem>
                    <MenuItem value="high">High</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialog(false)}>
            Cancel
          </Button>
          <Button 
            variant="contained" 
            onClick={handleCreateContent}
            sx={{ bgcolor: '#10B981', '&:hover': { bgcolor: '#059669' } }}
          >
            Create Content
          </Button>
        </DialogActions>
      </Dialog>

      {/* View Content Dialog */}
      <Dialog
        open={viewDialog}
        onClose={() => setViewDialog(false)}
        maxWidth="lg"
        fullWidth
        PaperProps={{
          sx: {
            bgcolor: '#1E293B',
            border: '1px solid #334155'
          }
        }}
      >
        {selectedContent && (
          <>
            <DialogTitle>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {selectedContent.title}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Content Details & Preview
              </Typography>
            </DialogTitle>
            <DialogContent>
              <Box sx={{ py: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Production Timeline
                </Typography>
                <Stepper activeStep={selectedContent.currentStep} orientation="vertical">
                  {contentSteps.map((step, index) => (
                    <Step key={step}>
                      <StepLabel>{step}</StepLabel>
                      <StepContent>
                        <Typography variant="body2" color="text.secondary">
                          {index < selectedContent.currentStep ? 'Completed' :
                           index === selectedContent.currentStep ? 'In Progress' : 'Pending'}
                        </Typography>
                      </StepContent>
                    </Step>
                  ))}
                </Stepper>
              </Box>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setViewDialog(false)}>
                Close
              </Button>
              <Button 
                variant="contained"
                startIcon={<Settings />}
              >
                Edit Settings
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Box>
  );
};

export default Content;