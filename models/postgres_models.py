"""
PostgreSQL models for master data (animal types and breeds).
These models are stored in PostgreSQL for consistency and performance.
"""
from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from db.base import Base


class AnimalType(Base):
    """Animal types model (master data)."""
    __tablename__ = "animal_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationship with breeds
    breeds = relationship("Breed", back_populates="animal_type", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AnimalType(name='{self.name}', active={self.is_active})>"


class Breed(Base):
    """Breeds model (master data)."""
    __tablename__ = "breeds"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    animal_type_id = Column(Integer, ForeignKey("animal_types.id"), nullable=False)
    description = Column(Text, nullable=True)
    origin = Column(String(100), nullable=True)
    characteristics = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationship with animal type
    animal_type = relationship("AnimalType", back_populates="breeds")
    
    # Unique constraint on breed name within animal type
    __table_args__ = (
        {"schema": None},
    )
    
    def __repr__(self):
        return f"<Breed(name='{self.name}', animal_type='{self.animal_type.name if self.animal_type else 'Unknown'}')>"
