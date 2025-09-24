import React from 'react';
import '../styles/TrendCard.css';

const TrendCard = ({ trend, onAnalyze, onCreateContent }) => {
    const formatNumber = (num) => {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num?.toString() || '0';
    };

    const getPopularityClass = (score) => {
        if (score >= 80) return 'popularity-high';
        if (score >= 60) return 'popularity-medium';
        return 'popularity-low';
    };

    const getGrowthIcon = (rate) => {
        if (rate > 20) return '🚀';
        if (rate > 0) return '📈';
        if (rate < -20) return '📉';
        return '➡️';
    };

    const formatTimeAgo = (timestamp) => {
        const now = new Date();
        const trendTime = new Date(timestamp);
        const diffInHours = Math.floor((now - trendTime) / (1000 * 60 * 60));
        
        if (diffInHours < 1) return 'Just now';
        if (diffInHours < 24) return `${diffInHours}h ago`;
        const diffInDays = Math.floor(diffInHours / 24);
        return `${diffInDays}d ago`;
    };

    return (
        <div className="trend-card">
            <div className="trend-header">
                <div className="trend-title">
                    <h3>{trend.topic}</h3>
                    <span className="trend-source">{trend.source}</span>
                </div>
                <div className="trend-timing">
                    <span className="time-ago">{formatTimeAgo(trend.collected_at)}</span>
                </div>
            </div>

            <div className="trend-metrics">
                <div className="metric-item">
                    <span className="metric-label">Popularity</span>
                    <div className="metric-value">
                        <span className={`popularity-score ${getPopularityClass(trend.popularity_score)}`}>
                            {trend.popularity_score?.toFixed(1)}
                        </span>
                        <div className="popularity-bar">
                            <div 
                                className={`popularity-fill ${getPopularityClass(trend.popularity_score)}`}
                                style={{ width: `${trend.popularity_score}%` }}
                            ></div>
                        </div>
                    </div>
                </div>

                <div className="metric-item">
                    <span className="metric-label">Growth</span>
                    <div className="metric-value">
                        <span className="growth-rate">
                            {getGrowthIcon(trend.growth_rate)}
                            {trend.growth_rate > 0 ? '+' : ''}
                            {trend.growth_rate?.toFixed(1)}%
                        </span>
                    </div>
                </div>

                <div className="metric-item">
                    <span className="metric-label">Region</span>
                    <div className="metric-value">
                        <span className="region-badge">{trend.region || 'Global'}</span>
                    </div>
                </div>
            </div>

            {trend.keywords && trend.keywords.length > 0 && (
                <div className="trend-keywords">
                    <span className="keywords-label">Keywords:</span>
                    <div className="keywords-list">
                        {trend.keywords.slice(0, 5).map((keyword, index) => (
                            <span key={index} className="keyword-tag">
                                {keyword}
                            </span>
                        ))}
                        {trend.keywords.length > 5 && (
                            <span className="keyword-more">
                                +{trend.keywords.length - 5} more
                            </span>
                        )}
                    </div>
                </div>
            )}

            {trend.category && (
                <div className="trend-category">
                    <span className={`category-badge category-${trend.category.toLowerCase()}`}>
                        {trend.category}
                    </span>
                </div>
            )}

            {trend.ai_analysis && (
                <div className="trend-analysis">
                    <h4>AI Analysis</h4>
                    <div className="analysis-scores">
                        <div className="score-item">
                            <span>Viral Potential</span>
                            <span className="score">{trend.ai_analysis.viral_potential}/10</span>
                        </div>
                        <div className="score-item">
                            <span>Competition</span>
                            <span className="score">{trend.ai_analysis.competition_level}/10</span>
                        </div>
                        <div className="score-item">
                            <span>Monetization</span>
                            <span className="score">{trend.ai_analysis.monetization_score}/10</span>
                        </div>
                    </div>
                    {trend.ai_analysis.content_angles && (
                        <div className="content-suggestions">
                            <span className="suggestions-label">Suggested Angles:</span>
                            <ul>
                                {trend.ai_analysis.content_angles.slice(0, 3).map((angle, index) => (
                                    <li key={index}>{angle}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            )}

            <div className="trend-actions">
                {!trend.ai_analysis && (
                    <button 
                        className="analyze-button"
                        onClick={() => onAnalyze(trend.id)}
                    >
                        🤖 Analyze with AI
                    </button>
                )}
                
                {trend.ai_analysis && (
                    <button 
                        className="create-content-button"
                        onClick={() => onCreateContent(trend)}
                    >
                        ✨ Create Content
                    </button>
                )}
                
                <button className="view-details-button">
                    👁️ View Details
                </button>
            </div>

            {trend.opportunities_count > 0 && (
                <div className="opportunities-indicator">
                    <span>
                        💡 {trend.opportunities_count} content opportunities created
                    </span>
                </div>
            )}
        </div>
    );
};

export default TrendCard;