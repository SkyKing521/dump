# Это надо для работы с БД и только с БД
from datetime import datetime, timezone
from sqlalchemy import  Boolean, text
from .database import Base
from enum import Enum

from sqlalchemy import (
     Integer, String, ForeignKey, DateTime, Enum as SQLEnum,
)
from sqlalchemy.orm import (
     relationship,
    mapped_column, Mapped
)

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    nickname: Mapped[str] = mapped_column(String(50), nullable=True)
    email:Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128))
    salt: Mapped[str] = mapped_column(String(64))  # Новое поле для salt
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("TIMEZONE('utc', now())")
    )

    sent_messages: Mapped[list["Message"]] = relationship(back_populates="sender")
    memberships: Mapped[list["GroupMember"]] = relationship(back_populates="user")

    # Исходящие контакты (где этот пользователь инициатор)
    outgoing_contacts: Mapped[list["UserContact"]] = relationship(
        foreign_keys="UserContact.user_id",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    # Входящие контакты (где этот пользователь получатель)
    incoming_contacts: Mapped[list["UserContact"]] = relationship(
        foreign_keys="UserContact.contact_id",
        back_populates="contact",
        cascade="all, delete-orphan"
    )

# Типы отношений между пользователями
class RelationshipStatus(Enum):
    PENDING = "pending"     # Запрос отправлен, ожидает подтверждения
    APPROVED = "approved"   # Контакт подтвержден
    BLOCKED = "blocked"    # Пользователь заблокирован
    DELETED = "deleted"    # Контакт удален


# Модель связи между пользователями
class UserContact(Base):
    __tablename__ = 'user_contacts'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    contact_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    custom_nickname: Mapped[str] = mapped_column(String(50),nullable=True) #имя, которое даёт сам пользователь
    status: Mapped[RelationshipStatus] = mapped_column(SQLEnum(RelationshipStatus), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связь с пользователем-инициатором
    user: Mapped["User"] = relationship(
        foreign_keys=[user_id],
        back_populates="outgoing_contacts"
    )

    # Связь с пользователем-контактом
    contact: Mapped["User"] = relationship(
        foreign_keys=[contact_id],
        back_populates="incoming_contacts"
    )

    def __repr__(self):
        return f"<UserContact(id={self.id}, user={self.user_id}, contact={self.contact_id}, status={self.status.value})>"

class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("TIMEZONE('utc', now())")
    )

    members: Mapped[list["GroupMember"]] = relationship(back_populates="group")
    messages: Mapped[list["Message"]] = relationship(back_populates="group")


class GroupMember(Base):
    __tablename__ = "group_members"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    joined_at: Mapped[datetime] = mapped_column(
        server_default=text("TIMEZONE('utc', now())")
    )

    group: Mapped["Group"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="memberships")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(String(500))
    is_group: Mapped[bool] = mapped_column(Boolean, default=False)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    receiver_id: Mapped[int | None] = mapped_column(nullable=True)
    group_id: Mapped[int | None] = mapped_column(ForeignKey("groups.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("TIMEZONE('utc', now())")
    )

    sender: Mapped["User"] = relationship(back_populates="sent_messages")
    group: Mapped["Group | None"] = relationship(back_populates="messages")