-- Migration 003: Create content_items table
-- This table stores the actual content produced from opportunities

CREATE TABLE content_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    opportunity_id UUID NOT NULL REFERENCES content_opportunities(id) ON DELETE CASCADE,
    
    -- Basic content information
    title VARCHAR(500) NOT NULL,
    description TEXT,
    content_type VARCHAR(50) NOT NULL DEFAULT 'video',
    
    -- Content planning and structure
    content_plan JSONB DEFAULT '{}',
    script_content TEXT,
    visual_plan JSONB DEFAULT '{}',
    audio_plan JSONB DEFAULT '{}',
    
    -- Production details
    production_status VARCHAR(30) DEFAULT 'planning',
    production_quality_tier VARCHAR(20) DEFAULT 'balanced',
    estimated_duration_seconds INTEGER,
    actual_duration_seconds INTEGER,
    
    -- Asset management
    assets JSONB DEFAULT '{}', -- URLs and paths to generated assets
    thumbnail_url VARCHAR(1000),
    preview_url VARCHAR(1000),
    final_content_url VARCHAR(1000),
    
    -- AI generation metadata
    ai_services_used JSONB DEFAULT '{}',
    generation_prompts JSONB DEFAULT '{}',
    ai_generation_log JSONB DEFAULT '{}',
    
    -- Quality and review
    quality_score FLOAT DEFAULT 0.0,
    review_status VARCHAR(20) DEFAULT 'pending',
    review_notes TEXT,
    reviewer_id UUID,
    
    -- Cost tracking
    cost_breakdown JSONB DEFAULT '{}',
    total_production_cost DECIMAL(10,2) DEFAULT 0.00,
    ai_service_costs DECIMAL(10,2) DEFAULT 0.00,
    manual_work_cost DECIMAL(10,2) DEFAULT 0.00,
    
    -- Platform optimization
    platform_versions JSONB DEFAULT '{}', -- Different versions for different platforms
    seo_keywords TEXT[],
    target_audience VARCHAR(100),
    content_tags TEXT[],
    
    -- Workflow and assignments
    assigned_to UUID,
    producer_id UUID,
    editor_id UUID,
    approver_id UUID,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    production_started_at TIMESTAMP WITH TIME ZONE,
    production_completed_at TIMESTAMP WITH TIME ZONE,
    approved_at TIMESTAMP WITH TIME ZONE,
    published_at TIMESTAMP WITH TIME ZONE,
    
    -- Scheduling
    scheduled_publish_at TIMESTAMP WITH TIME ZONE,
    embargo_until TIMESTAMP WITH TIME ZONE,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}',
    version INTEGER DEFAULT 1,
    parent_content_id UUID REFERENCES content_items(id), -- For versions/remixes
    
    -- Constraints
    CONSTRAINT content_items_production_status_check CHECK (production_status IN (
        'planning', 'script_generation', 'asset_generation', 'editing', 
        'review', 'approved', 'published', 'archived', 'failed'
    )),
    CONSTRAINT content_items_quality_tier_check CHECK (production_quality_tier IN ('budget', 'balanced', 'premium')),
    CONSTRAINT content_items_review_status_check CHECK (review_status IN ('pending', 'approved', 'rejected', 'needs_revision')),
    CONSTRAINT content_items_content_type_check CHECK (content_type IN ('video', 'image', 'text', 'audio', 'interactive', 'mixed')),
    CONSTRAINT content_items_quality_score_check CHECK (quality_score >= 0 AND quality_score <= 100),
    CONSTRAINT content_items_duration_check CHECK (estimated_duration_seconds IS NULL OR estimated_duration_seconds > 0),
    CONSTRAINT content_items_actual_duration_check CHECK (actual_duration_seconds IS NULL OR actual_duration_seconds > 0),
    CONSTRAINT content_items_total_cost_check CHECK (total_production_cost >= 0),
    CONSTRAINT content_items_version_check CHECK (version >= 1)
);

-- Create indexes for performance
CREATE INDEX idx_content_opportunity_id ON content_items(opportunity_id);
CREATE INDEX idx_content_production_status ON content_items(production_status);
CREATE INDEX idx_content_created_at ON content_items(created_at DESC);
CREATE INDEX idx_content_review_status ON content_items(review_status);
CREATE INDEX idx_content_quality_tier ON content_items(production_quality_tier);
CREATE INDEX idx_content_assigned_to ON content_items(assigned_to);
CREATE INDEX idx_content_quality_score ON content_items(quality_score DESC);
CREATE INDEX idx_content_total_cost ON content_items(total_production_cost);

