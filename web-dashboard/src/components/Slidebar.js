import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Drawer, 
  List, 
  ListItem, 
  ListItemIcon, 
  ListItemText,
  Box,
  Typography,
  Divider,
  Chip
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  TrendingUp,
  Lightbulb,
  VideoLibrary,
  Analytics,
  Settings,
  AutoAwesome,
  Schedule
} from '@mui/icons-material';
import { useAppStore } from '../store/appStore';

const Sidebar = ({ open }) => {
  const location = useLocation();
  const { setCurrentPage, contentQueue } = useAppStore();

  const menuItems = [
    {
      text: 'Dashboard',
      icon: <DashboardIcon />,
      path: '/dashboard',
      color: '#3B82F6'
    },
    {
      text: 'Trends Monitor',
      icon: <TrendingUp />,
      path: '/trends',
      color: '#F59E0B'
    },
    {
      text: 'Opportunities',
      icon: <Lightbulb />,
      path: '/opportunities',
      color: '#EF4444',
      badge: 12
    },
    {
      text: 'Content Studio',
      icon: <VideoLibrary />,
      path: '/content',
      color: '#10B981',
      badge: contentQueue.length
    },
    {
      text: 'Analytics',
      icon: <Analytics />,
      path: '/analytics',
      color: '#8B5CF6'
    },
    {
      text: 'Settings',
      icon: <Settings />,
      path: '/settings',
      color: '#6B7280'
    }
  ];

  const quickActions = [
    {
      text: 'AI Generate',
      icon: <AutoAwesome />,
      action: 'generate',
      color: '#EC4899'
    },
    {
      text: 'Schedule Post',
      icon: <Schedule />,
      action: 'schedule',
      color: '#06B6D4'
    }
  ];

  const drawerWidth = open ? 240 : 64;

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
          backgroundColor: '#1E293B',
          borderRight: '1px solid #334155',
          transition: 'width 0.3s ease',
          overflowX: 'hidden'
        },
      }}
    >
      <Box sx={{ mt: 8 }}>
        {/* Main Navigation */}
        <List>
          {menuItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <ListItem
                key={item.text}
                component={Link}
                to={item.path}
                onClick={() => setCurrentPage(item.path.slice(1))}
                sx={{
                  mx: 1,
                  mb: 0.5,
                  borderRadius: 2,
                  backgroundColor: isActive ? `${item.color}20` : 'transparent',
                  borderLeft: isActive ? `3px solid ${item.color}` : 'none',
                  '&:hover': {
                    backgroundColor: `${item.color}10`
                  },
                  transition: 'all 0.2s ease'
                }}
              >
                <ListItemIcon sx={{ 
                  color: isActive ? item.color : '#CBD5E1',
                  minWidth: open ? 40 : 'auto',
                  justifyContent: 'center'
                }}>
                  {item.icon}
                </ListItemIcon>
                {open && (
                  <ListItemText
                    primary={item.text}
                    sx={{
                      '& .MuiListItemText-primary': {
                        fontSize: '0.875rem',
                        fontWeight: isActive ? 600 : 400,
                        color: isActive ? '#F1F5F9' : '#CBD5E1'
                      }
                    }}
                  />
                )}
                {open && item.badge && (
                  <Chip
                    label={item.badge}
                    size="small"
                    sx={{
                      bgcolor: item.color,
                      color: 'white',
                      fontSize: '0.75rem',
                      height: 20,
                      minWidth: 20
                    }}
                  />
                )}
              </ListItem>
            );
          })}
        </List>

        {open && (
          <>
            <Divider sx={{ mx: 2, my: 2, borderColor: '#334155' }} />
            
            {/* Quick Actions */}
            <Box sx={{ px: 2, mb: 2 }}>
              <Typography 
                variant="caption" 
                sx={{ 
                  color: '#64748B',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em'
                }}
              >
                Quick Actions
              </Typography>
            </Box>
            
            <List>
              {quickActions.map((action) => (
                <ListItem
                  key={action.text}
                  button
                  sx={{
                    mx: 1,
                    mb: 0.5,
                    borderRadius: 2,
                    '&:hover': {
                      backgroundColor: `${action.color}10`
                    }
                  }}
                >
                  <ListItemIcon sx={{ 
                    color: action.color,
                    minWidth: 40
                  }}>
                    {action.icon}
                  </ListItemIcon>
                  <ListItemText
                    primary={action.text}
                    sx={{
                      '& .MuiListItemText-primary': {
                        fontSize: '0.875rem',
                        color: '#CBD5E1'
                      }
                    }}
                  />
                </ListItem>
              ))}
            </List>
          </>
        )}
      </Box>
    </Drawer>
  );
};

export default Sidebar;