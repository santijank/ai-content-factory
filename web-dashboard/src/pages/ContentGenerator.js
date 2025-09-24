import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  Alert,
  CircularProgress,
  Chip,
  Divider
} from '@mui/material';
import { AutoAwesome, PlayArrow } from '@mui/icons-material';
import toast from 'react-hot-toast';

const ContentGenerator = () => {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    idea: '',
    platform: 'youtube',
    content_type: 'educational'
  });
  const [generatedContent, setGeneratedContent] = useState(null);
  const [error, setError] = useState(null);

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    // Clear error when user starts typing
    if (error) setError(null);
  };

  const generateContent = async () => {
    // Validation
    if (!formData.idea.trim()) {
      setError('Please enter a content idea');
      toast.error('Content idea is required');
      return;
    }

    setLoading(true);
    setError(null);
    setGeneratedContent(null);

    try {
      console.log('🎬 Sending request to generate content...');
      console.log('Request data:', formData);

      const response = await fetch('/api/generate-content', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      });

      console.log('📡 Response status:', response.status);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('📝 Received data:', data);

      // Enhanced validation with detailed logging
      if (!data) {
        throw new Error('Empty response from server');
      }

      if (!data.success) {
        throw new Error(data.error || 'API returned unsuccessful response');
      }

      // Check content_plan existence with detailed logging
      if (!data.content_plan) {
        console.error('❌ Missing content_plan in response:', data);
        throw new Error('Invalid response: missing content_plan');
      }

      // Check required fields in content_plan
      const requiredFields = ['title', 'description', 'script'];
      const missingFields = requiredFields.filter(field => !data.content_plan[field]);
      
      if (missingFields.length > 0) {
        console.error('❌ Missing required fields:', missingFields);
        console.error('Available fields:', Object.keys(data.content_plan));
        
        // Auto-fix missing fields
        const fixedContentPlan = {
          title: data.content_plan.title || `${formData.idea} - Content`,
          description: data.content_plan.description || `Generated content about ${formData.idea}`,
          script: data.content_plan.script || {
            hook: `Introduction to ${formData.idea}`,
            main_content: `Main content about ${formData.idea}`,
            cta: 'Thanks for watching!'
          },
          ...data.content_plan
        };

        data.content_plan = fixedContentPlan;
        console.log('✅ Fixed content plan:', fixedContentPlan);
      }

      // Validate script structure
      if (!data.content_plan.script || typeof data.content_plan.script !== 'object') {
        console.warn('⚠️ Invalid script structure, creating default');
        data.content_plan.script = {
          hook: `Welcome! Today we're exploring ${formData.idea}`,
          main_content: `Let's dive deep into ${formData.idea} and discover the key insights you need to know.`,
          cta: 'Don\'t forget to like and subscribe for more content!'
        };
      }

      console.log('✅ Content generated successfully');
      setGeneratedContent(data.content_plan);
      toast.success('Content generated successfully!');

    } catch (error) {
      console.error('❌ Content generation failed:', error);
      
      const errorMessage = error.message || 'Failed to generate content';
      setError(errorMessage);
      toast.error(errorMessage);

      // Create fallback content for better UX
      const fallbackContent = {
        title: `${formData.idea} - Complete Guide`,
        description: `This is a comprehensive guide about ${formData.idea}. Learn everything you need to know in this detailed content.`,
        script: {
          hook: `Welcome! Today we're exploring ${formData.idea}`,
          main_content: `Let's dive into ${formData.idea}. Here are the key points: 1) Understanding the basics, 2) Advanced concepts, 3) Practical applications.`,
          cta: 'If you found this helpful, please like and subscribe!'
        },
        hashtags: [`#${formData.idea.replace(/\s+/g, '')}`, `#${formData.platform}`, '#content'],
        platform: formData.platform,
        estimated_duration: '5-10 minutes',
        fallback: true,
        error_reason: errorMessage
      };

      console.log('🔧 Using fallback content:', fallbackContent);
      setGeneratedContent(fallbackContent);
      
    } finally {
      setLoading(false);
    }
  };

  const platforms = [
    { value: 'youtube', label: 'YouTube', icon: '🎥' },
    { value: 'tiktok', label: 'TikTok', icon: '🎵' },
    { value: 'instagram', label: 'Instagram', icon: '📸' },
    { value: 'facebook', label: 'Facebook', icon: '👥' }
  ];

  const contentTypes = [
    { value: 'educational', label: 'Educational' },
    { value: 'entertainment', label: 'Entertainment' },
    { value: 'lifestyle', label: 'Lifestyle' },
    { value: 'news', label: 'News' }
  ];

  return (
    <Box>
      <Typography variant="h5" sx={{ fontWeight: 600, mb: 3 }}>
        AI Content Generator
      </Typography>

      {/* Input Form */}
      <Card sx={{ mb: 3, background: 'linear-gradient(135deg, #1E293B 0%, #334155 100%)', border: '1px solid #334155' }}>
        <CardContent>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Content Idea"
                placeholder="e.g., Best AI Tools for Content Creators 2025"
                value={formData.idea}
                onChange={(e) => handleInputChange('idea', e.target.value)}
                error={!!error && !formData.idea.trim()}
                helperText={error && !formData.idea.trim() ? 'This field is required' : ''}
                sx={{ mb: 2 }}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Platform</InputLabel>
                <Select
                  value={formData.platform}
                  onChange={(e) => handleInputChange('platform', e.target.value)}
                >
                  {platforms.map(platform => (
                    <MenuItem key={platform.value} value={platform.value}>
                      {platform.icon} {platform.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Content Type</InputLabel>
                <Select
                  value={formData.content_type}
                  onChange={(e) => handleInputChange('content_type', e.target.value)}
                >
                  {contentTypes.map(type => (
                    <MenuItem key={type.value} value={type.value}>
                      {type.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12}>
              <Button
                variant="contained"
                startIcon={loading ? <CircularProgress size={20} /> : <AutoAwesome />}
                onClick={generateContent}
                disabled={loading || !formData.idea.trim()}
                fullWidth
                sx={{ 
                  bgcolor: '#10B981', 
                  '&:hover': { bgcolor: '#059669' },
                  py: 1.5
                }}
              >
                {loading ? 'Generating Content...' : 'Generate Content'}
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          <Typography variant="body2">
            <strong>Error:</strong> {error}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Check the browser console (F12) for detailed error information.
          </Typography>
        </Alert>
      )}

      {/* Generated Content Display */}
      {generatedContent && (
        <Card sx={{ background: 'linear-gradient(135deg, #1E293B 0%, #334155 100%)', border: '1px solid #334155' }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Generated Content
              </Typography>
              {generatedContent.fallback && (
                <Chip 
                  label="Fallback Content" 
                  color="warning" 
                  size="small"
                  sx={{ ml: 2 }}
                />
              )}
            </Box>

            {/* Title */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Title
              </Typography>
              <Typography variant="h6" sx={{ fontWeight: 500 }}>
                {generatedContent.title || 'No title generated'}
              </Typography>
            </Box>

            {/* Description */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Description
              </Typography>
              <Typography variant="body2">
                {generatedContent.description || 'No description generated'}
              </Typography>
            </Box>

            {/* Script */}
            {generatedContent.script && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Script
                </Typography>
                <Box sx={{ bgcolor: '#0F172A', p: 2, borderRadius: 2 }}>
                  {/* Hook */}
                  <Box sx={{ mb: 2 }}>
                    <Chip label="Hook" size="small" sx={{ mb: 1, bgcolor: '#3B82F6' }} />
                    <Typography variant="body2">
                      {generatedContent.script.hook || 'No hook generated'}
                    </Typography>
                  </Box>

                  <Divider sx={{ my: 2, borderColor: '#334155' }} />

                  {/* Main Content */}
                  <Box sx={{ mb: 2 }}>
                    <Chip label="Main Content" size="small" sx={{ mb: 1, bgcolor: '#10B981' }} />
                    <Typography variant="body2">
                      {generatedContent.script.main_content || 'No main content generated'}
                    </Typography>
                  </Box>

                  <Divider sx={{ my: 2, borderColor: '#334155' }} />

                  {/* CTA */}
                  <Box>
                    <Chip label="Call to Action" size="small" sx={{ mb: 1, bgcolor: '#F59E0B' }} />
                    <Typography variant="body2">
                      {generatedContent.script.cta || 'No CTA generated'}
                    </Typography>
                  </Box>
                </Box>
              </Box>
            )}

            {/* Metadata */}
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Platform
                </Typography>
                <Typography variant="body2">
                  {platforms.find(p => p.value === generatedContent.platform)?.label || generatedContent.platform}
                </Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Estimated Duration
                </Typography>
                <Typography variant="body2">
                  {generatedContent.estimated_duration || 'Not specified'}
                </Typography>
              </Grid>
            </Grid>

            {/* Hashtags */}
            {generatedContent.hashtags && generatedContent.hashtags.length > 0 && (
              <Box sx={{ mt: 3 }}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Hashtags
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  {generatedContent.hashtags.map((tag, index) => (
                    <Chip 
                      key={index} 
                      label={tag} 
                      size="small" 
                      sx={{ bgcolor: '#0F172A' }}
                    />
                  ))}
                </Box>
              </Box>
            )}

            {/* Debug Info */}
            {generatedContent.fallback && (
              <Alert severity="info" sx={{ mt: 3 }}>
                <Typography variant="body2">
                  <strong>Debug Info:</strong> This is fallback content due to: {generatedContent.error_reason}
                </Typography>
              </Alert>
            )}

            {/* Action Buttons */}
            <Box sx={{ display: 'flex', gap: 2, mt: 3 }}>
              <Button
                variant="contained"
                startIcon={<PlayArrow />}
                sx={{ bgcolor: '#3B82F6', '&:hover': { bgcolor: '#1D4ED8' } }}
              >
                Add to Production Queue
              </Button>
              <Button
                variant="outlined"
                onClick={() => generateContent()}
                disabled={loading}
              >
                Regenerate
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default ContentGenerator;