-- Composite indexes for common queries
CREATE INDEX idx_content_status_created ON content_items(production_status, created_at DESC);
CREATE INDEX idx_content_review_quality ON content_items(review_status, quality_score DESC);
CREATE INDEX idx_content_tier_cost ON content_items(production_quality_tier, total_production_cost);

-- GIN indexes for JSONB columns
CREATE INDEX idx_content_assets_gin ON content_items USING gin(assets);
CREATE INDEX idx_content_plan_gin ON content_items USING gin(content_plan);
CREATE INDEX idx_content_ai_services_gin ON content_items USING gin(ai_services_used);
CREATE INDEX idx_content_platform_versions_gin ON content_items USING gin(platform_versions);

-- GIN indexes for arrays
CREATE INDEX idx_content_seo_keywords_gin ON content_items USING gin(seo_keywords);
CREATE INDEX idx_content_tags_gin ON content_items USING gin(content_tags);

-- Full-text search index
CREATE INDEX idx_content_search ON content_items 
USING gin(to_tsvector('english', 
    COALESCE(title, '') || ' ' || 
    COALESCE(description, '') || ' ' || 
    COALESCE(script_content, '')
));

-- Partial indexes for active content
CREATE INDEX idx_content_active ON content_items(production_status, created_at DESC)
WHERE production_status IN ('planning', 'script_generation', 'asset_generation', 'editing', 'review');

-- Index for scheduled content
CREATE INDEX idx_content_scheduled ON content_items(scheduled_publish_at)
WHERE scheduled_publish_at IS NOT NULL AND production_status = 'approved';

-- Trigger to update updated_at timestamp
CREATE TRIGGER content_items_update_updated_at
    BEFORE UPDATE ON content_items
    FOR EACH ROW
    EXECUTE FUNCTION update_trends_updated_at();

-- Add comments for documentation
COMMENT ON TABLE content_items IS 'Stores actual content produced from content opportunities';
COMMENT ON COLUMN content_items.opportunity_id IS 'Reference to the content opportunity that generated this item';
COMMENT ON COLUMN content_items.content_plan IS 'Detailed plan for content creation (JSON structure)';
COMMENT ON COLUMN content_items.production_status IS 'Current status in the production pipeline';
COMMENT ON COLUMN content_items.production_quality_tier IS 'Quality tier determining which AI services to use';
COMMENT ON COLUMN content_items.assets IS 'JSON object containing URLs and metadata for all generated assets';
COMMENT ON COLUMN content_items.ai_services_used IS 'Log of which AI services were used and their configurations';
COMMENT ON COLUMN content_items.cost_breakdown IS 'Detailed breakdown of production costs';
COMMENT ON COLUMN content_items.platform_versions IS 'Different optimized versions for different platforms';

-- Create a view for content production pipeline
CREATE VIEW content_production_pipeline AS
SELECT 
    ci.id,
    ci.title,
    ci.content_type,
    ci.production_status,
    ci.production_quality_tier,
    ci.review_status,
    ci.quality_score,
    ci.total_production_cost,
    ci.assigned_to,
    ci.created_at,
    ci.production_started_at,
    ci.production_completed_at,
    -- Opportunity context
    co.suggested_angle,
    co.priority_score,
    co.estimated_views,
    -- Trend context
    t.topic as trend_topic,
    t.source as trend_source,
    t.popularity_score as trend_popularity,
    -- Production metrics
    EXTRACT(EPOCH FROM (COALESCE(ci.production_completed_at, CURRENT_TIMESTAMP) - ci.created_at)) / 3600 AS production_hours,
    CASE 
        WHEN ci.production_completed_at IS NOT NULL AND ci.total_production_cost > 0 THEN
            ci.total_production_cost / NULLIF(EXTRACT(EPOCH FROM (ci.production_completed_at - ci.production_started_at)) / 3600, 0)
        ELSE NULL
    END AS cost_per_hour
FROM content_items ci
JOIN content_opportunities co ON ci.opportunity_id = co.id
JOIN trends t ON co.trend_id = t.id
ORDER BY ci.created_at DESC;

COMMENT ON VIEW content_production_pipeline IS 'Comprehensive view of content production with opportunity and trend context';

