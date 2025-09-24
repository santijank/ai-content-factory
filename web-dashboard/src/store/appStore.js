import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useAppStore = create(
  persist(
    (set, get) => ({
      // UI State
      sidebarOpen: true,
      currentPage: 'dashboard',
      loading: false,
      
      // User Settings
      user: {
        name: 'AI Content Creator',
        tier: 'BALANCED',
        activePlatforms: ['youtube', 'tiktok'],
      },
      
      // Dashboard State
      dashboardData: {
        trendsCount: 0,
        opportunitiesCount: 0,
        contentCount: 0,
        todayRevenue: 0,
      },
      
      // Trends State
      trends: [],
      selectedTrends: [],
      
      // Opportunities State
      opportunities: [],
      selectedOpportunities: [],
      
      // Content State
      contentItems: [],
      contentQueue: [],
      
      // Actions
      toggleSidebar: () => set((state) => ({ 
        sidebarOpen: !state.sidebarOpen 
      })),
      
      setCurrentPage: (page) => set({ currentPage: page }),
      
      setLoading: (loading) => set({ loading }),
      
      updateDashboardData: (data) => set((state) => ({
        dashboardData: { ...state.dashboardData, ...data }
      })),
      
      setTrends: (trends) => set({ trends }),
      
      toggleTrendSelection: (trendId) => set((state) => {
        const isSelected = state.selectedTrends.includes(trendId);
        return {
          selectedTrends: isSelected
            ? state.selectedTrends.filter(id => id !== trendId)
            : [...state.selectedTrends, trendId]
        };
      }),
      
      setOpportunities: (opportunities) => set({ opportunities }),
      
      selectOpportunity: (opportunityId) => set((state) => ({
        selectedOpportunities: [...state.selectedOpportunities, opportunityId]
      })),
      
      addToContentQueue: (contentData) => set((state) => ({
        contentQueue: [...state.contentQueue, {
          id: Date.now(),
          ...contentData,
          status: 'queued',
          createdAt: new Date().toISOString()
        }]
      })),
      
      updateContentStatus: (contentId, status) => set((state) => ({
        contentQueue: state.contentQueue.map(item =>
          item.id === contentId ? { ...item, status } : item
        )
      })),
      
      updateUserSettings: (settings) => set((state) => ({
        user: { ...state.user, ...settings }
      })),
      
      // Clear functions
      clearSelectedTrends: () => set({ selectedTrends: [] }),
      clearSelectedOpportunities: () => set({ selectedOpportunities: [] }),
      clearContentQueue: () => set({ contentQueue: [] }),
    }),
    {
      name: 'ai-content-factory-store',
      partialize: (state) => ({
        user: state.user,
        sidebarOpen: state.sidebarOpen,
      }),
    }
  )
);