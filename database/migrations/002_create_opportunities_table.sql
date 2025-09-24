-- Migration 002: Create content_opportunities table
-- This table stores AI-generated content opportunities based on trending topics

CREATE TABLE content_opportunities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trend_id UUID NOT NULL REFERENCES trends(id) ON DELETE CASCADE,
    
    -- Content strategy
    suggested_angle TEXT NOT NULL,
    content_type VARCHAR(50) NOT NULL DEFAULT 'video',
    target_platforms TEXT[] DEFAULT ARRAY['youtube'],
    
    -- Predictions and scoring
    estimated_views INTEGER DEFAULT 0,
    estimated_engagement_rate FLOAT DEFAULT 0.0,
    competition_level VARCHAR(20) DEFAULT 'medium',
    viral_potential_score FLOAT DEFAULT 0.0,
    
    -- Cost and ROI analysis
    production_cost DECIMAL(10,2) DEFAULT 0.00,
    estimated_revenue DECIMAL(10,2) DEFAULT 0.00,
    estimated_roi FLOAT DEFAULT 0.0,
    priority_score FLOAT NOT NULL DEFAULT 0.0,
    
    -- Production details
    estimated_production_time INTEGER DEFAULT 60, -- minutes
    difficulty_level VARCHAR(20) DEFAULT 'medium',
    required_skills TEXT[] DEFAULT '{}',
    
    -- Content planning
    suggested_title VARCHAR(500),
    suggested_description TEXT,
    suggested_hashtags TEXT[] DEFAULT '{}',
    content_outline JSONB DEFAULT '{}',
    
    -- AI analysis metadata
    ai_confidence_score FLOAT DEFAULT 0.0,
    analysis_version VARCHAR(50) DEFAULT '1.0',
    analysis_prompt TEXT,
    ai_raw_response JSONB DEFAULT '{}',
    
    -- Status and workflow
    status VARCHAR(20) DEFAULT 'pending',
    assigned_to UUID,
    due_date TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    selected_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}',
    
    -- Constraints
    CONSTRAINT opportunities_estimated_views_check CHECK (estimated_views >= 0),
    CONSTRAINT opportunities_engagement_rate_check CHECK (estimated_engagement_rate >= 0 AND estimated_engagement_rate <= 100),
    CONSTRAINT opportunities_competition_level_check CHECK (competition_level IN ('low', 'medium', 'high')),
    CONSTRAINT opportunities_viral_potential_check CHECK (viral_potential_score >= 0 AND viral_potential_score <= 100),
    CONSTRAINT opportunities_production_cost_check CHECK (production_cost >= 0),
    CONSTRAINT opportunities_estimated_revenue_check CHECK (estimated_revenue >= 0),
    CONSTRAINT opportunities_priority_score_check CHECK (priority_score >= 0 AND priority_score <= 100),
    CONSTRAINT opportunities_production_time_check CHECK (estimated_production_time > 0),
    CONSTRAINT opportunities_difficulty_level_check CHECK (difficulty_level IN ('easy', 'medium', 'hard')),
    CONSTRAINT opportunities_ai_confidence_check CHECK (ai_confidence_score >= 0 AND ai_confidence_score <= 100),
    CONSTRAINT opportunities_status_check CHECK (status IN ('pending', 'selected', 'in_production', 'completed', 'published', 'rejected', 'expired')),
    CONSTRAINT opportunities_content_type_check CHECK (content_type IN ('video', 'image', 'text', 'audio', 'interactive', 'mixed'))
);

-- Create indexes for performance
CREATE INDEX idx_opportunities_trend_id ON content_opportunities(trend_id);
CREATE INDEX idx_opportunities_priority_score ON content_opportunities(priority_score DESC);
CREATE INDEX idx_opportunities_status ON content_opportunities(status);
CREATE INDEX idx_opportunities_created_at ON content_opportunities(created_at DESC);
CREATE INDEX idx_opportunities_competition_level ON content_opportunities(competition_level);
CREATE INDEX idx_opportunities_viral_potential ON content_opportunities(viral_potential_score DESC);
CREATE INDEX idx_opportunities_estimated_roi ON content_opportunities(estimated_roi DESC);

-- Composite indexes for common query patterns
CREATE INDEX idx_opportunities_status_priority ON content_opportunities(status, priority_score DESC);
CREATE INDEX idx_opportunities_status_created ON content_opportunities(status, created_at DESC);
CREATE INDEX idx_opportunities_platform_priority ON content_opportunities(target_platforms, priority_score DESC);

-- GIN index for target platforms array
CREATE INDEX idx_opportunities_platforms_gin ON content_opportunities USING gin(target_platforms);

-- GIN index for hashtags array
CREATE INDEX idx_opportunities_hashtags_gin ON content_opportunities USING gin(suggested_hashtags);

