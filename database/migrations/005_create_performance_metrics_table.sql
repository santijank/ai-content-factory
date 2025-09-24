-- Migration 005: Create performance_metrics table
-- This table tracks performance data for uploaded content across platforms

CREATE TABLE performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    upload_id UUID NOT NULL REFERENCES uploads(id) ON DELETE CASCADE,
    
    -- Basic engagement metrics
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    dislikes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    saves INTEGER DEFAULT 0,
    
    -- Advanced engagement metrics
    engagement_rate FLOAT DEFAULT 0.0,
    watch_time_seconds BIGINT DEFAULT 0,
    avg_view_duration_seconds INTEGER DEFAULT 0,
    click_through_rate FLOAT DEFAULT 0.0,
    
    -- Audience metrics
    subscriber_gain INTEGER DEFAULT 0,
    follower_gain INTEGER DEFAULT 0,
    unique_viewers INTEGER DEFAULT 0,
    returning_viewers INTEGER DEFAULT 0,
    
    -- Revenue metrics
    revenue DECIMAL(10,2) DEFAULT 0.00,
    ad_revenue DECIMAL(10,2) DEFAULT 0.00,
    sponsored_revenue DECIMAL(10,2) DEFAULT 0.00,
    merchandise_revenue DECIMAL(10,2) DEFAULT 0.00,
    
    -- Platform-specific metrics (stored as JSONB for flexibility)
    platform_specific_metrics JSONB DEFAULT '{}',
    
    -- Demographics and geographic data
    demographics JSONB DEFAULT '{}', -- Age, gender breakdown
    geographic_data JSONB DEFAULT '{}', -- Country, city breakdown
    device_data JSONB DEFAULT '{}', -- Mobile, desktop, tablet breakdown
    traffic_sources JSONB DEFAULT '{}', -- How viewers found the content
    
    -- Time-based analysis
    hourly_data JSONB DEFAULT '{}', -- Performance by hour
    daily_data JSONB DEFAULT '{}', -- Performance by day
    
    -- Comparative metrics
    industry_benchmark_percentile INTEGER, -- How this performs vs industry average
    channel_benchmark_percentile INTEGER, -- How this performs vs channel average
    
    -- Quality indicators
    retention_rate FLOAT DEFAULT 0.0, -- Percentage of video watched on average
    completion_rate FLOAT DEFAULT 0.0, -- Percentage who watched to the end
    replay_rate FLOAT DEFAULT 0.0, -- Percentage who replayed
    
    -- Data collection metadata
    measured_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_source VARCHAR(50) DEFAULT 'api', -- api, scraping, manual
    collection_method VARCHAR(50) DEFAULT 'automatic',
    data_freshness_minutes INTEGER DEFAULT 0, -- How old the data is
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}',
    
    -- Constraints
    CONSTRAINT performance_views_check CHECK (views >= 0),
    CONSTRAINT performance_likes_check CHECK (likes >= 0),
    CONSTRAINT performance_dislikes_check CHECK (dislikes >= 0),
    CONSTRAINT performance_comments_check CHECK (comments >= 0),
    CONSTRAINT performance_shares_check CHECK (shares >= 0),
    CONSTRAINT performance_saves_check CHECK (saves >= 0),
    CONSTRAINT performance_engagement_rate_check CHECK (engagement_rate >= 0 AND engagement_rate <= 100),
    CONSTRAINT performance_watch_time_check CHECK (watch_time_seconds >= 0),
    CONSTRAINT performance_avg_duration_check CHECK (avg_view_duration_seconds >= 0),
    CONSTRAINT performance_ctr_check CHECK (click_through_rate >= 0 AND click_through_rate <= 100),
    CONSTRAINT performance_revenue_check CHECK (revenue >= 0),
    CONSTRAINT performance_ad_revenue_check CHECK (ad_revenue >= 0),
    CONSTRAINT performance_retention_rate_check CHECK (retention_rate >= 0 AND retention_rate <= 100),
    CONSTRAINT performance_completion_rate_check CHECK (completion_rate >= 0 AND completion_rate <= 100),
    CONSTRAINT performance_replay_rate_check CHECK (replay_rate >= 0 AND replay_rate <= 100),
    CONSTRAINT performance_industry_percentile_check CHECK (industry_benchmark_percentile IS NULL OR (industry_benchmark_percentile >= 0 AND industry_benchmark_percentile <= 100)),
    CONSTRAINT performance_channel_percentile_check CHECK (channel_benchmark_percentile IS NULL OR (channel_benchmark_percentile >= 0 AND channel_benchmark_percentile <= 100)),
    CONSTRAINT performance_data_source_check CHECK (data_source IN ('api', 'scraping', 'manual', 'webhook')),
    CONSTRAINT performance_collection_method_check CHECK (collection_method IN ('automatic', 'manual', 'scheduled', 'realtime'))
);

