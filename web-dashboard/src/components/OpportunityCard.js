import React, { useState } from 'react';
import '../styles/OpportunityCard.css';

const OpportunityCard = ({ opportunity, onGenerate, onEdit, onDelete }) => {
    const [isExpanded, setIsExpanded] = useState(false);
    const [isGenerating, setIsGenerating] = useState(false);

    const getROIClass = (roi) => {
        if (roi >= 3.0) return 'roi-excellent';
        if (roi >= 2.0) return 'roi-good';
        if (roi >= 1.5) return 'roi-fair';
        return 'roi-poor';
    };

    const getCompetitionClass = (level) => {
        const classes = {
            'low': 'competition-low',
            'medium': 'competition-medium',
            'high': 'competition-high'
        };
        return classes[level] || 'competition-unknown';
    };

    const getPriorityClass = (score) => {
        if (score >= 8) return 'priority-high';
        if (score >= 6) return 'priority-medium';
        return 'priority-low';
    };

    const formatCurrency = (amount) => {
        return new Intl.NumberFormat('th-TH', {
            style: 'currency',
            currency: 'THB'
        }).format(amount || 0);
    };

    const handleGenerate = async () => {
        setIsGenerating(true);
        try {
            await onGenerate(opportunity.id);
        } finally {
            setIsGenerating(false);
        }
    };

    const formatTimeAgo = (timestamp) => {
        const now = new Date();
        const oppTime = new Date(timestamp);
        const diffInHours = Math.floor((now - oppTime) / (1000 * 60 * 60));
        
        if (diffInHours < 1) return 'Just now';
        if (diffInHours < 24) return `${diffInHours}h ago`;
        const diffInDays = Math.floor(diffInHours / 24);
        return `${diffInDays}d ago`;
    };

    return (
        <div className={`opportunity-card ${opportunity.status}`}>
            <div className="opportunity-header">
                <div className="opportunity-title">
                    <h3>{opportunity.title || opportunity.suggested_angle}</h3>
                    <div className="opportunity-meta">
                        <span className="trend-topic">
                            📈 {opportunity.trend?.topic || 'Unknown Trend'}
                        </span>
                        <span className="created-time">
                            {formatTimeAgo(opportunity.created_at)}
                        </span>
                    </div>
                </div>
                
                <div className="opportunity-priority">
                    <span className={`priority-badge ${getPriorityClass(opportunity.priority_score)}`}>
                        Priority: {opportunity.priority_score?.toFixed(1)}
                    </span>
                </div>
            </div>

            <div className="opportunity-metrics">
                <div className="metric-group">
                    <div className="metric-item">
                        <span className="metric-label">Estimated Views</span>
                        <span className="metric-value">
                            {opportunity.estimated_views?.toLocaleString() || '0'}
                        </span>
                    </div>
                    
                    <div className="metric-item">
                        <span className="metric-label">ROI</span>
                        <span className={`metric-value ${getROIClass(opportunity.estimated_roi)}`}>
                            {opportunity.estimated_roi?.toFixed(2)}x
                        </span>
                    </div>
                </div>

                <div className="metric-group">
                    <div className="metric-item">
                        <span className="metric-label">Production Cost</span>
                        <span className="metric-value">
                            {formatCurrency(opportunity.production_cost)}
                        </span>
                    </div>
                    
                    <div className="metric-item">
                        <span className="metric-label">Competition</span>
                        <span className={`metric-value ${getCompetitionClass(opportunity.competition_level)}`}>
                            {opportunity.competition_level}
                        </span>
                    </div>
                </div>
            </div>

            <div className="opportunity-description">
                <p className={isExpanded ? 'expanded' : 'collapsed'}>
                    {opportunity.description || opportunity.suggested_angle}
                </p>
                {opportunity.description && opportunity.description.length > 150 && (
                    <button 
                        className="expand-button"
                        onClick={() => setIsExpanded(!isExpanded)}
                    >
                        {isExpanded ? 'Show Less' : 'Show More'}
                    </button>
                )}
            </div>

            {opportunity.content_ideas && opportunity.content_ideas.length > 0 && (
                <div className="content-ideas">
                    <h4>Content Ideas:</h4>
                    <ul>
                        {opportunity.content_ideas.slice(0, isExpanded ? -1 : 3).map((idea, index) => (
                            <li key={index}>{idea}</li>
                        ))}
                    </ul>
                    {opportunity.content_ideas.length > 3 && !isExpanded && (
                        <button 
                            className="show-more-ideas"
                            onClick={() => setIsExpanded(true)}
                        >
                            +{opportunity.content_ideas.length - 3} more ideas
                        </button>
                    )}
                </div>
            )}

            {opportunity.target_platforms && (
                <div className="target-platforms">
                    <span className="platforms-label">Target Platforms:</span>
                    <div className="platforms-list">
                        {opportunity.target_platforms.map(platform => (
                            <span key={platform} className={`platform-badge platform-${platform}`}>
                                {platform}
                            </span>
                        ))}
                    </div>
                </div>
            )}

            <div className="opportunity-tags">
                {opportunity.trend?.category && (
                    <span className="tag category-tag">
                        {opportunity.trend.category}
                    </span>
                )}
                
                {opportunity.estimated_roi >= 3.0 && (
                    <span className="tag high-roi-tag">High ROI</span>
                )}
                
                {opportunity.competition_level === 'low' && (
                    <span className="tag low-competition-tag">Low Competition</span>
                )}
                
                {opportunity.production_cost < 50 && (
                    <span className="tag budget-friendly-tag">Budget Friendly</span>
                )}
                
                {opportunity.estimated_production_time < 60 && (
                    <span className="tag quick-win-tag">Quick Win</span>
                )}
            </div>

            <div className="opportunity-actions">
                <div className="primary-actions">
                    <button 
                        className={`generate-button ${isGenerating ? 'generating' : ''}`}
                        onClick={handleGenerate}
                        disabled={isGenerating || opportunity.status === 'generating'}
                    >
                        {isGenerating ? (
                            <>
                                <div className="spinner small"></div>
                                Generating...
                            </>
                        ) : (
                            <>
                                🚀 Generate Content
                            </>
                        )}
                    </button>
                </div>
                
                <div className="secondary-actions">
                    <button 
                        className="edit-button"
                        onClick={() => onEdit(opportunity)}
                        title="Edit opportunity"
                    >
                        ✏️
                    </button>
                    
                    <button 
                        className="delete-button"
                        onClick={() => onDelete(opportunity.id)}
                        title="Delete opportunity"
                    >
                        🗑️
                    </button>
                    
                    <button 
                        className="share-button"
                        onClick={() => navigator.share({
                            title: opportunity.title,
                            text: opportunity.description,
                            url: window.location.href
                        })}
                        title="Share opportunity"
                    >
                        📤
                    </button>
                </div>
            </div>

            {opportunity.ai_analysis && (
                <div className="ai-insights">
                    <h4>AI Insights</h4>
                    <div className="insights-grid">
                        <div className="insight-item">
                            <span className="insight-label">Viral Score</span>
                            <span className="insight-value">
                                {opportunity.ai_analysis.viral_potential}/10
                            </span>
                        </div>
                        <div className="insight-item">
                            <span className="insight-label">Audience Interest</span>
                            <span className="insight-value">
                                {opportunity.ai_analysis.audience_interest}/10
                            </span>
                        </div>
                        <div className="insight-item">
                            <span className="insight-label">Trend Momentum</span>
                            <span className="insight-value">
                                {opportunity.ai_analysis.trend_momentum}/10
                            </span>
                        </div>
                    </div>
                </div>
            )}

            {opportunity.status && (
                <div className="opportunity-status">
                    <span className={`status-indicator status-${opportunity.status}`}>
                        {opportunity.status === 'pending' && '⏳ Pending'}
                        {opportunity.status === 'selected' && '✅ Selected'}
                        {opportunity.status === 'generating' && '🔄 Generating'}
                        {opportunity.status === 'completed' && '✨ Completed'}
                        {opportunity.status === 'failed' && '❌ Failed'}
                    </span>
                </div>
            )}
        </div>
    );
};

export default OpportunityCard;