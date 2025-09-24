"""
AI Content Factory - Database Repositories Package
===============================================

This package contains all repository classes for database operations.
Repositories provide a clean abstraction layer over database models,
implementing common CRUD operations and business-specific queries.

Repositories included:
- TrendRepository: Trend data access and analysis
- OpportunityRepository: Content opportunity management
- ContentRepository: Content item operations
- PerformanceRepository: Performance metrics and analytics

Architecture:
    Repository Pattern - Encapsulates data access logic
    Unit of Work - Manages transactions and consistency
    Specification Pattern - Flexible query building

Usage:
    from database.repositories import TrendRepository, UnitOfWork
    
    with UnitOfWork() as uow:
        trends = uow.trends.get_trending_topics(limit=10)
        uow.commit()
"""

from typing import Dict, Any, Type
from contextlib import contextmanager
from sqlalchemy.orm import Session

# Import base repository
from .base_repository import BaseRepository

# Import all repositories
from .trend_repository import TrendRepository
from .opportunity_repository import OpportunityRepository  
from .content_repository import ContentRepository
from .performance_repository import PerformanceRepository

# Repository registry
REPOSITORY_REGISTRY: Dict[str, Type[BaseRepository]] = {
    'trends': TrendRepository,
    'opportunities': OpportunityRepository,
    'content': ContentRepository,
    'performance': PerformanceRepository
}

# Export all repositories
__all__ = [
    # Base classes
    'BaseRepository',
    'UnitOfWork',
    'RepositoryManager',
    
    # Repositories
    'TrendRepository',
    'OpportunityRepository', 
    'ContentRepository',
    'PerformanceRepository',
    
    # Utilities
    'REPOSITORY_REGISTRY',
    'get_repository',
    'create_repository_manager'
]

class UnitOfWork:
    """
    Unit of Work pattern implementation for managing database transactions.
    
    This class ensures that all repository operations within a context
    are executed within a single database transaction.
    
    Usage:
        with UnitOfWork() as uow:
            trend = uow.trends.create({...})
            opportunity = uow.opportunities.create({...})
            uow.commit()  # Commits both operations
    """
    
    def __init__(self, session: Session = None):
        self.session = session
        self._repositories = {}
        self._committed = False
        
    def __enter__(self):
        if not self.session:
            from database.config.database_config import get_db_session
            self.session = get_db_session()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        elif not self._committed:
            self.rollback()
        self.session.close()
        
    def commit(self):
        """Commit all pending changes."""
        if not self._committed:
            self.session.commit()
            self._committed = True
            
    def rollback(self):
        """Rollback all pending changes."""
        self.session.rollback()
        
    @property
    def trends(self) -> TrendRepository:
        """Get trends repository."""
        if 'trends' not in self._repositories:
            self._repositories['trends'] = TrendRepository(self.session)
        return self._repositories['trends']
        
    @property  
    def opportunities(self) -> OpportunityRepository:
        """Get opportunities repository."""
        if 'opportunities' not in self._repositories:
            self._repositories['opportunities'] = OpportunityRepository(self.session)
        return self._repositories['opportunities']
        
    @property
    def content(self) -> ContentRepository:
        """Get content repository."""
        if 'content' not in self._repositories:
            self._repositories['content'] = ContentRepository(self.session)
        return self._repositories['content']
        
    @property
    def performance(self) -> PerformanceRepository:
        """Get performance repository."""
        if 'performance' not in self._repositories:
            self._repositories['performance'] = PerformanceRepository(self.session)
        return self._repositories['performance']

class RepositoryManager:
    """
    Manages repository instances and provides unified access.
    
    This class creates and manages repository instances,
    ensuring proper session handling and consistency.
    """
    
    def __init__(self, session: Session):
        self.session = session
        self._repositories = {}
        
    def get_repository(self, name: str) -> BaseRepository:
        """
        Get repository by name.
        
        Args:
            name: Repository name ('trends', 'opportunities', etc.)
            
        Returns:
            Repository instance
            
        Raises:
            ValueError: If repository name not found
        """
        if name not in REPOSITORY_REGISTRY:
            raise ValueError(f"Repository '{name}' not found")
            
        if name not in self._repositories:
            repo_class = REPOSITORY_REGISTRY[name]
            self._repositories[name] = repo_class(self.session)
            
        return self._repositories[name]
        
    @property
    def trends(self) -> TrendRepository:
        """Get trends repository."""
        return self.get_repository('trends')
        
    @property
    def opportunities(self) -> OpportunityRepository:
        """Get opportunities repository."""
        return self.get_repository('opportunities')
        
    @property
    def content(self) -> ContentRepository:
        """Get content repository.""" 
        return self.get_repository('content')
        
    @property
    def performance(self) -> PerformanceRepository:
        """Get performance repository."""
        return self.get_repository('performance')

