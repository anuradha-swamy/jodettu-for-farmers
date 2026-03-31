from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class AnimalType(Base):
    __tablename__ = "animal_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    
    breeds = relationship("Breed", back_populates="animal_type")

class Breed(Base):
    __tablename__ = "breeds"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    animal_type_id = Column(Integer, ForeignKey("animal_types.id"))
    is_active = Column(Boolean, default=True)

    animal_type = relationship("AnimalType", back_populates="breeds")