-- GIN index for metadata JSONB
CREATE INDEX idx_opportunities_metadata_gin ON content_opportunities USING gin(metadata);

-- Full-text search index for content suggestions
CREATE INDEX idx_opportunities_content_search ON content_opportunities 
USING gin(to_tsvector('english', 
    COALESCE(suggested_title, '') || ' ' || 
    COALESCE(suggested_description, '') || ' ' || 
    COALESCE(suggested_angle, '')
));

-- Trigger to update updated_at timestamp
CREATE TRIGGER opportunities_update_updated_at
    BEFORE UPDATE ON content_opportunities
    FOR EACH ROW
    EXECUTE FUNCTION update_trends_updated_at();

-- Add comments for documentation
COMMENT ON TABLE content_opportunities IS 'AI-generated content opportunities based on trending topics';
COMMENT ON COLUMN content_opportunities.trend_id IS 'Reference to the trend that generated this opportunity';
COMMENT ON COLUMN content_opportunities.suggested_angle IS 'AI-suggested content angle or approach';
COMMENT ON COLUMN content_opportunities.content_type IS 'Type of content to create (video, image, text, etc.)';
COMMENT ON COLUMN content_opportunities.target_platforms IS 'Array of platforms where content should be published';
COMMENT ON COLUMN content_opportunities.estimated_views IS 'AI prediction of potential view count';
COMMENT ON COLUMN content_opportunities.competition_level IS 'Assessed competition level for this content angle';
COMMENT ON COLUMN content_opportunities.viral_potential_score IS 'AI assessment of viral potential (0-100)';
COMMENT ON COLUMN content_opportunities.priority_score IS 'Overall priority score combining multiple factors (0-100)';
COMMENT ON COLUMN content_opportunities.ai_confidence_score IS 'Confidence level of AI analysis (0-100)';

-- Create a view for high-priority opportunities
CREATE VIEW high_priority_opportunities AS
SELECT 
    o.id,
    o.trend_id,
    t.topic as trend_topic,
    t.source as trend_source,
    t.popularity_score as trend_popularity,
    o.suggested_angle,
    o.content_type,
    o.target_platforms,
    o.estimated_views,
    o.competition_level,
    o.viral_potential_score,
    o.estimated_roi,
    o.priority_score,
    o.estimated_production_time,
    o.difficulty_level,
    o.status,
    o.created_at,
    -- Calculate opportunity age in hours
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - o.created_at)) / 3600 AS age_hours,
    -- Calculate a combined score
    (o.priority_score * 0.6 + t.popularity_score * 0.4) AS combined_score
FROM content_opportunities o
JOIN trends t ON o.trend_id = t.id
WHERE 
    o.status IN ('pending', 'selected')
    AND o.priority_score >= 60
    AND t.collected_at >= CURRENT_TIMESTAMP - INTERVAL '72 hours' -- Recent trends only
ORDER BY combined_score DESC, o.created_at DESC;

COMMENT ON VIEW high_priority_opportunities IS 'View showing high-priority content opportunities with trend context';

-- Function to get opportunities by criteria
CREATE OR REPLACE FUNCTION get_opportunities_by_criteria(
    status_filter VARCHAR DEFAULT NULL,
    min_priority_score FLOAT DEFAULT 0.0,
    max_production_time INTEGER DEFAULT NULL,
    platform_filter TEXT DEFAULT NULL,
    competition_filter VARCHAR DEFAULT NULL,
    hours_back INTEGER DEFAULT 48,
    limit_count INTEGER DEFAULT 50
)
RETURNS TABLE (
    id UUID,
    trend_topic VARCHAR,
    suggested_angle TEXT,
    content_type VARCHAR,
    target_platforms TEXT[],
    priority_score FLOAT,
    estimated_views INTEGER,
    estimated_roi FLOAT,
    competition_level VARCHAR,
    estimated_production_time INTEGER,
    status VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE
) AS $
BEGIN
    RETURN QUERY
    SELECT 
        o.id, t.topic, o.suggested_angle, o.content_type, o.target_platforms,
        o.priority_score, o.estimated_views, o.estimated_roi, o.competition_level,
        o.estimated_production_time, o.status, o.created_at
    FROM content_opportunities o
    JOIN trends t ON o.trend_id = t.id
    WHERE 
        o.created_at >= CURRENT_TIMESTAMP - (hours_back || ' hours')::INTERVAL
        AND o.priority_score >= min_priority_score
        AND (status_filter IS NULL OR o.status = status_filter)
        AND (max_production_time IS NULL OR o.estimated_production_time <= max_production_time)
        AND (platform_filter IS NULL OR platform_filter = ANY(o.target_platforms))
        AND (competition_filter IS NULL OR o.competition_level = competition_filter)
    ORDER BY o.priority_score DESC, o.created_at DESC
    LIMIT limit_count;
