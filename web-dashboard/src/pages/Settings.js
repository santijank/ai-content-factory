import React, { useState, useEffect } from 'react';
import Modal from '../components/Modal';
import '../styles/Settings.css';

const Settings = () => {
    const [settings, setSettings] = useState({
        ai_config: {
            quality_tier: 'balanced',
            text_ai_provider: 'openai',
            image_ai_provider: 'leonardo',
            audio_ai_provider: 'azure'
        },
        trend_config: {
            collection_frequency: 'every_6_hours',
            sources: ['youtube', 'google_trends', 'twitter'],
            regions: ['TH', 'US', 'global'],
            categories: ['all']
        },
        content_config: {
            default_platforms: ['youtube', 'tiktok'],
            auto_publish: false,
            content_length: 'medium',
            language: 'th'
        },
        notification_config: {
            email_notifications: true,
            trend_alerts: true,
            generation_complete: true,
            upload_status: true
        },
        platform_credentials: {
            youtube: { connected: false },
            tiktok: { connected: false },
            instagram: { connected: false },
            facebook: { connected: false }
        }
    });
    
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [showApiModal, setShowApiModal] = useState(false);
    const [selectedProvider, setSelectedProvider] = useState(null);
    const [apiKeys, setApiKeys] = useState({});

    useEffect(() => {
        fetchSettings();
    }, []);

    const fetchSettings = async () => {
        try {
            setLoading(true);
            const response = await fetch('/api/settings');
            const data = await response.json();
            setSettings(prev => ({ ...prev, ...data }));
        } catch (error) {
            console.error('Error fetching settings:', error);
        } finally {
            setLoading(false);
        }
    };

    const saveSettings = async (updatedSettings = settings) => {
        try {
            setSaving(true);
            const response = await fetch('/api/settings', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(updatedSettings)
            });

            if (response.ok) {
                alert('Settings saved successfully!');
            } else {
                throw new Error('Failed to save settings');
            }
        } catch (error) {
            console.error('Error saving settings:', error);
            alert('Failed to save settings');
        } finally {
            setSaving(false);
        }
    };

    const handleSettingChange = (category, key, value) => {
        const updatedSettings = {
            ...settings,
            [category]: {
                ...settings[category],
                [key]: value
            }
        };
        setSettings(updatedSettings);
    };

    const handleArraySettingChange = (category, key, value, checked) => {
        const currentArray = settings[category][key] || [];
        let updatedArray;
        
        if (checked) {
            updatedArray = [...currentArray, value];
        } else {
            updatedArray = currentArray.filter(item => item !== value);
        }
        
        handleSettingChange(category, key, updatedArray);
    };

    const connectPlatform = async (platform) => {
        try {
            // Redirect to platform OAuth
            window.location.href = `/auth/${platform}`;
        } catch (error) {
            console.error(`Error connecting to ${platform}:`, error);
        }
    };

    const disconnectPlatform = async (platform) => {
        try {
            const response = await fetch(`/api/platforms/${platform}/disconnect`, {
                method: 'POST'
            });
            
            if (response.ok) {
                handleSettingChange('platform_credentials', platform, { connected: false });
                alert(`Disconnected from ${platform} successfully`);
            }
        } catch (error) {
            console.error(`Error disconnecting from ${platform}:`, error);
        }
    };

    const testApiConnection = async (provider, apiKey) => {
        try {
            const response = await fetch('/api/test-connection', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ provider, api_key: apiKey })
            });
            
            const result = await response.json();
            return result.success;
        } catch (error) {
            console.error('Error testing API connection:', error);
            return false;
        }
    };

    const handleApiKeySubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const apiKey = formData.get('api_key');
        
        const isValid = await testApiConnection(selectedProvider, apiKey);
        
        if (isValid) {
            setApiKeys(prev => ({ ...prev, [selectedProvider]: apiKey }));
            setShowApiModal(false);
            alert('API key saved and tested successfully!');
        } else {
            alert('Invalid API key. Please check and try again.');
        }
    };

    if (loading) {
        return (
            <div className="settings-page">
                <div className="loading-spinner">
                    <div className="spinner"></div>
                    <p>Loading settings...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="settings-page">
            <div className="settings-header">
                <h1>System Settings</h1>
                <button 
                    className="save-button"
                    onClick={() => saveSettings()}
                    disabled={saving}
                >
                    {saving ? 'Saving...' : 'Save Settings'}
                </button>
            </div>

            <div className="settings-sections">
                {/* AI Configuration */}
                <div className="settings-section">
                    <h2>AI Configuration</h2>
                    
                    <div className="setting-group">
                        <label>Quality Tier</label>
                        <select 
                            value={settings.ai_config.quality_tier}
                            onChange={(e) => handleSettingChange('ai_config', 'quality_tier', e.target.value)}
                        >
                            <option value="budget">Budget (Lower cost, basic quality)</option>
                            <option value="balanced">Balanced (Good quality, moderate cost)</option>
                            <option value="premium">Premium (Best quality, higher cost)</option>
                        </select>
                    </div>

                    <div className="setting-group">
                        <label>Text AI Provider</label>
                        <div className="provider-setting">
                            <select 
                                value={settings.ai_config.text_ai_provider}
                                onChange={(e) => handleSettingChange('ai_config', 'text_ai_provider', e.target.value)}
                            >
                                <option value="groq">Groq (Fast, budget-friendly)</option>
                                <option value="openai">OpenAI (GPT-4, balanced)</option>
                                <option value="claude">Claude (High quality, premium)</option>
                            </select>
                            <button 
                                className="config-button"
                                onClick={() => {
                                    setSelectedProvider(settings.ai_config.text_ai_provider);
                                    setShowApiModal(true);
                                }}
                            >
                                Configure API
                            </button>
                        </div>
                    </div>

                    <div className="setting-group">
                        <label>Image AI Provider</label>
                        <div className="provider-setting">
                            <select 
                                value={settings.ai_config.image_ai_provider}
                                onChange={(e) => handleSettingChange('ai_config', 'image_ai_provider', e.target.value)}
                            >
                                <option value="stable_diffusion">Stable Diffusion (Local, free)</option>
                                <option value="leonardo">Leonardo AI (Good quality)</option>
                                <option value="midjourney">Midjourney (Premium quality)</option>
                            </select>
                            <button 
                                className="config-button"
                                onClick={() => {
                                    setSelectedProvider(settings.ai_config.image_ai_provider);
                                    setShowApiModal(true);
                                }}
                            >
                                Configure API
                            </button>
                        </div>
                    </div>

                    <div className="setting-group">
                        <label>Audio AI Provider</label>
                        <div className="provider-setting">
                            <select 
                                value={settings.ai_config.audio_ai_provider}
                                onChange={(e) => handleSettingChange('ai_config', 'audio_ai_provider', e.target.value)}
                            >
                                <option value="gtts">Google TTS (Basic, free)</option>
                                <option value="azure">Azure TTS (Good quality)</option>
                                <option value="elevenlabs">ElevenLabs (Premium voices)</option>
                            </select>
                            <button 
                                className="config-button"
                                onClick={() => {
                                    setSelectedProvider(settings.ai_config.audio_ai_provider);
                                    setShowApiModal(true);
                                }}
                            >
                                Configure API
                            </button>
                        </div>
                    </div>
                </div>

                {/* Trend Collection */}
                <div className="settings-section">
                    <h2>Trend Collection</h2>
                    
                    <div className="setting-group">
                        <label>Collection Frequency</label>
                        <select 
                            value={settings.trend_config.collection_frequency}
                            onChange={(e) => handleSettingChange('trend_config', 'collection_frequency', e.target.value)}
                        >
                            <option value="every_hour">Every Hour</option>
                            <option value="every_3_hours">Every 3 Hours</option>
                            <option value="every_6_hours">Every 6 Hours</option>
                            <option value="daily">Daily</option>
                        </select>
                    </div>

                    <div className="setting-group">
                        <label>Data Sources</label>
                        <div className="checkbox-group">
                            {['youtube', 'google_trends', 'twitter', 'reddit'].map(source => (
                                <label key={source} className="checkbox-item">
                                    <input
                                        type="checkbox"
                                        checked={settings.trend_config.sources.includes(source)}
                                        onChange={(e) => handleArraySettingChange('trend_config', 'sources', source, e.target.checked)}
                                    />
                                    {source.charAt(0).toUpperCase() + source.slice(1).replace('_', ' ')}
                                </label>
                            ))}
                        </div>
                    </div>

                    <div className="setting-group">
                        <label>Target Regions</label>
                        <div className="checkbox-group">
                            {[
                                { value: 'TH', label: 'Thailand' },
                                { value: 'US', label: 'United States' },
                                { value: 'JP', label: 'Japan' },
                                { value: 'KR', label: 'South Korea' },
                                { value: 'global', label: 'Global' }
                            ].map(region => (
                                <label key={region.value} className="checkbox-item">
                                    <input
                                        type="checkbox"
                                        checked={settings.trend_config.regions.includes(region.value)}
                                        onChange={(e) => handleArraySettingChange('trend_config', 'regions', region.value, e.target.checked)}
                                    />
                                    {region.label}
                                </label>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Content Configuration */}
                <div className="settings-section">
                    <h2>Content Configuration</h2>
                    
                    <div className="setting-group">
                        <label>Default Platforms</label>
                        <div className="checkbox-group">
                            {['youtube', 'tiktok', 'instagram', 'facebook'].map(platform => (
                                <label key={platform} className="checkbox-item">
                                    <input
                                        type="checkbox"
                                        checked={settings.content_config.default_platforms.includes(platform)}
                                        onChange={(e) => handleArraySettingChange('content_config', 'default_platforms', platform, e.target.checked)}
                                    />
                                    {platform.charAt(0).toUpperCase() + platform.slice(1)}
                                </label>
                            ))}
                        </div>
                    </div>

                    <div className="setting-group">
                        <label>Content Length</label>
                        <select 
                            value={settings.content_config.content_length}
                            onChange={(e) => handleSettingChange('content_config', 'content_length', e.target.value)}
                        >
                            <option value="short">Short (15-30 seconds)</option>
                            <option value="medium">Medium (30-60 seconds)</option>
                            <option value="long">Long (1-3 minutes)</option>
                        </select>
                    </div>

                    <div className="setting-group">
                        <label>Primary Language</label>
                        <select 
                            value={settings.content_config.language}
                            onChange={(e) => handleSettingChange('content_config', 'language', e.target.value)}
                        >
                            <option value="th">Thai (ไทย)</option>
                            <option value="en">English</option>
                            <option value="mixed">Mixed (Thai + English)</option>
                        </select>
                    </div>

                    <div className="setting-group">
                        <label className="checkbox-item">
                            <input
                                type="checkbox"
                                checked={settings.content_config.auto_publish}
                                onChange={(e) => handleSettingChange('content_config', 'auto_publish', e.target.checked)}
                            />
                            Auto-publish approved content
                        </label>
                    </div>
                </div>

                {/* Platform Connections */}
                <div className="settings-section">
                    <h2>Platform Connections</h2>
                    
                    {Object.entries(settings.platform_credentials).map(([platform, creds]) => (
                        <div key={platform} className="platform-connection">
                            <div className="platform-info">
                                <span className="platform-name">
                                    {platform.charAt(0).toUpperCase() + platform.slice(1)}
                                </span>
                                <span className={`connection-status ${creds.connected ? 'connected' : 'disconnected'}`}>
                                    {creds.connected ? '● Connected' : '○ Not Connected'}
                                </span>
                            </div>
                            <div className="platform-actions">
                                {creds.connected ? (
                                    <button 
                                        className="disconnect-button"
                                        onClick={() => disconnectPlatform(platform)}
                                    >
                                        Disconnect
                                    </button>
                                ) : (
                                    <button 
                                        className="connect-button"
                                        onClick={() => connectPlatform(platform)}
                                    >
                                        Connect
                                    </button>
                                )}
                            </div>
                        </div>
                    ))}
                </div>

                {/* Notifications */}
                <div className="settings-section">
                    <h2>Notifications</h2>
                    
                    <div className="setting-group">
                        <label className="checkbox-item">
                            <input
                                type="checkbox"
                                checked={settings.notification_config.email_notifications}
                                onChange={(e) => handleSettingChange('notification_config', 'email_notifications', e.target.checked)}
                            />
                            Enable email notifications
                        </label>
                    </div>

                    <div className="setting-group">
                        <label className="checkbox-item">
                            <input
                                type="checkbox"
                                checked={settings.notification_config.trend_alerts}
                                onChange={(e) => handleSettingChange('notification_config', 'trend_alerts', e.target.checked)}
                            />
                            New trending opportunities
                        </label>
                    </div>

                    <div className="setting-group">
                        <label className="checkbox-item">
                            <input
                                type="checkbox"
                                checked={settings.notification_config.generation_complete}
                                onChange={(e) => handleSettingChange('notification_config', 'generation_complete', e.target.checked)}
                            />
                            Content generation completed
                        </label>
                    </div>

                    <div className="setting-group">
                        <label className="checkbox-item">
                            <input
                                type="checkbox"
                                checked={settings.notification_config.upload_status}
                                onChange={(e) => handleSettingChange('notification_config', 'upload_status', e.target.checked)}
                            />
                            Upload status updates
                        </label>
                    </div>
                </div>

                {/* System Status */}
                <div className="settings-section">
                    <h2>System Status</h2>
                    
                    <div className="status-grid">
                        <div className="status-item">
                            <span className="status-label">Trend Monitor</span>
                            <span className="status-indicator status-active">● Active</span>
                        </div>
                        <div className="status-item">
                            <span className="status-label">Content Engine</span>
                            <span className="status-indicator status-active">● Active</span>
                        </div>
                        <div className="status-item">
                            <span className="status-label">Platform Manager</span>
                            <span className="status-indicator status-active">● Active</span>
                        </div>
                        <div className="status-item">
                            <span className="status-label">Database</span>
                            <span className="status-indicator status-active">● Connected</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* API Configuration Modal */}
            {showApiModal && (
                <Modal
                    title={`Configure ${selectedProvider} API`}
                    onClose={() => setShowApiModal(false)}
                >
                    <form onSubmit={handleApiKeySubmit} className="api-form">
                        <div className="form-group">
                            <label>API Key</label>
                            <input
                                type="password"
                                name="api_key"
                                placeholder="Enter your API key"
                                required
                            />
                        </div>
                        
                        <div className="form-group">
                            <small className="help-text">
                                {selectedProvider === 'openai' && 'Get your API key from platform.openai.com'}
                                {selectedProvider === 'groq' && 'Get your API key from console.groq.com'}
                                {selectedProvider === 'claude' && 'Get your API key from console.anthropic.com'}
                                {selectedProvider === 'leonardo' && 'Get your API key from app.leonardo.ai'}
                                {selectedProvider === 'elevenlabs' && 'Get your API key from elevenlabs.io'}
                                {selectedProvider === 'azure' && 'Configure your Azure Cognitive Services'}
                            </small>
                        </div>
                        
                        <div className="form-actions">
                            <button type="button" onClick={() => setShowApiModal(false)}>
                                Cancel
                            </button>
                            <button type="submit" className="primary-button">
                                Test & Save
                            </button>
                        </div>
                    </form>
                </Modal>
            )}
        </div>
    );
};

export default Settings;