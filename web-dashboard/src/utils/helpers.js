// Utility Helper Functions for AI Content Factory

// ========================
// Date & Time Utilities
// ========================

export const formatDate = (date, format = 'default') => {
  if (!date) return '';
  
  const d = new Date(date);
  
  const formats = {
    default: d.toLocaleDateString(),
    time: d.toLocaleTimeString(),
    datetime: d.toLocaleString(),
    iso: d.toISOString(),
    relative: getRelativeTime(d),
    thai: d.toLocaleDateString('th-TH'),
    short: d.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      year: 'numeric' 
    })
  };
  
  return formats[format] || formats.default;
};

export const getRelativeTime = (date) => {
  const now = new Date();
  const diffInSeconds = Math.floor((now - new Date(date)) / 1000);
  
  const intervals = [
    { label: 'year', seconds: 31536000 },
    { label: 'month', seconds: 2592000 },
    { label: 'week', seconds: 604800 },
    { label: 'day', seconds: 86400 },
    { label: 'hour', seconds: 3600 },
    { label: 'minute', seconds: 60 },
    { label: 'second', seconds: 1 }
  ];
  
  for (const interval of intervals) {
    const count = Math.floor(diffInSeconds / interval.seconds);
    if (count >= 1) {
      return `${count} ${interval.label}${count !== 1 ? 's' : ''} ago`;
    }
  }
  
  return 'just now';
};

export const isToday = (date) => {
  const today = new Date();
  const checkDate = new Date(date);
  return checkDate.toDateString() === today.toDateString();
};

export const isYesterday = (date) => {
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  const checkDate = new Date(date);
  return checkDate.toDateString() === yesterday.toDateString();
};

// ========================
// Number & Currency Utilities
// ========================

export const formatNumber = (num, options = {}) => {
  if (num === null || num === undefined || isNaN(num)) return '0';
  
  const {
    decimals = 0,
    currency = false,
    currencyCode = 'THB',
    compact = false,
    percentage = false
  } = options;
  
  if (percentage) {
    return `${(num * 100).toFixed(decimals)}%`;
  }
  
  if (compact) {
    return formatCompactNumber(num, decimals);
  }
  
  if (currency) {
    return new Intl.NumberFormat('th-TH', {
      style: 'currency',
      currency: currencyCode,
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }).format(num);
  }
  
  return new Intl.NumberFormat('th-TH', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  }).format(num);
};

export const formatCompactNumber = (num, decimals = 1) => {
  const units = [
    { value: 1e9, symbol: 'B' },
    { value: 1e6, symbol: 'M' },
    { value: 1e3, symbol: 'K' }
  ];
  
  for (const unit of units) {
    if (Math.abs(num) >= unit.value) {
      return `${(num / unit.value).toFixed(decimals)}${unit.symbol}`;
    }
  }
  
  return num.toString();
};

export const calculatePercentageChange = (current, previous) => {
  if (!previous || previous === 0) return 0;
  return ((current - previous) / previous) * 100;
};

// ========================
// String Utilities
// ========================

export const truncateText = (text, maxLength = 100, suffix = '...') => {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength).trim() + suffix;
};

export const capitalizeFirst = (str) => {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
};

export const capitalizeWords = (str) => {
  if (!str) return '';
  return str.split(' ')
    .map(word => capitalizeFirst(word))
    .join(' ');
};

export const slugify = (text) => {
  if (!text) return '';
  return text
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, '-')
    .replace(/^-+|-+$/g, '');
};

export const extractHashtags = (text) => {
  if (!text) return [];
  const hashtagRegex = /#[\w\u0E00-\u0E7F]+/g;
  return text.match(hashtagRegex) || [];
};