END;
$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_opportunities_by_criteria IS 'Flexible function to retrieve content opportunities with various filters';

-- Function to update opportunity status
CREATE OR REPLACE FUNCTION update_opportunity_status(
    opportunity_id UUID,
    new_status VARCHAR,
    assigned_user UUID DEFAULT NULL
)
RETURNS BOOLEAN AS $
DECLARE
    current_status VARCHAR;
BEGIN
    -- Get current status
    SELECT status INTO current_status 
    FROM content_opportunities 
    WHERE id = opportunity_id;
    
    IF current_status IS NULL THEN
        RETURN FALSE; -- Opportunity not found
    END IF;
    
    -- Update the opportunity
    UPDATE content_opportunities 
    SET 
        status = new_status,
        assigned_to = COALESCE(assigned_user, assigned_to),
        selected_at = CASE WHEN new_status = 'selected' THEN CURRENT_TIMESTAMP ELSE selected_at END,
        completed_at = CASE WHEN new_status = 'completed' THEN CURRENT_TIMESTAMP ELSE completed_at END,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = opportunity_id;
    
    RETURN TRUE;
END;
$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_opportunity_status IS 'Function to update opportunity status with automatic timestamp handling';

-- Function to calculate opportunity metrics
CREATE OR REPLACE FUNCTION calculate_opportunity_metrics()
RETURNS TABLE (
    total_opportunities BIGINT,
    pending_count BIGINT,
    selected_count BIGINT,
    completed_count BIGINT,
    avg_priority_score FLOAT,
    avg_estimated_views INTEGER,
    avg_production_time INTEGER,
    high_priority_count BIGINT,
    low_competition_count BIGINT
) AS $
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*) as total_opportunities,
        COUNT(*) FILTER (WHERE status = 'pending') as pending_count,
        COUNT(*) FILTER (WHERE status = 'selected') as selected_count,
        COUNT(*) FILTER (WHERE status = 'completed') as completed_count,
        AVG(priority_score) as avg_priority_score,
        AVG(estimated_views)::INTEGER as avg_estimated_views,
        AVG(estimated_production_time)::INTEGER as avg_production_time,
        COUNT(*) FILTER (WHERE priority_score >= 70) as high_priority_count,
        COUNT(*) FILTER (WHERE competition_level = 'low') as low_competition_count
    FROM content_opportunities
    WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days';
END;
$ LANGUAGE plpgsql;

COMMENT ON FUNCTION calculate_opportunity_metrics IS 'Function to calculate various metrics about content opportunities';

-- Function to expire old opportunities
CREATE OR REPLACE FUNCTION expire_old_opportunities(expiry_hours INTEGER DEFAULT 72)
RETURNS INTEGER AS $
DECLARE
    expired_count INTEGER;
BEGIN
    UPDATE content_opportunities 
    SET 
        status = 'expired',
        updated_at = CURRENT_TIMESTAMP
    WHERE 
        status = 'pending'
        AND created_at < CURRENT_TIMESTAMP - (expiry_hours || ' hours')::INTERVAL;
    
    GET DIAGNOSTICS expired_count = ROW_COUNT;
    
    RETURN expired_count;
END;
$ LANGUAGE plpgsql;

COMMENT ON FUNCTION expire_old_opportunities IS 'Function to automatically expire old pending opportunities';

-- Create a trigger to automatically calculate priority score
CREATE OR REPLACE FUNCTION calculate_priority_score()
RETURNS TRIGGER AS $
BEGIN
    -- Calculate priority score based on multiple factors
    NEW.priority_score := LEAST(100.0, GREATEST(0.0,
        -- Base score from viral potential (40%)
        (COALESCE(NEW.viral_potential_score, 50.0) * 0.4) +
        -- ROI factor (30%)
        (LEAST(100, GREATEST(0, NEW.estimated_roi * 10)) * 0.3) +
        -- Competition factor (20%) - inverse relationship
        (CASE 
            WHEN NEW.competition_level = 'low' THEN 20
            WHEN NEW.competition_level = 'medium' THEN 12
            ELSE 5
        END) +
        -- Production time factor (10%) - inverse relationship  
        (CASE
            WHEN NEW.estimated_production_time <= 30 THEN 10
            WHEN NEW.estimated_production_time <= 60 THEN 7
            WHEN NEW.estimated_production_time <= 120 THEN 4
            ELSE 1
        END)
    ));
    
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

CREATE TRIGGER opportunity_calculate_priority
    BEFORE INSERT OR UPDATE ON content_opportunities
    FOR EACH ROW
    EXECUTE FUNCTION calculate_priority_score();