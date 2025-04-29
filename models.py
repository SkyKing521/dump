from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

# Association table for many-to-many relationship between users and rooms
room_users = Table('room_users', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('room_id', Integer, ForeignKey('rooms.id'))
)

class Room(Base):
    __tablename__ = "rooms"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    is_public = Column(Boolean, default=True)
    password = Column(String, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    users = relationship("User", secondary=room_users, back_populates="rooms")
    messages = relationship("Message", back_populates="room")
    creator = relationship("User", back_populates="created_rooms") 