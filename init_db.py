from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, Table, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime
from werkzeug.security import generate_password_hash
from config import DATABASE_URL
import os

Base = declarative_base()

# Association table for many-to-many relationship between users and rooms
user_rooms = Table('user_rooms', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('room_id', Integer, ForeignKey('rooms.id'))
)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    nickname = Column(String(50), nullable=True)
    password_hash = Column(String(128), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    avatar_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_online = Column(Boolean, default=False)
    microphone_enabled = Column(Boolean, default=True)
    camera_enabled = Column(Boolean, default=True)
    
    # Relationship with rooms
    rooms = relationship("Room", secondary=user_rooms, back_populates="users")
    
    def get_display_name(self):
        return self.nickname if self.nickname else self.username

class Room(Base):
    __tablename__ = 'rooms'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_public = Column(Boolean, default=True)
    created_by_id = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    users = relationship("User", secondary=user_rooms, back_populates="rooms")
    created_by = relationship("User", foreign_keys=[created_by_id])
    messages = relationship('Message', back_populates='room')

class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey('rooms.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    room = relationship("Room")
    user = relationship("User")

# Create database engine
engine = create_engine(DATABASE_URL)

# Create all tables
Base.metadata.create_all(engine)

# Create a session
Session = sessionmaker(bind=engine)
session = Session()

# Check if admin user exists
admin = session.query(User).filter_by(username='admin').first()
if not admin:
    # Create admin user with default settings
    admin = User(
        username='admin',
        password_hash=generate_password_hash('admin'),
        email='admin@example.com',
        is_online=False,
        microphone_enabled=True,
        camera_enabled=True
    )
    session.add(admin)
    
    # Create default room
    default_room = Room(
        name='General',
        created_by=admin,
        is_public=True
    )
    default_room.users.append(admin)
    session.add(default_room)
    
    session.commit()

session.close()
print("Database initialized successfully!") 