-- Create indexes for performance
CREATE INDEX idx_performance_upload_id ON performance_metrics(upload_id);
CREATE INDEX idx_performance_measured_at ON performance_metrics(measured_at DESC);
CREATE INDEX idx_performance_views ON performance_metrics(views DESC);
CREATE INDEX idx_performance_engagement_rate ON performance_metrics(engagement_rate DESC);
CREATE INDEX idx_performance_revenue ON performance_metrics(revenue DESC);
CREATE INDEX idx_performance_created_at ON performance_metrics(created_at DESC);

-- Composite indexes for common queries
CREATE INDEX idx_performance_upload_measured ON performance_metrics(upload_id, measured_at DESC);
CREATE INDEX idx_performance_views_revenue ON performance_metrics(views DESC, revenue DESC);

-- Index for latest metrics per upload
CREATE UNIQUE INDEX idx_performance_latest ON performance_metrics(upload_id, measured_at DESC);

-- GIN indexes for JSONB columns
CREATE INDEX idx_performance_platform_metrics_gin ON performance_metrics USING gin(platform_specific_metrics);
CREATE INDEX idx_performance_demographics_gin ON performance_metrics USING gin(demographics);
CREATE INDEX idx_performance_geographic_gin ON performance_metrics USING gin(geographic_data);
CREATE INDEX idx_performance_metadata_gin ON performance_metrics USING gin(metadata);

-- Partial index for recent high-performing content
CREATE INDEX idx_performance_recent_high ON performance_metrics(views DESC, engagement_rate DESC)
WHERE measured_at >= CURRENT_TIMESTAMP - INTERVAL '7 days' AND views > 1000;

-- Trigger to update updated_at timestamp
CREATE TRIGGER performance_metrics_update_updated_at
    BEFORE UPDATE ON performance_metrics
    FOR EACH ROW
    EXECUTE FUNCTION update_trends_updated_at();

-- Add comments for documentation
COMMENT ON TABLE performance_metrics IS 'Stores performance and analytics data for uploaded content';
COMMENT ON COLUMN performance_metrics.upload_id IS 'Reference to the upload being tracked';
COMMENT ON COLUMN performance_metrics.engagement_rate IS 'Overall engagement rate percentage';
COMMENT ON COLUMN performance_metrics.platform_specific_metrics IS 'Platform-unique metrics (YouTube retention graphs, TikTok shares, etc.)';
COMMENT ON COLUMN performance_metrics.demographics IS 'Audience demographics breakdown';
COMMENT ON COLUMN performance_metrics.geographic_data IS 'Geographic distribution of viewers';
COMMENT ON COLUMN performance_metrics.measured_at IS 'When these metrics were collected';
COMMENT ON COLUMN performance_metrics.industry_benchmark_percentile IS 'Performance percentile vs industry average';
COMMENT ON COLUMN performance_metrics.channel_benchmark_percentile IS 'Performance percentile vs channel average';

-- Create a comprehensive analytics view
CREATE VIEW content_performance_analytics AS
SELECT 
    pm.id as metric_id,
    pm.upload_id,
    u.platform,
    u.platform_title,
    u.published_at,
    -- Content context
    ci.title as content_title,
    ci.content_type,
    ci.production_quality_tier,
    ci.total_production_cost,
    -- Opportunity context  
    co.priority_score,
    co.estimated_views,
    co.estimated_roi,
    co.competition_level,
    -- Trend context
    t.topic as trend_topic,
    t.source as trend_source,
    t.popularity_score as trend_popularity,
    t.category as trend_category,
    -- Performance metrics
    pm.views,
    pm.likes,
    pm.comments,
    pm.shares,
    pm.engagement_rate,
    pm.watch_time_seconds,
    pm.avg_view_duration_seconds,
    pm.revenue,
    pm.retention_rate,
    pm.completion_rate,
    pm.measured_at,
    -- Calculated metrics
    CASE WHEN pm.views > 0 THEN pm.revenue / pm.views * 1000 ELSE 0 END as revenue_per_mille,
    CASE WHEN ci.total_production_cost > 0 THEN pm.revenue / ci.total_production_cost ELSE 0 END as actual_roi,
    pm.views::FLOAT / NULLIF(co.estimated_views, 0) as views_vs_estimate_ratio,
    EXTRACT(EPOCH FROM (pm.measured_at - u.published_at)) / 86400 as days_since_publish
