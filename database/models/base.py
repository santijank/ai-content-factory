"""
Database Base Configuration
SQLAlchemy setup and base model
"""

import os
from datetime import datetime
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID
import uuid

# Database URL from environment or default to SQLite
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///ai_content_factory.db')

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=os.getenv('SQL_DEBUG', 'false').lower() == 'true',
    pool_pre_ping=True
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class
Base = declarative_base()

class BaseModel(Base):
    """Base model with common fields"""
    __abstract__ = True
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def get_db_session():
    """Get database session"""
    return SessionLocal()

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")

def drop_db():
    """Drop all database tables"""
    Base.metadata.drop_all(bind=engine)
    print("🗑️ Database tables dropped")

def reset_db():
    """Reset database (drop and recreate)"""
    drop_db()
    init_db()
    print("🔄 Database reset completed")

# Context manager for database sessions
class DatabaseSession:
    def __init__(self):
        self.session = None
    
    def __enter__(self):
        self.session = get_db_session()
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()

def get_db():
    """Dependency for getting database session"""
    db = get_db_session()
    try:
        yield db
    finally:
        db.close()