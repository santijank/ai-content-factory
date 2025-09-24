import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import yaml
import os
from dataclasses import dataclass

# Import trend source collectors
from .youtube_trends import YouTubeTrendsCollector
from .google_trends import GoogleTrendsCollector
from .twitter_trends import TwitterTrendsCollector
from .reddit_trends import RedditTrendsCollector

from models.trend_data import TrendData, TrendBatch, TrendSource, merge_similar_trends

# Setup logging
logger = logging.getLogger(__name__)

@dataclass
class CollectorConfig:
    """Configuration for trend collector"""
    enabled: bool = True
    max_trends: int = 50
    timeout_seconds: int = 30
    retry_attempts: int = 3
    rate_limit_delay: float = 1.0
    
class TrendCollector:
    """Main orchestrator for trend collection from multiple sources"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.path.join(os.path.dirname(__file__), '../config/trend_sources.yaml')
        self.config = self._load_config()
        self.collectors = self._initialize_collectors()
        
        logger.info(f"TrendCollector initialized with {len(self.collectors)} active collectors")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        default_config = {
            'sources': {
                'youtube': {
                    'enabled': True,
                    'max_trends': 50,
                    'regions': ['US', 'GB', 'TH'],
                    'categories': ['all']
                },
                'google': {
                    'enabled': True,
                    'max_trends': 25,
                    'regions': ['US', 'TH'],
                    'timeframe': 'now 1-d'
                },
                'twitter': {
                    'enabled': False,  # Requires API keys
                    'max_trends': 30,
                    'locations': [1, 23424977]  # Worldwide, USA
                },
                'reddit': {
                    'enabled': True,
                    'max_trends': 25,
                    'subreddits': ['all', 'popular', 'trending']
                }
            },
            'collection': {
                'merge_similar': True,
                'similarity_threshold': 0.7,
                'min_popularity_score': 10.0,
                'max_total_trends': 200
            }
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = yaml.safe_load(f)
                    if loaded_config:
                        # Merge with defaults
                        default_config.update(loaded_config)
                        logger.info(f"Loaded config from {self.config_path}")
            except Exception as e:
                logger.warning(f"Error loading config file {self.config_path}: {e}")
                logger.info("Using default configuration")
        else:
            logger.info("Config file not found, using default configuration")
            
        return default_config
    
    def _initialize_collectors(self) -> Dict[str, Any]:
        """Initialize trend collectors based on configuration"""
        collectors = {}
        
        sources_config = self.config.get('sources', {})
        
        # YouTube collector
        if sources_config.get('youtube', {}).get('enabled', True):
            try:
                collectors['youtube'] = YouTubeTrendsCollector(
                    config=sources_config.get('youtube', {})
                )
                logger.info("YouTube trends collector initialized")
            except Exception as e:
                logger.error(f"Failed to initialize YouTube collector: {e}")
        
        # Google Trends collector
        if sources_config.get('google', {}).get('enabled', True):
            try:
                collectors['google'] = GoogleTrendsCollector(
                    config=sources_config.get('google', {})
                )
                logger.info("Google trends collector initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Google collector: {e}")
        
        # Twitter collector (optional)
        if sources_config.get('twitter', {}).get('enabled', False):
            try:
                collectors['twitter'] = TwitterTrendsCollector(
                    config=sources_config.get('twitter', {})
                )
                logger.info("Twitter trends collector initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Twitter collector: {e}")
        
        # Reddit collector
        if sources_config.get('reddit', {}).get('enabled', True):
            try:
                collectors['reddit'] = RedditTrendsCollector(
                    config=sources_config.get('reddit', {})
                )
                logger.info("Reddit trends collector initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Reddit collector: {e}")
        
        if not collectors:
            logger.warning("No trend collectors were successfully initialized!")
            
        return collectors
    
    async def collect_all_trends(self) -> List[TrendData]:
        """Collect trends from all enabled sources"""
        logger.info("Starting comprehensive trend collection...")
        
        all_trends = []
        collection_tasks = []
        
        # Create async tasks for each collector
        for source_name, collector in self.collectors.items():
            task = asyncio.create_task(
                self._collect_from_source(source_name, collector),
                name=f"collect_{source_name}"
            )
            collection_tasks.append(task)
        
        # Wait for all collections to complete
        if collection_tasks:
            results = await asyncio.gather(*collection_tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                source_name = list(self.collectors.keys())[i]
                
                if isinstance(result, Exception):
                    logger.error(f"Error collecting from {source_name}: {result}")
                elif isinstance(result, list):
                    all_trends.extend(result)
                    logger.info(f"Collected {len(result)} trends from {source_name}")
        
        # Post-process trends
        processed_trends = self._post_process_trends(all_trends)
        
        logger.info(f"Collection completed: {len(processed_trends)} trends after processing")
        return processed_trends
    
    async def _collect_from_source(self, source_name: str, collector) -> List[TrendData]:
        """Collect trends from a specific source with error handling"""
        try:
            logger.debug(f"Starting collection from {source_name}")
            
            # Set timeout for collection
            timeout = self.config.get('collection', {}).get('timeout_seconds', 30)
            
            trends = await asyncio.wait_for(
                collector.collect_trends(),
                timeout=timeout
            )
            
            if trends:
                logger.info(f"Successfully collected {len(trends)} trends from {source_name}")
                return trends
            else:
                logger.warning(f"No trends collected from {source_name}")
                return []
                
        except asyncio.TimeoutError:
            logger.error(f"Timeout collecting trends from {source_name}")
            return []
        except Exception as e:
            logger.error(f"Error collecting trends from {source_name}: {e}")
            return []
    
    def _post_process_trends(self, trends: List[TrendData]) -> List[TrendData]:
        """Post-process collected trends"""
        if not trends:
            return trends
        
        collection_config = self.config.get('collection', {})
        
        logger.info(f"Post-processing {len(trends)} raw trends...")
        
        # Filter by minimum popularity score
        min_score = collection_config.get('min_popularity_score', 10.0)
        filtered_trends = [t for t in trends if t.popularity_score >= min_score]
        
        if len(filtered_trends) != len(trends):
            logger.info(f"Filtered out {len(trends) - len(filtered_trends)} trends below score {min_score}")
        
        # Merge similar trends if enabled
        if collection_config.get('merge_similar', True):
            similarity_threshold = collection_config.get('similarity_threshold', 0.7)
            merged_trends = merge_similar_trends(filtered_trends, similarity_threshold)
            
            if len(merged_trends) != len(filtered_trends):
                logger.info(f"Merged {len(filtered_trends) - len(merged_trends)} similar trends")
            
            processed_trends = merged_trends
        else:
            processed_trends = filtered_trends
        
        # Sort by popularity score
        processed_trends.sort(key=lambda t: t.popularity_score, reverse=True)
        
        # Limit total number of trends
        max_trends = collection_config.get('max_total_trends', 200)
        if len(processed_trends) > max_trends:
            processed_trends = processed_trends[:max_trends]
            logger.info(f"Limited to top {max_trends} trends")
        
        # Add collection metadata
        for trend in processed_trends:
            if not trend.raw_data:
                trend.raw_data = {}
            trend.raw_data['processed_at'] = datetime.utcnow().isoformat()
            trend.raw_data['collection_batch'] = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        
        return processed_trends
    
    async def collect_from_specific_source(self, source: str) -> List[TrendData]:
        """Collect trends from a specific source only"""
        if source not in self.collectors:
            raise ValueError(f"Source '{source}' not available. Available sources: {list(self.collectors.keys())}")
        
        logger.info(f"Collecting trends from {source} only...")
        
        collector = self.collectors[source]
        trends = await self._collect_from_source(source, collector)
        
        # Apply basic post-processing
        processed_trends = self._post_process_trends(trends)
        
        logger.info(f"Collected {len(processed_trends)} trends from {source}")
        return processed_trends
    
    def get_sources_status(self) -> Dict[str, Any]:
        """Get status of all trend sources"""
        status = {}
        
        for source_name, collector in self.collectors.items():
            try:
                # Get basic collector info
                collector_status = {
                    'enabled': True,
                    'type': type(collector).__name__,
                    'last_collection': None,
                    'status': 'ready'
                }
                
                # Try to get more detailed status if collector supports it
                if hasattr(collector, 'get_status'):
                    collector_status.update(collector.get_status())
                
                status[source_name] = collector_status
                
            except Exception as e:
                status[source_name] = {
                    'enabled': False,
                    'status': 'error',
                    'error': str(e)
                }
        
        # Add sources that are configured but not initialized
        configured_sources = self.config.get('sources', {}).keys()
        for source_name in configured_sources:
            if source_name not in status:
                source_config = self.config['sources'][source_name]
                status[source_name] = {
                    'enabled': source_config.get('enabled', False),
                    'status': 'not_initialized',
                    'reason': 'Configuration disabled or initialization failed'
                }
        
        return status
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about trend collection"""
        stats = {
            'total_sources_configured': len(self.config.get('sources', {})),
            'active_collectors': len(self.collectors),
            'collection_config': self.config.get('collection', {}),
            'sources': {}
        }
        
        # Per-source stats
        for source_name in self.config.get('sources', {}).keys():
            source_config = self.config['sources'][source_name]
            
            stats['sources'][source_name] = {
                'enabled': source_config.get('enabled', False),
                'max_trends': source_config.get('max_trends', 0),
                'initialized': source_name in self.collectors
            }
        
        return stats
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all collectors"""
        health_status = {
            'overall_status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'collectors': {},
            'issues': []
        }
        
        for source_name, collector in self.collectors.items():
            try:
                # Quick health check - try to initialize a basic operation
                if hasattr(collector, 'health_check'):
                    collector_health = await collector.health_check()
                else:
                    # Basic check - just ensure collector is responsive
                    collector_health = {
                        'status': 'healthy',
                        'message': 'Collector is responsive'
                    }
                
                health_status['collectors'][source_name] = collector_health
                
                if collector_health.get('status') != 'healthy':
                    health_status['issues'].append(f"{source_name}: {collector_health.get('message', 'Unknown issue')}")
                    
            except Exception as e:
                health_status['collectors'][source_name] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
                health_status['issues'].append(f"{source_name}: {str(e)}")
        
        # Determine overall status
        unhealthy_count = sum(1 for c in health_status['collectors'].values() if c.get('status') != 'healthy')
        
        if unhealthy_count == 0:
            health_status['overall_status'] = 'healthy'
        elif unhealthy_count < len(self.collectors):
            health_status['overall_status'] = 'degraded'
        else:
            health_status['overall_status'] = 'unhealthy'
        
        return health_status
    
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """Update collector configuration"""
        try:
            # Validate new configuration
            if 'sources' not in new_config:
                raise ValueError("Configuration must contain 'sources' section")
            
            # Backup current config
            old_config = self.config.copy()
            
            # Update configuration
            self.config.update(new_config)
            
            # Re-initialize collectors with new config
            self.collectors = self._initialize_collectors()
            
            logger.info("Collector configuration updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update configuration: {e}")
            # Restore old configuration
            self.config = old_config
            self.collectors = self._initialize_collectors()
            return False
    
    def save_config(self, file_path: Optional[str] = None) -> bool:
        """Save current configuration to file"""
        try:
            save_path = file_path or self.config_path
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
            
            logger.info(f"Configuration saved to {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    async def test_collection(self, source: Optional[str] = None, limit: int = 5) -> Dict[str, Any]:
        """Test trend collection with limited results"""
        logger.info(f"Running test collection (limit: {limit})")
        
        test_results = {
            'timestamp': datetime.utcnow().isoformat(),
            'test_limit': limit,
            'results': {}
        }
        
        if source:
            # Test specific source
            if source not in self.collectors:
                test_results['error'] = f"Source '{source}' not available"
                return test_results
            
            try:
                trends = await self.collect_from_specific_source(source)
                test_results['results'][source] = {
                    'status': 'success',
                    'trend_count': len(trends),
                    'sample_trends': [
                        {
                            'topic': t.topic,
                            'score': t.popularity_score,
                            'source': t.source.value
                        } for t in trends[:limit]
                    ]
                }
            except Exception as e:
                test_results['results'][source] = {
                    'status': 'error',
                    'error': str(e)
                }
        else:
            # Test all sources
            for source_name, collector in self.collectors.items():
                try:
                    trends = await self._collect_from_source(source_name, collector)
                    limited_trends = trends[:limit] if trends else []
                    
                    test_results['results'][source_name] = {
                        'status': 'success',
                        'trend_count': len(trends),
                        'sample_trends': [
                            {
                                'topic': t.topic,
                                'score': t.popularity_score,
                                'source': t.source.value
                            } for t in limited_trends
                        ]
                    }
                except Exception as e:
                    test_results['results'][source_name] = {
                        'status': 'error',
                        'error': str(e)
                    }
        
        return test_results