FROM performance_metrics pm
JOIN uploads u ON pm.upload_id = u.id
JOIN content_items ci ON u.content_id = ci.id
JOIN content_opportunities co ON ci.opportunity_id = co.id
JOIN trends t ON co.trend_id = t.id
ORDER BY pm.measured_at DESC;

COMMENT ON VIEW content_performance_analytics IS 'Comprehensive view combining performance metrics with content, opportunity, and trend context';

-- Function to get latest performance metrics for uploads
CREATE OR REPLACE FUNCTION get_latest_performance_metrics(
    platform_filter VARCHAR DEFAULT NULL,
    hours_back INTEGER DEFAULT 24,
    min_views INTEGER DEFAULT 0,
    limit_count INTEGER DEFAULT 50
)
RETURNS TABLE (
    upload_id UUID,
    platform VARCHAR,
    platform_title VARCHAR,
    views INTEGER,
    engagement_rate FLOAT,
    revenue DECIMAL,
    measured_at TIMESTAMP WITH TIME ZONE,
    content_title VARCHAR,
    trend_topic VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT ON (pm.upload_id)
        pm.upload_id,
        u.platform,
        u.platform_title,
        pm.views,
        pm.engagement_rate,
        pm.revenue,
        pm.measured_at,
        ci.title,
        t.topic
    FROM performance_metrics pm
    JOIN uploads u ON pm.upload_id = u.id
    JOIN content_items ci ON u.content_id = ci.id
    JOIN content_opportunities co ON ci.opportunity_id = co.id
    JOIN trends t ON co.trend_id = t.id
    WHERE 
        pm.measured_at >= CURRENT_TIMESTAMP - (hours_back || ' hours')::INTERVAL
        AND pm.views >= min_views
        AND (platform_filter IS NULL OR u.platform = platform_filter)
    ORDER BY pm.upload_id, pm.measured_at DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate ROI and performance summary
CREATE OR REPLACE FUNCTION calculate_performance_summary(
    days_back INTEGER DEFAULT 7,
    platform_filter VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    total_content INTEGER,
    total_views BIGINT,
    total_revenue DECIMAL,
    avg_engagement_rate FLOAT,
    avg_roi FLOAT,
    best_performing_title VARCHAR,
    best_performing_views INTEGER,
    worst_performing_title VARCHAR,
    worst_performing_views INTEGER,
    platform_breakdown JSONB,
    category_breakdown JSONB
) AS $$
BEGIN
    RETURN QUERY
    WITH latest_metrics AS (
        SELECT DISTINCT ON (pm.upload_id)
            pm.upload_id,
            pm.views,
            pm.engagement_rate,
            pm.revenue,
            u.platform,
            ci.title,
            ci.total_production_cost,
            t.category
        FROM performance_metrics pm
        JOIN uploads u ON pm.upload_id = u.id
        JOIN content_items ci ON u.content_id = ci.id
        JOIN content_opportunities co ON ci.opportunity_id = co.id
        JOIN trends t ON co.trend_id = t.id
        WHERE 
            pm.measured_at >= CURRENT_TIMESTAMP - (days_back || ' days')::INTERVAL
            AND (platform_filter IS NULL OR u.platform = platform_filter)
        ORDER BY pm.upload_id, pm.measured_at DESC
    ),
    best_worst AS (
        SELECT 
            MAX(views) as max_views,
            MIN(views) as min_views
        FROM latest_metrics
    )
    SELECT 
        COUNT(*)::INTEGER as total_content,
        SUM(lm.views) as total_views,
        SUM(lm.revenue) as total_revenue,
        AVG(lm.engagement_rate) as avg_engagement_rate,
        AVG(CASE WHEN lm.total_production_cost > 0 THEN lm.revenue / lm.total_production_cost ELSE 0 END) as avg_roi,
        (SELECT title FROM latest_metrics WHERE views = (SELECT max_views FROM best_worst) LIMIT 1) as best_performing_title,
        (SELECT max_views FROM best_worst)::INTEGER as best_performing_views,
        (SELECT title FROM latest_metrics WHERE views = (SELECT min_views FROM best_worst) LIMIT 1) as worst_performing_title,
        (SELECT min_views FROM best_worst)::INTEGER as worst_performing_views,
        json_build_object(
            'youtube', COUNT(*) FILTER (WHERE platform = 'youtube'),
            'tiktok', COUNT(*) FILTER (WHERE platform = 'tiktok'),
            'instagram', COUNT(*) FILTER (WHERE platform = 'instagram'),
            'facebook', COUNT(*) FILTER (WHERE platform = 'facebook')
        ) as platform_breakdown,
        json_build_object(
            'technology', COUNT(*) FILTER (WHERE category = 'technology'),
            'entertainment', COUNT(*) FILTER (WHERE category = 'entertainment'),
            'gaming', COUNT(*) FILTER (WHERE category = 'gaming'),
            'music', COUNT(*) FILTER (WHERE category = 'music'),
            'other', COUNT(*) FILTER (WHERE category = 'other')
        ) as category_breakdown
    FROM latest_metrics lm;
END;
$$ LANGUAGE plpgsql;

-- Function to track performance trends over time
CREATE OR REPLACE FUNCTION get_performance_trends(
    upload_id_param UUID,
    days_back INTEGER DEFAULT 30
)
RETURNS TABLE (
    measured_date DATE,
    views INTEGER,
    engagement_rate FLOAT,
    revenue DECIMAL,
    daily_view_growth INTEGER,
    daily_revenue_growth DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pm.measured_at::DATE as measured_date,
        pm.views,
        pm.engagement_rate,
        pm.revenue,
        pm.views - LAG(pm.views) OVER (ORDER BY pm.measured_at::DATE) as daily_view_growth,
        pm.revenue - LAG(pm.revenue) OVER (ORDER BY pm.measured_at::DATE) as daily_revenue_growth
    FROM performance_metrics pm
    WHERE 
        pm.upload_id = upload_id_param
        AND pm.measured_at >= CURRENT_TIMESTAMP - (days_back || ' days')::INTERVAL
    ORDER BY pm.measured_at::DATE;
END;
$$ LANGUAGE plpgsql;

-- Function to identify viral content
CREATE OR REPLACE FUNCTION identify_viral_content(
    min_views INTEGER DEFAULT 10000,
    min_engagement_rate FLOAT DEFAULT 5.0,
    days_back INTEGER DEFAULT 7
)
RETURNS TABLE (
    upload_id UUID,
    platform VARCHAR,
    content_title VARCHAR,
    trend_topic VARCHAR,
    views INTEGER,
    engagement_rate FLOAT,
    revenue DECIMAL,
    viral_score FLOAT,
    published_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT ON (pm.upload_id)
        pm.upload_id,
        u.platform,
        ci.title,
        t.topic,
        pm.views,
        pm.engagement_rate,
        pm.revenue,
        -- Calculate viral score based on views, engagement, and growth rate
        (pm.views::FLOAT / 1000 * 0.4) + 
        (pm.engagement_rate * 0.3) + 
        (CASE WHEN u.published_at IS NOT NULL THEN
            pm.views::FLOAT / GREATEST(1, EXTRACT(EPOCH FROM (pm.measured_at - u.published_at)) / 3600) * 0.3
        ELSE 0 END) as viral_score,
        u.published_at
    FROM performance_metrics pm
    JOIN uploads u ON pm.upload_id = u.id
    JOIN content_items ci ON u.content_id = ci.id
    JOIN content_opportunities co ON ci.opportunity_id = co.id
    JOIN trends t ON co.trend_id = t.id
    WHERE 
        pm.measured_at >= CURRENT_TIMESTAMP - (days_back || ' days')::INTERVAL
        AND pm.views >= min_views
        AND pm.engagement_rate >= min_engagement_rate
    ORDER BY pm.upload_id, pm.measured_at DESC
    HAVING (pm.views::FLOAT / 1000 * 0.4) + (pm.engagement_rate * 0.3) + 
           (CASE WHEN u.published_at IS NOT NULL THEN
                pm.views::FLOAT / GREATEST(1, EXTRACT(EPOCH FROM (pm.measured_at - u.published_at)) / 3600) * 0.3
            ELSE 0 END) >= 50 -- Viral score threshold
    ORDER BY viral_score DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to clean up old performance metrics
CREATE OR REPLACE FUNCTION cleanup_old_performance_metrics(retention_days INTEGER DEFAULT 365)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Keep only the latest metric per upload per day for old data
    WITH metrics_to_keep AS (
        SELECT DISTINCT ON (upload_id, measured_at::DATE) 
            id
        FROM performance_metrics 
        WHERE measured_at < CURRENT_TIMESTAMP - (retention_days || ' days')::INTERVAL
        ORDER BY upload_id, measured_at::DATE, measured_at DESC
    )
    DELETE FROM performance_metrics 
    WHERE 
        measured_at < CURRENT_TIMESTAMP - (retention_days || ' days')::INTERVAL
        AND id NOT IN (SELECT id FROM metrics_to_keep);
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;