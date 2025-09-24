import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Toaster } from 'react-hot-toast';

// Pages
import Dashboard from './pages/Dashboard';
import Trends from './pages/Trends';
import Opportunities from './pages/Opportunities';
import Content from './pages/Content';
import Analytics from './pages/Analytics';
import Settings from './pages/Settings';

// Components
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';

// Store
import { useAppStore } from './store/appStore';

// Create theme
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#3B82F6',
      light: '#60A5FA',
      dark: '#1D4ED8',
    },
    secondary: {
      main: '#10B981',
      light: '#34D399',
      dark: '#059669',
    },
    background: {
      default: '#0F172A',
      paper: '#1E293B',
    },
    text: {
      primary: '#F1F5F9',
      secondary: '#CBD5E1',
    }
  },
  typography: {
    fontFamily: '"Inter", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 500,
    }
  },
  shape: {
    borderRadius: 12,
  }
});

// Create query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

function App() {
  const { sidebarOpen } = useAppStore();

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Router>
          <div className="min-h-screen bg-slate-900 text-slate-100">
            <Navbar />
            <div className="flex">
              <Sidebar open={sidebarOpen} />
              <main className={`flex-1 transition-all duration-300 ${
                sidebarOpen ? 'ml-64' : 'ml-16'
              }`}>
                <div className="p-6">
                  <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/trends" element={<Trends />} />
                    <Route path="/opportunities" element={<Opportunities />} />
                    <Route path="/content" element={<Content />} />
                    <Route path="/analytics" element={<Analytics />} />
                    <Route path="/settings" element={<Settings />} />
                  </Routes>
                </div>
              </main>
            </div>
          </div>
          <Toaster 
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#1E293B',
                color: '#F1F5F9',
                border: '1px solid #334155'
              }
            }}
          />
        </Router>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;