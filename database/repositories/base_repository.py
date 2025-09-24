"""
AI Content Factory - Base Repository
==================================

Base repository class providing common CRUD operations and utilities
for all repository implementations.
"""

from typing import List, Optional, Dict, Any, Type, Union
from abc import ABC, abstractmethod
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_, desc, asc, func

from database.models.base import BaseModel


class BaseRepository(ABC):
    """
    Abstract base class for all repositories.
    
    Provides common CRUD operations and query utilities
    that can be inherited by specific repository implementations.
    """
    
    def __init__(self, session: Session, model: Type[BaseModel]):
        """
        Initialize repository.
        
        Args:
            session: SQLAlchemy session
            model: Model class this repository manages
        """
        self.session = session
        self.model = model
        
    # Basic CRUD Operations
    
    def create(self, data: Dict[str, Any]) -> BaseModel:
        """
        Create a new record.
        
        Args:
            data: Dictionary of field values
            
        Returns:
            Created model instance
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            instance = self.model(**data)
            self.session.add(instance)
            self.session.flush()  # Get ID without committing
            return instance
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
            
    def get_by_id(self, id: Union[UUID, str, int]) -> Optional[BaseModel]:
        """
        Get record by ID.
        
        Args:
            id: Record ID
            
        Returns:
            Model instance if found, None otherwise
        """
        return self.session.query(self.model).filter(self.model.id == id).first()
        
    def get_all(self, limit: int = None, offset: int = None) -> List[BaseModel]:
        """
        Get all records with optional pagination.
        
        Args:
            limit: Maximum number of records
            offset: Number of records to skip
            
        Returns:
            List of model instances
        """
        query = self.session.query(self.model)
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
            
        return query.all()
        
    def update(self, id: Union[UUID, str, int], data: Dict[str, Any]) -> Optional[BaseModel]:
        """
        Update record by ID.
        
        Args:
            id: Record ID
            data: Dictionary of fields to update
            
        Returns:
            Updated model instance if found, None otherwise
        """
        instance = self.get_by_id(id)
        if instance:
            for key, value in data.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            self.session.flush()
        return instance
        
    def delete(self, id: Union[UUID, str, int]) -> bool:
        """
        Delete record by ID.
        
        Args:
            id: Record ID
            
        Returns:
            True if deleted, False if not found
        """
        instance = self.get_by_id(id)
        if instance:
            self.session.delete(instance)
            self.session.flush()
            return True
        return False
        
    def count(self, filters: Dict[str, Any] = None) -> int:
        """
        Count records with optional filters.
        
        Args:
            filters: Dictionary of field filters
            
        Returns:
            Number of matching records
        """
        query = self.session.query(func.count(self.model.id))
        
        if filters:
            query = self._apply_filters(query, filters)
            
        return query.scalar()
        
    # Query Building Utilities
    
    def find_by(self, **kwargs) -> List[BaseModel]:
        """
        Find records by field values.
        
        Args:
            **kwargs: Field name and value pairs
            
        Returns:
            List of matching model instances
            
        Example:
            users = repo.find_by(name="John", active=True)
        """
        query = self.session.query(self.model)
        
        for field, value in kwargs.items():
            if hasattr(self.model, field):
                query = query.filter(getattr(self.model, field) == value)
                
        return query.all()
        
    def find_one_by(self, **kwargs) -> Optional[BaseModel]:
        """
        Find single record by field values.
        
        Args:
            **kwargs: Field name and value pairs
            
        Returns:
            First matching model instance or None
        """
        results = self.find_by(**kwargs)
        return results[0] if results else None
        
    def exists(self, **kwargs) -> bool:
        """
        Check if record exists with given field values.
        
        Args:
            **kwargs: Field name and value pairs
            
        Returns:
            True if record exists, False otherwise
        """
        query = self.session.query(self.model.id)
        
        for field, value in kwargs.items():
            if hasattr(self.model, field):
                query = query.filter(getattr(self.model, field) == value)
                
        return query.first() is not None
        
    # Advanced Query Methods
    
    def find_in_range(self, field: str, start: Any, end: Any) -> List[BaseModel]:
        """
        Find records where field value is in range.
        
        Args:
            field: Field name
            start: Range start value
            end: Range end value
            
        Returns:
            List of matching records
        """
        if not hasattr(self.model, field):
            raise ValueError(f"Field '{field}' not found in model")
            
        model_field = getattr(self.model, field)
        return self.session.query(self.model).filter(
            and_(model_field >= start, model_field <= end)
        ).all()
        
    def find_recent(self, field: str = 'created_at', hours: int = 24) -> List[BaseModel]:
        """
        Find records created in the last N hours.
        
        Args:
            field: Date/datetime field name
            hours: Number of hours to look back
            
        Returns:
            List of recent records
        """
        if not hasattr(self.model, field):
            raise ValueError(f"Field '{field}' not found in model")
            
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        model_field = getattr(self.model, field)
        
        return self.session.query(self.model).filter(
            model_field >= cutoff
        ).order_by(desc(model_field)).all()
        
    def search(self, query: str, fields: List[str]) -> List[BaseModel]:
        """
        Search records by text in specified fields.
        
        Args:
            query: Search query string
            fields: List of field names to search in
            
        Returns:
            List of matching records
        """
        if not query:
            return []
            
        search_filters = []
        for field in fields:
            if hasattr(self.model, field):
                model_field = getattr(self.model, field)
                search_filters.append(model_field.ilike(f"%{query}%"))
                
        if not search_filters:
            return []
            
        return self.session.query(self.model).filter(
            or_(*search_filters)
        ).all()
        
    # Batch Operations
    
    def bulk_create(self, data_list: List[Dict[str, Any]]) -> List[BaseModel]:
        """
        Create multiple records in batch.
        
        Args:
            data_list: List of data dictionaries
            
        Returns:
            List of created model instances
        """
        instances = []
        try:
            for data in data_list:
                instance = self.model(**data)
                self.session.add(instance)
                instances.append(instance)
                
            self.session.flush()
            return instances
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
            
    def bulk_update(self, updates: List[Dict[str, Any]]) -> int:
        """
        Update multiple records in batch.
        
        Args:
            updates: List of dictionaries with 'id' and update data
            
        Returns:
            Number of records updated
        """
        updated_count = 0
        
        try:
            for update_data in updates:
                record_id = update_data.pop('id', None)
                if record_id and update_data:
                    result = self.session.query(self.model).filter(
                        self.model.id == record_id
                    ).update(update_data)
                    updated_count += result
                    
            self.session.flush()
            return updated_count
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
            
    # Helper Methods
    
    def _apply_filters(self, query, filters: Dict[str, Any]):
        """
        Apply filters to a query.
        
        Args:
            query: SQLAlchemy query object
            filters: Dictionary of filters
            
        Returns:
            Filtered query object
        """
        for field, value in filters.items():
            if hasattr(self.model, field):
                model_field = getattr(self.model, field)
                
                if isinstance(value, list):
                    query = query.filter(model_field.in_(value))
                elif isinstance(value, dict):
                    # Handle complex filters like {'gt': 10, 'lt': 100}
                    if 'gt' in value:
                        query = query.filter(model_field > value['gt'])
                    if 'lt' in value:
                        query = query.filter(model_field < value['lt'])
                    if 'gte' in value:
                        query = query.filter(model_field >= value['gte'])
                    if 'lte' in value:
                        query = query.filter(model_field <= value['lte'])
                    if 'like' in value:
                        query = query.filter(model_field.ilike(f"%{value['like']}%"))
                else:
                    query = query.filter(model_field == value)
                    
        return query
        
    def _apply_ordering(self, query, order_by: Union[str, List[str]]):
        """
        Apply ordering to a query.
        
        Args:
            query: SQLAlchemy query object
            order_by: Field name(s) for ordering
            
        Returns:
            Ordered query object
        """
        if isinstance(order_by, str):
            order_by = [order_by]
            
        for field in order_by:
            if field.startswith('-'):
                # Descending order
                field_name = field[1:]
                if hasattr(self.model, field_name):
                    query = query.order_by(desc(getattr(self.model, field_name)))
            else:
                # Ascending order
                if hasattr(self.model, field):
                    query = query.order_by(asc(getattr(self.model, field)))
                    
        return query
        
    # Pagination
    
    def paginate(self, page: int = 1, per_page: int = 20, filters: Dict[str, Any] = None, 
                 order_by: Union[str, List[str]] = None) -> Dict[str, Any]:
        """
        Paginated query with optional filters and ordering.
        
        Args:
            page: Page number (1-based)
            per_page: Records per page
            filters: Optional filters dictionary
            order_by: Optional ordering field(s)
            
        Returns:
            Dictionary with pagination metadata and results
        """
        query = self.session.query(self.model)
        
        # Apply filters
        if filters:
            query = self._apply_filters(query, filters)
            
        # Apply ordering  
        if order_by:
            query = self._apply_ordering(query, order_by)
            
        # Count total records
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        items = query.offset(offset).limit(per_page).all()
        
        # Calculate pagination metadata
        total_pages = (total + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < total_pages
        
        return {
            'items': items,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'has_prev': has_prev,
            'has_next': has_next,
            'prev_page': page - 1 if has_prev else None,
            'next_page': page + 1 if has_next else None
        }