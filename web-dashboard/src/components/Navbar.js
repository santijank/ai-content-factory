import React from 'react';
import { AppBar, Toolbar, Typography, IconButton, Badge, Avatar, Box } from '@mui/material';
import { Menu as MenuIcon, Notifications, Settings, TrendingUp } from '@mui/icons-material';
import { useAppStore } from '../store/appStore';

const Navbar = () => {
  const { toggleSidebar, user, dashboardData } = useAppStore();

  return (
    <AppBar 
      position="sticky" 
      sx={{ 
        backgroundColor: '#1E293B',
        borderBottom: '1px solid #334155',
        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
      }}
    >
      <Toolbar>
        <IconButton
          edge="start"
          color="inherit"
          aria-label="toggle sidebar"
          onClick={toggleSidebar}
          sx={{ mr: 2 }}
        >
          <MenuIcon />
        </IconButton>
        
        <Box sx={{ display: 'flex', alignItems: 'center', mr: 3 }}>
          <TrendingUp sx={{ mr: 1, color: '#3B82F6' }} />
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            AI Content Factory
          </Typography>
        </Box>

        {/* Stats Quick View */}
        <Box sx={{ display: 'flex', gap: 3, mr: 'auto', ml: 4 }}>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="caption" color="text.secondary">
              Today's Revenue
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: 600, color: '#10B981' }}>
              ฿{dashboardData.todayRevenue.toLocaleString()}
            </Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="caption" color="text.secondary">
              Active Trends
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: 600, color: '#F59E0B' }}>
              {dashboardData.trendsCount}
            </Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="caption" color="text.secondary">
              Opportunities
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: 600, color: '#EF4444' }}>
              {dashboardData.opportunitiesCount}
            </Typography>
          </Box>
        </Box>

        {/* Right side icons */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <IconButton color="inherit">
            <Badge badgeContent={4} color="error">
              <Notifications />
            </Badge>
          </IconButton>
          
          <IconButton color="inherit">
            <Settings />
          </IconButton>
          
          <Box sx={{ ml: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
            <Box sx={{ textAlign: 'right' }}>
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                {user.name}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {user.tier} Plan
              </Typography>
            </Box>
            <Avatar 
              sx={{ 
                bgcolor: '#3B82F6',
                width: 40,
                height: 40
              }}
            >
              AI
            </Avatar>
          </Box>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Navbar;