def get_repository(name: str, session: Session = None) -> BaseRepository:
    """
    Get a single repository instance.
    
    Args:
        name: Repository name
        session: Database session (optional)
        
    Returns:
        Repository instance
        
    Example:
        trends_repo = get_repository('trends')
        trends = trends_repo.get_trending_topics()
    """
    if name not in REPOSITORY_REGISTRY:
        raise ValueError(f"Repository '{name}' not found")
        
    if not session:
        from database.config.database_config import get_db_session
        session = get_db_session()
        
    repo_class = REPOSITORY_REGISTRY[name]
    return repo_class(session)

def create_repository_manager(session: Session = None) -> RepositoryManager:
    """
    Create a repository manager instance.
    
    Args:
        session: Database session (optional)
        
    Returns:
        RepositoryManager instance
        
    Example:
        repos = create_repository_manager()
        trends = repos.trends.get_all()
    """
    if not session:
        from database.config.database_config import get_db_session
        session = get_db_session()
        
    return RepositoryManager(session)

# Convenience functions for common operations
@contextmanager
def transaction():
    """
    Context manager for database transactions.
    
    Usage:
        with transaction() as repos:
            trend = repos.trends.create({...})
            opportunity = repos.opportunities.create({...})
            # Auto-commits on success, rolls back on error
    """
    with UnitOfWork() as uow:
        try:
            yield uow
            uow.commit()
        except Exception:
            uow.rollback()
            raise

def batch_operation(operations: list, batch_size: int = 100):
    """
    Execute multiple operations in batches.
    
    Args:
        operations: List of operation functions
        batch_size: Number of operations per batch
        
    Example:
        operations = [
            lambda uow: uow.trends.create({'topic': 'AI'}),
            lambda uow: uow.trends.create({'topic': 'ML'}),
        ]
        batch_operation(operations)
    """
    total_operations = len(operations)
    
    for i in range(0, total_operations, batch_size):
        batch = operations[i:i + batch_size]
        
        with UnitOfWork() as uow:
            for operation in batch:
                operation(uow)
            uow.commit()

# Repository health check
def health_check() -> Dict[str, Any]:
    """
    Check repository health and connectivity.
    
    Returns:
        Dictionary with health status information
    """
    results = {
        'status': 'healthy',
        'repositories': {},
        'errors': []
    }
    
    try:
        with UnitOfWork() as uow:
            # Test each repository
            for name, repo_class in REPOSITORY_REGISTRY.items():
                try:
                    repo = getattr(uow, name)
                    # Try a simple operation
                    count = repo.count()
                    results['repositories'][name] = {
                        'status': 'healthy',
                        'record_count': count
                    }
                except Exception as e:
                    results['repositories'][name] = {
                        'status': 'unhealthy', 
                        'error': str(e)
                    }
                    results['errors'].append(f"{name}: {str(e)}")
                    
            if results['errors']:
                results['status'] = 'degraded'
                
    except Exception as e:
        results['status'] = 'unhealthy'
        results['errors'].append(f"Database connection: {str(e)}")
        
    return results

# Version info
__version__ = "1.0.0"
__repository_version__ = "1.0.0"

# Repository metadata
REPOSITORY_INFO = {
    'TrendRepository': {
        'description': 'Manages trending topics and analysis',
        'model': 'Trend',
        'primary_operations': ['get_trending_topics', 'analyze_trends', 'get_by_source']
    },
    'OpportunityRepository': {
        'description': 'Manages content opportunities',
        'model': 'ContentOpportunity', 
        'primary_operations': ['get_top_opportunities', 'update_status', 'get_by_trend']
    },
    'ContentRepository': {
        'description': 'Manages generated content items',
        'model': 'ContentItem',
        'primary_operations': ['create_content', 'update_status', 'get_by_opportunity']
    },
    'PerformanceRepository': {
        'description': 'Manages performance metrics and analytics',
        'model': 'PerformanceMetric',
        'primary_operations': ['record_metrics', 'get_analytics', 'get_by_upload']
    }
}