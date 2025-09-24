import React, { useState } from 'react';
import '../styles/ContentCard.css';

const ContentCard = ({ content, onClick, onPublish, onEdit, onDelete }) => {
    const [isPublishing, setIsPublishing] = useState(false);

    const getStatusIcon = (status) => {
        const icons = {
            'draft': '📝',
            'generating': '🔄',
            'ready': '✅',
            'published': '🌐',
            'failed': '❌',
            'scheduled': '⏰'
        };
        return icons[status] || '❓';
    };

    const getStatusClass = (status) => {
        return `status-${status}`;
    };

    const formatCurrency = (amount) => {
        return new Intl.NumberFormat('th-TH', {
            style: 'currency',
            currency: 'THB'
        }).format(amount || 0);
    };

    const formatTimeAgo = (timestamp) => {
        const now = new Date();
        const contentTime = new Date(timestamp);
        const diffInHours = Math.floor((now - contentTime) / (1000 * 60 * 60));
        
        if (diffInHours < 1) return 'Just now';
        if (diffInHours < 24) return `${diffInHours}h ago`;
        const diffInDays = Math.floor(diffInHours / 24);
        return `${diffInDays}d ago`;
    };

    const handlePublish = async (platform) => {
        setIsPublishing(true);
        try {
            await onPublish(content.id, platform);
        } finally {
            setIsPublishing(false);
        }
    };

    const getPlatformIcon = (platform) => {
        const icons = {
            'youtube': '📺',
            'tiktok': '🎵',
            'instagram': '📷',
            'facebook': '👥',
            'twitter': '🐦'
        };
        return icons[platform] || '🌐';
    };

    const getThumbnailUrl = (content) => {
        if (content.assets && content.assets.thumbnail) {
            return content.assets.thumbnail;
        }
        return '/images/default-thumbnail.jpg';
    };

    const getPerformanceMetrics = (content) => {
        if (!content.performance_data) return null;
        
        const totalViews = Object.values(content.performance_data).reduce(
            (sum, platformData) => sum + (platformData.views || 0), 0
        );
        const totalLikes = Object.values(content.performance_data).reduce(
            (sum, platformData) => sum + (platformData.likes || 0), 0
        );
        const totalRevenue = Object.values(content.performance_data).reduce(
            (sum, platformData) => sum + (platformData.revenue || 0), 0
        );
        
        return { totalViews, totalLikes, totalRevenue };
    };

    const performance = getPerformanceMetrics(content);

    return (
        <div className={`content-card ${getStatusClass(content.status)}`} onClick={onClick}>
            <div className="content-thumbnail">
                <img 
                    src={getThumbnailUrl(content)} 
                    alt={content.title}
                    onError={(e) => {
                        e.target.src = '/images/default-thumbnail.jpg';
                    }}
                />
                <div className="content-status-overlay">
                    <span className={`status-badge ${getStatusClass(content.status)}`}>
                        {getStatusIcon(content.status)} {content.status}
                    </span>
                </div>
                {content.duration && (
                    <div className="duration-badge">
                        {content.duration}s
                    </div>
                )}
            </div>

            <div className="content-info">
                <div className="content-header">
                    <h3 className="content-title">{content.title}</h3>
                    <span className="content-created">
                        {formatTimeAgo(content.created_at)}
                    </span>
                </div>

                <div className="content-description">
                    <p>{content.description}</p>
                </div>

                <div className="content-platforms">
                    <span className="platforms-label">Platforms:</span>
                    <div className="platforms-list">
                        {content.target_platforms?.map(platform => (
                            <span key={platform} className={`platform-badge platform-${platform}`}>
                                {getPlatformIcon(platform)} {platform}
                            </span>
                        ))}
                    </div>
                </div>

                {content.tags && content.tags.length > 0 && (
                    <div className="content-tags">
                        {content.tags.slice(0, 3).map((tag, index) => (
                            <span key={index} className="content-tag">
                                #{tag}
                            </span>
                        ))}
                        {content.tags.length > 3 && (
                            <span className="more-tags">
                                +{content.tags.length - 3} more
                            </span>
                        )}
                    </div>
                )}

                <div className="content-metrics">
                    <div className="cost-info">
                        <span className="cost-label">Cost:</span>
                        <span className="cost-value">
                            {formatCurrency(content.production_cost)}
                        </span>
                    </div>
                    
                    {content.estimated_revenue && (
                        <div className="revenue-info">
                            <span className="revenue-label">Est. Revenue:</span>
                            <span className="revenue-value">
                                {formatCurrency(content.estimated_revenue)}
                            </span>
                        </div>
                    )}
                </div>

                {performance && (
                    <div className="performance-metrics">
                        <div className="metric-item">
                            <span className="metric-icon">👁️</span>
                            <span className="metric-value">
                                {performance.totalViews.toLocaleString()}
                            </span>
                        </div>
                        <div className="metric-item">
                            <span className="metric-icon">❤️</span>
                            <span className="metric-value">
                                {performance.totalLikes.toLocaleString()}
                            </span>
                        </div>
                        <div className="metric-item">
                            <span className="metric-icon">💰</span>
                            <span className="metric-value">
                                {formatCurrency(performance.totalRevenue)}
                            </span>
                        </div>
                    </div>
                )}

                <div className="content-actions" onClick={(e) => e.stopPropagation()}>
                    {content.status === 'ready' && (
                        <div className="publish-actions">
                            <button 
                                className="publish-all-button"
                                onClick={() => handlePublish('all')}
                                disabled={isPublishing}
                            >
                                {isPublishing ? (
                                    <>
                                        <div className="spinner small"></div>
                                        Publishing...
                                    </>
                                ) : (
                                    <>
                                        🚀 Publish All
                                    </>
                                )}
                            </button>
                            
                            <div className="platform-publish-buttons">
                                {content.target_platforms?.map(platform => (
                                    <button
                                        key={platform}
                                        className={`platform-publish-button platform-${platform}`}
                                        onClick={() => handlePublish(platform)}
                                        disabled={isPublishing}
                                        title={`Publish to ${platform}`}
                                    >
                                        {getPlatformIcon(platform)}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    <div className="secondary-actions">
                        {content.status === 'draft' && (
                            <button 
                                className="edit-button"
                                onClick={() => onEdit(content)}
                                title="Edit content"
                            >
                                ✏️ Edit
                            </button>
                        )}
                        
                        {content.assets && content.assets.video_url && (
                            <button 
                                className="preview-button"
                                onClick={() => window.open(content.assets.video_url, '_blank')}
                                title="Preview video"
                            >
                                👁️ Preview
                            </button>
                        )}
                        
                        {content.status === 'published' && content.upload_urls && (
                            <div className="view-links">
                                {Object.entries(content.upload_urls).map(([platform, url]) => (
                                    <button
                                        key={platform}
                                        className={`view-link-button platform-${platform}`}
                                        onClick={() => window.open(url, '_blank')}
                                        title={`View on ${platform}`}
                                    >
                                        {getPlatformIcon(platform)}
                                    </button>
                                ))}
                            </div>
                        )}
                        
                        <button 
                            className="download-button"
                            onClick={() => {
                                // Download logic here
                                alert('Download feature coming soon!');
                            }}
                            title="Download content"
                        >
                            📥
                        </button>
                        
                        <button 
                            className="delete-button"
                            onClick={() => {
                                if (window.confirm('Are you sure you want to delete this content?')) {
                                    onDelete(content.id);
                                }
                            }}
                            title="Delete content"
                        >
                            🗑️
                        </button>
                    </div>
                </div>

                {content.content_plan && (
                    <div className="content-plan-preview">
                        <h4>Content Plan</h4>
                        <div className="plan-details">
                            {content.content_plan.hook && (
                                <div className="plan-item">
                                    <span className="plan-label">Hook:</span>
                                    <span className="plan-value">{content.content_plan.hook}</span>
                                </div>
                            )}
                            {content.content_plan.style && (
                                <div className="plan-item">
                                    <span className="plan-label">Style:</span>
                                    <span className="plan-value">{content.content_plan.style}</span>
                                </div>
                            )}
                            {content.content_plan.estimated_time && (
                                <div className="plan-item">
                                    <span className="plan-label">Production Time:</span>
                                    <span className="plan-value">{content.content_plan.estimated_time} min</span>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>

            {content.status === 'generating' && (
                <div className="generation-progress">
                    <div className="progress-bar">
                        <div className="progress-fill"></div>
                    </div>
                    <span className="progress-text">Generating content...</span>
                </div>
            )}

            {content.ai_score && (
                <div className="ai-score-badge">
                    <span className="score-label">AI Score:</span>
                    <span className="score-value">{content.ai_score}/10</span>
                </div>
            )}
        </div>
    );
};

export default ContentCard;