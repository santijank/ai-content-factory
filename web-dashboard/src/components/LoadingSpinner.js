import React from 'react';
import './LoadingSpinner.css';

const LoadingSpinner = ({ 
  size = 'medium', 
  color = 'primary', 
  text = 'Loading...', 
  overlay = false,
  className = '' 
}) => {
  const sizeClasses = {
    small: 'spinner-sm',
    medium: 'spinner-md', 
    large: 'spinner-lg'
  };

  const colorClasses = {
    primary: 'spinner-primary',
    secondary: 'spinner-secondary',
    success: 'spinner-success',
    warning: 'spinner-warning',
    danger: 'spinner-danger'
  };

  const spinnerClass = `
    loading-spinner 
    ${sizeClasses[size] || sizeClasses.medium}
    ${colorClasses[color] || colorClasses.primary}
    ${className}
  `.trim();

  const SpinnerComponent = (
    <div className={spinnerClass}>
      <div className="spinner-ring">
        <div></div>
        <div></div>
        <div></div>
        <div></div>
      </div>
      {text && <div className="spinner-text">{text}</div>}
    </div>
  );

  if (overlay) {
    return (
      <div className="spinner-overlay">
        {SpinnerComponent}
      </div>
    );
  }

  return SpinnerComponent;
};

// Different spinner variants
export const DotSpinner = ({ size = 'medium', color = 'primary', text = '' }) => (
  <div className={`dot-spinner spinner-${size} spinner-${color}`}>
    <div className="dot-spinner-dots">
      <div className="dot"></div>
      <div className="dot"></div>
      <div className="dot"></div>
    </div>
    {text && <div className="spinner-text">{text}</div>}
  </div>
);

export const PulseSpinner = ({ size = 'medium', color = 'primary', text = '' }) => (
  <div className={`pulse-spinner spinner-${size} spinner-${color}`}>
    <div className="pulse-circle"></div>
    {text && <div className="spinner-text">{text}</div>}
  </div>
);

export const BarSpinner = ({ size = 'medium', color = 'primary', text = '' }) => (
  <div className={`bar-spinner spinner-${size} spinner-${color}`}>
    <div className="bar"></div>
    <div className="bar"></div>
    <div className="bar"></div>
    <div className="bar"></div>
    <div className="bar"></div>
    {text && <div className="spinner-text">{text}</div>}
  </div>
);

// Loading states for specific components
export const TrendLoadingSpinner = () => (
  <LoadingSpinner 
    text="🔍 Analyzing trends..." 
    color="primary" 
    size="medium"
  />
);

export const ContentLoadingSpinner = () => (
  <LoadingSpinner 
    text="🎬 Generating content..." 
    color="success" 
    size="medium"
  />
);

export const UploadLoadingSpinner = () => (
  <LoadingSpinner 
    text="📤 Uploading to platforms..." 
    color="warning" 
    size="medium"
  />
);

export const AnalyticsLoadingSpinner = () => (
  <DotSpinner 
    text="📊 Loading analytics..." 
    color="secondary" 
    size="medium"
  />
);

export default LoadingSpinner;