-- Function to get content by production status
CREATE OR REPLACE FUNCTION get_content_by_status(
    status_filter VARCHAR DEFAULT NULL,
    quality_tier_filter VARCHAR DEFAULT NULL,
    assigned_to_filter UUID DEFAULT NULL,
    hours_back INTEGER DEFAULT 168, -- 1 week default
    limit_count INTEGER DEFAULT 50
)
RETURNS TABLE (
    id UUID,
    title VARCHAR,
    content_type VARCHAR,
    production_status VARCHAR,
    production_quality_tier VARCHAR,
    review_status VARCHAR,
    quality_score FLOAT,
    total_production_cost DECIMAL,
    created_at TIMESTAMP WITH TIME ZONE,
    opportunity_priority FLOAT,
    trend_topic VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ci.id, ci.title, ci.content_type, ci.production_status, ci.production_quality_tier,
        ci.review_status, ci.quality_score, ci.total_production_cost, ci.created_at,
        co.priority_score, t.topic
    FROM content_items ci
    JOIN content_opportunities co ON ci.opportunity_id = co.id
    JOIN trends t ON co.trend_id = t.id
    WHERE 
        ci.created_at >= CURRENT_TIMESTAMP - (hours_back || ' hours')::INTERVAL
        AND (status_filter IS NULL OR ci.production_status = status_filter)
        AND (quality_tier_filter IS NULL OR ci.production_quality_tier = quality_tier_filter)
        AND (assigned_to_filter IS NULL OR ci.assigned_to = assigned_to_filter)
    ORDER BY ci.created_at DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Function to update production status with automatic timestamps
CREATE OR REPLACE FUNCTION update_production_status(
    content_id UUID,
    new_status VARCHAR,
    assigned_user UUID DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
    current_status VARCHAR;
BEGIN
    SELECT production_status INTO current_status 
    FROM content_items 
    WHERE id = content_id;
    
    IF current_status IS NULL THEN
        RETURN FALSE;
    END IF;
    
    UPDATE content_items 
    SET 
        production_status = new_status,
        assigned_to = COALESCE(assigned_user, assigned_to),
        production_started_at = CASE 
            WHEN new_status IN ('script_generation', 'asset_generation') AND production_started_at IS NULL 
            THEN CURRENT_TIMESTAMP 
            ELSE production_started_at 
        END,
        production_completed_at = CASE 
            WHEN new_status = 'approved' 
            THEN CURRENT_TIMESTAMP 
            ELSE production_completed_at 
        END,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = content_id;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate production metrics
CREATE OR REPLACE FUNCTION calculate_production_metrics(days_back INTEGER DEFAULT 7)
RETURNS TABLE (
    total_content BIGINT,
    completed_content BIGINT,
    avg_production_time_hours FLOAT,
    avg_production_cost DECIMAL,
    avg_quality_score FLOAT,
    success_rate FLOAT,
    content_by_tier JSONB,
    content_by_status JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*) as total_content,
        COUNT(*) FILTER (WHERE production_status IN ('approved', 'published')) as completed_content,
        AVG(EXTRACT(EPOCH FROM (production_completed_at - production_started_at)) / 3600) as avg_production_time_hours,
        AVG(total_production_cost) as avg_production_cost,
        AVG(quality_score) FILTER (WHERE quality_score > 0) as avg_quality_score,
        (COUNT(*) FILTER (WHERE production_status IN ('approved', 'published')) * 100.0 / NULLIF(COUNT(*), 0)) as success_rate,
        json_build_object(
            'budget', COUNT(*) FILTER (WHERE production_quality_tier = 'budget'),
            'balanced', COUNT(*) FILTER (WHERE production_quality_tier = 'balanced'),
            'premium', COUNT(*) FILTER (WHERE production_quality_tier = 'premium')
        ) as content_by_tier,
        json_build_object(
            'planning', COUNT(*) FILTER (WHERE production_status = 'planning'),
            'script_generation', COUNT(*) FILTER (WHERE production_status = 'script_generation'),
            'asset_generation', COUNT(*) FILTER (WHERE production_status = 'asset_generation'),
            'editing', COUNT(*) FILTER (WHERE production_status = 'editing'),
            'review', COUNT(*) FILTER (WHERE production_status = 'review'),
            'approved', COUNT(*) FILTER (WHERE production_status = 'approved'),
            'published', COUNT(*) FILTER (WHERE production_status = 'published')
        ) as content_by_status
    FROM content_items
    WHERE created_at >= CURRENT_TIMESTAMP - (days_back || ' days')::INTERVAL;
END;
$$ LANGUAGE plpgsql;

-- Function to archive old completed content
CREATE OR REPLACE FUNCTION archive_old_content(archive_after_days INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    archived_count INTEGER;
BEGIN
    UPDATE content_items 
    SET 
        production_status = 'archived',
        updated_at = CURRENT_TIMESTAMP
    WHERE 
        production_status = 'published'
        AND published_at < CURRENT_TIMESTAMP - (archive_after_days || ' days')::INTERVAL;
    
    GET DIAGNOSTICS archived_count = ROW_COUNT;
    
    RETURN archived_count;
END;
$$ LANGUAGE plpgsql;