export const removeEmojis = (text) => {
  if (!text) return '';
  return text.replace(/[\u{1F600}-\u{1F64F}]|[\u{1F300}-\u{1F5FF}]|[\u{1F680}-\u{1F6FF}]|[\u{1F1E0}-\u{1F1FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]/gu, '');
};

// ========================
// Array & Object Utilities
// ========================

export const sortBy = (array, key, direction = 'asc') => {
  if (!Array.isArray(array)) return [];
  
  return [...array].sort((a, b) => {
    const aVal = getNestedValue(a, key);
    const bVal = getNestedValue(b, key);
    
    if (aVal === bVal) return 0;
    
    const comparison = aVal > bVal ? 1 : -1;
    return direction === 'desc' ? -comparison : comparison;
  });
};

export const groupBy = (array, key) => {
  if (!Array.isArray(array)) return {};
  
  return array.reduce((groups, item) => {
    const groupKey = getNestedValue(item, key);
    if (!groups[groupKey]) {
      groups[groupKey] = [];
    }
    groups[groupKey].push(item);
    return groups;
  }, {});
};

export const getNestedValue = (obj, path) => {
  if (!obj || !path) return undefined;
  
  return path.split('.').reduce((current, key) => {
    return current && current[key] !== undefined ? current[key] : undefined;
  }, obj);
};

export const filterBy = (array, filters) => {
  if (!Array.isArray(array)) return [];
  
  return array.filter(item => {
    return Object.entries(filters).every(([key, value]) => {
      if (value === null || value === undefined || value === '') return true;
      
      const itemValue = getNestedValue(item, key);
      
      if (typeof value === 'string') {
        return itemValue?.toString().toLowerCase().includes(value.toLowerCase());
      }
      
      return itemValue === value;
    });
  });
};

export const uniqueBy = (array, key) => {
  if (!Array.isArray(array)) return [];
  
  const seen = new Set();
  return array.filter(item => {
    const value = getNestedValue(item, key);
    if (seen.has(value)) {
      return false;
    }
    seen.add(value);
    return true;
  });
};

// ========================
// Validation Utilities
// ========================

export const validateEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

export const validateUrl = (url) => {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};

export const validateRequired = (value) => {
  return value !== null && value !== undefined && value !== '';
};

export const validateMinLength = (value, minLength) => {
  return value && value.length >= minLength;
};

export const validateMaxLength = (value, maxLength) => {
  return !value || value.length <= maxLength;
};

// ========================
// Storage Utilities
// ========================

export const storage = {
  get: (key, defaultValue = null) => {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
      console.error('Error reading from localStorage:', error);
      return defaultValue;
    }
  },
  
  set: (key, value) => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch (error) {
      console.error('Error writing to localStorage:', error);
      return false;
    }
  },
  
  remove: (key) => {
    try {
      localStorage.removeItem(key);
      return true;
    } catch (error) {
      console.error('Error removing from localStorage:', error);
      return false;
    }
  },
  
  clear: () => {
    try {
      localStorage.clear();
      return true;
    } catch (error) {
      console.error('Error clearing localStorage:', error);
      return false;
    }
  }
};

// ========================
// API Utilities
// ========================

export const makeApiCall = async (url, options = {}) => {
  const defaultOptions = {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  };
  
  const finalOptions = { ...defaultOptions, ...options };
  
  try {
    const response = await fetch(url, finalOptions);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return await response.json();
    } else {
      return await response.text();
    }
  } catch (error) {
    console.error('API call failed:', error);
    throw error;
  }
};

export const buildQueryString = (params) => {
  const cleanParams = Object.entries(params)
    .filter(([_, value]) => value !== null && value !== undefined && value !== '')
    .map(([key, value]) => [key, encodeURIComponent(value)]);
  
  return new URLSearchParams(cleanParams).toString();
};

// ========================
// Color Utilities
// ========================

export const getStatusColor = (status) => {
  const colors = {
    success: '#28a745',
    error: '#dc3545',
    warning: '#ffc107',
    info: '#17a2b8',
    primary: '#007bff',
    secondary: '#6c757d',
    pending: '#fd7e14',
    active: '#20c997',
    inactive: '#868e96'
  };
  
  return colors[status] || colors.secondary;
};

