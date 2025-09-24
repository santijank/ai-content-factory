-- Migration 001: Create trends table
-- This table stores trending topics collected from various sources

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

CREATE TABLE trends (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source VARCHAR(50) NOT NULL,
    topic VARCHAR(500) NOT NULL,
    keywords JSONB DEFAULT '[]'::jsonb,
    popularity_score FLOAT NOT NULL DEFAULT 0.0,
    growth_rate FLOAT,
    category VARCHAR(100) DEFAULT 'other',
    region VARCHAR(50) DEFAULT 'global',
    collected_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    raw_data JSONB DEFAULT '{}'::jsonb,
    
    -- Constraints
    CONSTRAINT trends_popularity_score_check CHECK (popularity_score >= 0 AND popularity_score <= 100),
    CONSTRAINT trends_growth_rate_check CHECK (growth_rate IS NULL OR (growth_rate >= -100 AND growth_rate <= 1000)),
    CONSTRAINT trends_source_check CHECK (source IN ('youtube', 'google', 'twitter', 'reddit', 'tiktok', 'other')),
    CONSTRAINT trends_category_check CHECK (category IN (
        'technology', 'entertainment', 'music', 'gaming', 'sports', 
        'news', 'health', 'business', 'education', 'lifestyle', 'other'
    ))
);

-- Create indexes for performance
CREATE INDEX idx_trends_source ON trends(source);
CREATE INDEX idx_trends_collected_at ON trends(collected_at DESC);
CREATE INDEX idx_trends_popularity_score ON trends(popularity_score DESC);
CREATE INDEX idx_trends_category ON trends(category);
CREATE INDEX idx_trends_region ON trends(region);

-- Full-text search index for topics
CREATE INDEX idx_trends_topic_gin ON trends USING gin(to_tsvector('english', topic));

-- Composite index for common queries
CREATE INDEX idx_trends_source_collected_at ON trends(source, collected_at DESC);
CREATE INDEX idx_trends_category_popularity ON trends(category, popularity_score DESC);

-- Partial index for recent trends (last 7 days)
CREATE INDEX idx_trends_recent ON trends(collected_at DESC, popularity_score DESC)
WHERE collected_at >= CURRENT_TIMESTAMP - INTERVAL '7 days';

-- GIN index for keywords array
CREATE INDEX idx_trends_keywords_gin ON trends USING gin(keywords);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_trends_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trends_update_updated_at
    BEFORE UPDATE ON trends
    FOR EACH ROW
    EXECUTE FUNCTION update_trends_updated_at();

-- Add comments for documentation
COMMENT ON TABLE trends IS 'Stores trending topics collected from various social media platforms and search engines';
COMMENT ON COLUMN trends.id IS 'Unique identifier for each trend record';
COMMENT ON COLUMN trends.source IS 'Platform where the trend was collected (youtube, google, twitter, reddit, etc.)';
COMMENT ON COLUMN trends.topic IS 'The trending topic or title';
COMMENT ON COLUMN trends.keywords IS 'Array of keywords extracted from the topic (stored as JSON)';
COMMENT ON COLUMN trends.popularity_score IS 'Calculated popularity score (0-100 scale)';
COMMENT ON COLUMN trends.growth_rate IS 'Estimated growth rate percentage (nullable)';
COMMENT ON COLUMN trends.category IS 'Categorization of the trend content';
COMMENT ON COLUMN trends.region IS 'Geographic region where trend was collected';
COMMENT ON COLUMN trends.collected_at IS 'Timestamp when the trend was collected';
COMMENT ON COLUMN trends.raw_data IS 'Original data from the source API (stored as JSON)';

-- Create a view for recent high-quality trends
CREATE VIEW recent_quality_trends AS
SELECT 
    id,
    source,
    topic,
    keywords,
    popularity_score,
    growth_rate,
    category,
    region,
    collected_at,
    -- Calculate trend age in hours
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - collected_at)) / 3600 AS age_hours,
    -- Calculate a composite quality score
    CASE 
        WHEN growth_rate IS NOT NULL THEN
            (popularity_score * 0.7) + (LEAST(growth_rate, 100) * 0.3)
        ELSE
            popularity_score
    END AS quality_score
FROM trends
WHERE 
    collected_at >= CURRENT_TIMESTAMP - INTERVAL '48 hours'
    AND popularity_score >= 20
ORDER BY quality_score DESC, collected_at DESC;

COMMENT ON VIEW recent_quality_trends IS 'View showing recent trends with good popularity scores, including calculated quality metrics';

-- Function to get trending topics by time period
CREATE OR REPLACE FUNCTION get_trends_by_period(
    hours_back INTEGER DEFAULT 24,
    min_score FLOAT DEFAULT 10.0,
    source_filter VARCHAR DEFAULT NULL,
    category_filter VARCHAR DEFAULT NULL,
    region_filter VARCHAR DEFAULT NULL,
    limit_count INTEGER DEFAULT 50
)
RETURNS TABLE (
    id UUID,
    source VARCHAR,
    topic VARCHAR,
    popularity_score FLOAT,
    growth_rate FLOAT,
    category VARCHAR,
    region VARCHAR,
    collected_at TIMESTAMP WITH TIME ZONE,
    keywords JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.id, t.source, t.topic, t.popularity_score, t.growth_rate,
        t.category, t.region, t.collected_at, t.keywords
    FROM trends t
    WHERE 
        t.collected_at >= CURRENT_TIMESTAMP - (hours_back || ' hours')::INTERVAL
        AND t.popularity_score >= min_score
        AND (source_filter IS NULL OR t.source = source_filter)
        AND (category_filter IS NULL OR t.category = category_filter)
        AND (region_filter IS NULL OR t.region = region_filter)
    ORDER BY t.popularity_score DESC, t.collected_at DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_trends_by_period IS 'Function to retrieve trends with flexible filtering by time, source, category, and region';

-- Function to search trends by keywords
CREATE OR REPLACE FUNCTION search_trends(
    search_term TEXT,
    hours_back INTEGER DEFAULT 168, -- Default 1 week
    limit_count INTEGER DEFAULT 20
)
RETURNS TABLE (
    id UUID,
    source VARCHAR,
    topic VARCHAR,
    popularity_score FLOAT,
    category VARCHAR,
    collected_at TIMESTAMP WITH TIME ZONE,
    similarity_rank FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.id, t.source, t.topic, t.popularity_score, t.category, t.collected_at,
        ts_rank(to_tsvector('english', t.topic), plainto_tsquery('english', search_term)) as similarity_rank
    FROM trends t
    WHERE 
        t.collected_at >= CURRENT_TIMESTAMP - (hours_back || ' hours')::INTERVAL
        AND (
            to_tsvector('english', t.topic) @@ plainto_tsquery('english', search_term)
            OR t.keywords @> to_jsonb(ARRAY[lower(search_term)])
        )
    ORDER BY similarity_rank DESC, t.popularity_score DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION search_trends IS 'Full-text search function for trends by topic content and keywords';

-- Create a function to clean old trends (data retention)
CREATE OR REPLACE FUNCTION cleanup_old_trends(retention_days INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM trends 
    WHERE collected_at < CURRENT_TIMESTAMP - (retention_days || ' days')::INTERVAL;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Log the cleanup
    INSERT INTO schema_migrations (migration_name, applied_at) 
    VALUES ('cleanup_old_trends_' || TO_CHAR(CURRENT_TIMESTAMP, 'YYYY_MM_DD'), CURRENT_TIMESTAMP)
    ON CONFLICT (migration_name) DO NOTHING;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_old_trends IS 'Function to remove old trend data based on retention policy';