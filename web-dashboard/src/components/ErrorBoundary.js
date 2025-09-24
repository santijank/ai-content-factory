import React from 'react';
import './ErrorBoundary.css';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null,
      errorInfo: null,
      errorId: null
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Generate unique error ID for tracking
    const errorId = `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    // Log error details
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    // Update state with error details
    this.setState({
      error: error,
      errorInfo: errorInfo,
      errorId: errorId
    });

    // Send error to logging service (if configured)
    this.logErrorToService(error, errorInfo, errorId);
  }

  logErrorToService = (error, errorInfo, errorId) => {
    try {
      // You can integrate with error tracking services like Sentry, LogRocket, etc.
      const errorData = {
        errorId,
        message: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href
      };

      // Example: Send to your error tracking endpoint
      if (process.env.REACT_APP_ERROR_TRACKING_URL) {
        fetch(process.env.REACT_APP_ERROR_TRACKING_URL, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(errorData)
        }).catch(console.error);
      }
    } catch (loggingError) {
      console.error('Failed to log error:', loggingError);
    }
  };

  handleRetry = () => {
    this.setState({ 
      hasError: false, 
      error: null, 
      errorInfo: null,
      errorId: null 
    });
  };

  handleReload = () => {
    window.location.reload();
  };

  handleReportError = () => {
    const { error, errorInfo, errorId } = this.state;
    const errorDetails = {
      errorId,
      message: error?.message,
      stack: error?.stack,
      componentStack: errorInfo?.componentStack,
      timestamp: new Date().toISOString()
    };

    // Create mailto link with error details
    const subject = encodeURIComponent(`Error Report - ${errorId}`);
    const body = encodeURIComponent(`
Error Report:
============
Error ID: ${errorId}
Message: ${error?.message}
Time: ${new Date().toLocaleString()}
URL: ${window.location.href}

Technical Details:
${JSON.stringify(errorDetails, null, 2)}

Please describe what you were doing when this error occurred:
[Please fill in]
    `);

    window.open(`mailto:support@example.com?subject=${subject}&body=${body}`);
  };

  render() {
    if (this.state.hasError) {
      const { error, errorId } = this.state;
      const { fallback: Fallback, showDetails = false } = this.props;

      // Use custom fallback if provided
      if (Fallback) {
        return (
          <Fallback 
            error={error}
            errorId={errorId}
            retry={this.handleRetry}
            reload={this.handleReload}
          />
        );
      }

      // Default error UI
      return (
        <div className="error-boundary">
          <div className="error-boundary-container">
            <div className="error-icon">
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="#dc3545" strokeWidth="2"/>
                <line x1="15" y1="9" x2="9" y2="15" stroke="#dc3545" strokeWidth="2"/>
                <line x1="9" y1="9" x2="15" y2="15" stroke="#dc3545" strokeWidth="2"/>
              </svg>
            </div>
            
            <h2 className="error-title">Oops! Something went wrong</h2>
            <p className="error-message">
              We encountered an unexpected error. Don't worry, our team has been notified.
            </p>

            <div className="error-actions">
              <button 
                className="btn btn-primary" 
                onClick={this.handleRetry}
              >
                Try Again
              </button>
              <button 
                className="btn btn-secondary" 
                onClick={this.handleReload}
              >
                Reload Page
              </button>
              <button 
                className="btn btn-outline" 
                onClick={this.handleReportError}
              >
                Report Issue
              </button>
            </div>

            {errorId && (
              <div className="error-id">
                <small>Error ID: {errorId}</small>
              </div>
            )}

            {showDetails && process.env.NODE_ENV === 'development' && (
              <details className="error-details">
                <summary>Technical Details (Development Mode)</summary>
                <div className="error-stack">
                  <h4>Error Message:</h4>
                  <pre>{error?.message}</pre>
                  
                  <h4>Stack Trace:</h4>
                  <pre>{error?.stack}</pre>
                  
                  {this.state.errorInfo?.componentStack && (
                    <>
                      <h4>Component Stack:</h4>
                      <pre>{this.state.errorInfo.componentStack}</pre>
                    </>
                  )}
                </div>
              </details>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Higher-order component for functional components
export const withErrorBoundary = (Component, errorBoundaryProps = {}) => {
  const WrappedComponent = (props) => (
    <ErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </ErrorBoundary>
  );
  
  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;
  return WrappedComponent;
};

// Specialized error boundaries for different sections
export const TrendErrorBoundary = ({ children }) => (
  <ErrorBoundary 
    fallback={({ retry }) => (
      <div className="section-error">
        <h3>🔍 Trend Analysis Error</h3>
        <p>Unable to load trend data. Please try again.</p>
        <button className="btn btn-sm btn-primary" onClick={retry}>
          Retry Loading Trends
        </button>
      </div>
    )}
  >
    {children}
  </ErrorBoundary>
);

export const ContentErrorBoundary = ({ children }) => (
  <ErrorBoundary
    fallback={({ retry }) => (
      <div className="section-error">
        <h3>🎬 Content Generation Error</h3>
        <p>Unable to generate content. Please check your settings and try again.</p>
        <button className="btn btn-sm btn-primary" onClick={retry}>
          Retry Content Generation
        </button>
      </div>
    )}
  >
    {children}
  </ErrorBoundary>
);

export const AnalyticsErrorBoundary = ({ children }) => (
  <ErrorBoundary
    fallback={({ retry }) => (
      <div className="section-error">
        <h3>📊 Analytics Error</h3>
        <p>Unable to load analytics data. Please try refreshing the page.</p>
        <button className="btn btn-sm btn-primary" onClick={retry}>
          Retry Loading Analytics
        </button>
      </div>
    )}
  >
    {children}
  </ErrorBoundary>
);

// Hook for error reporting in functional components
export const useErrorHandler = () => {
  return React.useCallback((error, errorInfo = {}) => {
    console.error('Manual error report:', error, errorInfo);
    
    // You can throw the error to trigger the nearest ErrorBoundary
    throw error;
  }, []);
};

export default ErrorBoundary;