export const getTrendColor = (score) => {
  if (score >= 8) return '#28a745'; // Green
  if (score >= 6) return '#20c997'; // Teal
  if (score >= 4) return '#ffc107'; // Yellow
  if (score >= 2) return '#fd7e14'; // Orange
  return '#dc3545'; // Red
};

export const getRoiColor = (roi) => {
  if (roi >= 3) return '#28a745';
  if (roi >= 2) return '#20c997';
  if (roi >= 1) return '#ffc107';
  return '#dc3545';
};

// ========================
// Content Utilities
// ========================

export const generateSlug = (title) => {
  if (!title) return '';
  return title
    .toLowerCase()
    .replace(/[^a-z0-9\u0E00-\u0E7F]+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
};

export const estimateReadTime = (text) => {
  if (!text) return 0;
  const wordsPerMinute = 200;
  const words = text.trim().split(/\s+/).length;
  return Math.ceil(words / wordsPerMinute);
};

export const extractKeywords = (text, limit = 10) => {
  if (!text) return [];
  
  const commonWords = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'];
  
  const words = text
    .toLowerCase()
    .replace(/[^\w\s]/g, '')
    .split(/\s+/)
    .filter(word => word.length > 2 && !commonWords.includes(word));
  
  const frequency = words.reduce((acc, word) => {
    acc[word] = (acc[word] || 0) + 1;
    return acc;
  }, {});
  
  return Object.entries(frequency)
    .sort(([,a], [,b]) => b - a)
    .slice(0, limit)
    .map(([word]) => word);
};

// ========================
// Platform Utilities
// ========================

export const getPlatformIcon = (platform) => {
  const icons = {
    youtube: '📺',
    tiktok: '🎵',
    instagram: '📷',
    facebook: '👥',
    twitter: '🐦',
    linkedin: '💼'
  };
  
  return icons[platform.toLowerCase()] || '📱';
};

export const getPlatformColor = (platform) => {
  const colors = {
    youtube: '#FF0000',
    tiktok: '#000000',
    instagram: '#E4405F',
    facebook: '#1877F2',
    twitter: '#1DA1F2',
    linkedin: '#0A66C2'
  };
  
  return colors[platform.toLowerCase()] || '#6c757d';
};

export const formatViewCount = (views) => {
  return formatCompactNumber(views, 1);
};

// ========================
// Performance Utilities
// ========================

export const debounce = (func, delay) => {
  let timeoutId;
  return (...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func.apply(null, args), delay);
  };
};

export const throttle = (func, limit) => {
  let inThrottle;
  return (...args) => {
    if (!inThrottle) {
      func.apply(null, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
};

export const memoize = (func) => {
  const cache = new Map();
  return (...args) => {
    const key = JSON.stringify(args);
    if (cache.has(key)) {
      return cache.get(key);
    }
    const result = func(...args);
    cache.set(key, result);
    return result;
  };
};

// ========================
// Export Default Object
// ========================

const helpers = {
  // Date & Time
  formatDate,
  getRelativeTime,
  isToday,
  isYesterday,
  
  // Numbers & Currency
  formatNumber,
  formatCompactNumber,
  calculatePercentageChange,
  
  // Strings
  truncateText,
  capitalizeFirst,
  capitalizeWords,
  slugify,
  extractHashtags,
  removeEmojis,
  
  // Arrays & Objects
  sortBy,
  groupBy,
  getNestedValue,
  filterBy,
  uniqueBy,
  
  // Validation
  validateEmail,
  validateUrl,
  validateRequired,
  validateMinLength,
  validateMaxLength,
  
  // Storage
  storage,
  
  // API
  makeApiCall,
  buildQueryString,
  
  // Colors
  getStatusColor,
  getTrendColor,
  getRoiColor,
  
  // Content
  generateSlug,
  estimateReadTime,
  extractKeywords,
  
  // Platform
  getPlatformIcon,
  getPlatformColor,
  formatViewCount,
  
  // Performance
  debounce,
  throttle,
  memoize
};

export default helpers;