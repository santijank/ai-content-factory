-- Migration 004: Create uploads table
-- This table tracks content uploads to various platforms

CREATE TABLE uploads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_id UUID NOT NULL REFERENCES content_items(id) ON DELETE CASCADE,
    
    -- Platform information
    platform VARCHAR(20) NOT NULL,
    platform_id VARCHAR(255), -- ID returned by the platform after upload
    platform_url VARCHAR(1000), -- Direct URL to the content on platform
    
    -- Upload details
    upload_status VARCHAR(20) DEFAULT 'pending',
    upload_attempt INTEGER DEFAULT 1,
    max_retries INTEGER DEFAULT 3,
    
    -- Platform-specific metadata
    metadata JSONB DEFAULT '{}',
    platform_title VARCHAR(500),
    platform_description TEXT,
    platform_tags TEXT[],
    platform_category VARCHAR(100),
    
    -- Upload configuration
    upload_config JSONB DEFAULT '{}', -- Platform-specific upload settings
    privacy_setting VARCHAR(20) DEFAULT 'public',
    monetization_enabled BOOLEAN DEFAULT false,
    comments_enabled BOOLEAN DEFAULT true,
    
    -- Scheduling
    scheduled_publish_at TIMESTAMP WITH TIME ZONE,
    published_at TIMESTAMP WITH TIME ZONE,
    
    -- File information
    file_path VARCHAR(1000),
    file_size_bytes BIGINT,
    file_format VARCHAR(20),
    thumbnail_path VARCHAR(1000),
    
    -- Upload performance
    upload_duration_seconds INTEGER,
    upload_speed_mbps FLOAT,
    processing_duration_seconds INTEGER,
    
    -- API response data
    api_response JSONB DEFAULT '{}',
    error_log JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    upload_started_at TIMESTAMP WITH TIME ZONE,
    upload_completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Additional metadata
    uploader_user_id UUID,
    upload_batch_id UUID, -- For batch uploads
    
    -- Constraints
    CONSTRAINT uploads_platform_check CHECK (platform IN (
        'youtube', 'tiktok', 'instagram', 'facebook', 'twitter', 'linkedin', 
        'reddit', 'snapchat', 'pinterest', 'other'
    )),
    CONSTRAINT uploads_status_check CHECK (upload_status IN (
        'pending', 'uploading', 'processing', 'published', 'failed', 'cancelled', 'scheduled'
    )),
    CONSTRAINT uploads_privacy_check CHECK (privacy_setting IN ('public', 'unlisted', 'private')),
    CONSTRAINT uploads_attempt_check CHECK (upload_attempt > 0),
    CONSTRAINT uploads_max_retries_check CHECK (max_retries >= 0),
    CONSTRAINT uploads_file_size_check CHECK (file_size_bytes IS NULL OR file_size_bytes >= 0),
    CONSTRAINT uploads_upload_duration_check CHECK (upload_duration_seconds IS NULL OR upload_duration_seconds > 0),
    CONSTRAINT uploads_processing_duration_check CHECK (processing_duration_seconds IS NULL OR processing_duration_seconds > 0),
    
    -- Ensure platform_id is unique per platform (can't upload same content twice to same platform)
    CONSTRAINT uploads_platform_id_unique UNIQUE (platform, platform_id) DEFERRABLE INITIALLY DEFERRED
);

-- Create indexes for performance
CREATE INDEX idx_uploads_content_id ON uploads(content_id);
CREATE INDEX idx_uploads_platform ON uploads(platform);
CREATE INDEX idx_uploads_status ON uploads(upload_status);
CREATE INDEX idx_uploads_created_at ON uploads(created_at DESC);
CREATE INDEX idx_uploads_published_at ON uploads(published_at DESC) WHERE published_at IS NOT NULL;
CREATE INDEX idx_uploads_uploader ON uploads(uploader_user_id);
CREATE INDEX idx_uploads_batch ON uploads(upload_batch_id) WHERE upload_batch_id IS NOT NULL;

-- Composite indexes for common queries
CREATE INDEX idx_uploads_platform_status ON uploads(platform, upload_status);
CREATE INDEX idx_uploads_content_platform ON uploads(content_id, platform);
CREATE INDEX idx_uploads_status_created ON uploads(upload_status, created_at DESC);

-- Index for scheduled uploads
CREATE INDEX idx_uploads_scheduled ON uploads(scheduled_publish_at)
WHERE scheduled_publish_at IS NOT NULL AND upload_status = 'scheduled';

-- GIN indexes for JSONB columns
CREATE INDEX idx_uploads_metadata_gin ON uploads USING gin(metadata);
CREATE INDEX idx_uploads_config_gin ON uploads USING gin(upload_config);
CREATE INDEX idx_uploads_api_response_gin ON uploads USING gin(api_response);

-- GIN index for platform tags
CREATE INDEX idx_uploads_tags_gin ON uploads USING gin(platform_tags);

-- Full-text search index for platform content
CREATE INDEX idx_uploads_content_search ON uploads 
USING gin(to_tsvector('english', 
    COALESCE(platform_title, '') || ' ' || 
    COALESCE(platform_description, '')
));

-- Trigger to update updated_at timestamp
CREATE TRIGGER uploads_update_updated_at
    BEFORE UPDATE ON uploads
    FOR EACH ROW
    EXECUTE FUNCTION update_trends_updated_at();

-- Add comments for documentation
COMMENT ON TABLE uploads IS 'Tracks content uploads to various social media platforms';
COMMENT ON COLUMN uploads.content_id IS 'Reference to the content item being uploaded';
COMMENT ON COLUMN uploads.platform IS 'Target platform for upload (youtube, tiktok, etc.)';
COMMENT ON COLUMN uploads.platform_id IS 'Unique ID returned by platform after successful upload';
COMMENT ON COLUMN uploads.platform_url IS 'Direct URL to access the content on the platform';
COMMENT ON COLUMN uploads.upload_status IS 'Current status of the upload process';
COMMENT ON COLUMN uploads.metadata IS 'Platform-specific metadata and settings';
COMMENT ON COLUMN uploads.upload_config IS 'Configuration used for this specific upload';
COMMENT ON COLUMN uploads.api_response IS