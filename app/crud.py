from sqlalchemy import select, insert
from sqlalchemy.sql.sqltypes import NULLTYPE

from .msg_models import User, Group, GroupMember, Message
from .msg_schemas import UserSchema, GroupSchema
#from .database import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession


class UserCRUD:
    @staticmethod
    async def create_user(
        session : AsyncSession,
        user_data: dict
    ) -> dict:
        result = await session.execute(
            insert(User).values(
                username=user_data['username'],
                salt=user_data['salt'],
                password_hash=user_data['password_hash'],
                email=user_data['email']
            ).returning(User)
        )
        await session.commit()
        return UserSchema().dump(result.scalar_one())

    @staticmethod
    # поиск пользователя по имени
    async def get_user_by_username(session: AsyncSession, username: str):
        result = await session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()  # Возвращает модель User


class GroupCRUD:
    @staticmethod
    async def create_group(session, name: str, creator_id: int, members: list[int]):
        async with session.begin():
            group = Group(name=name, creator_id=creator_id)
            session.add(group)
            await session.flush()

            members = [GroupMember(group_id=group.id, user_id=uid) for uid in members]
            session.add_all(members)

            await session.commit()
            return group

    @staticmethod
    async def get_group(session, group_id: int):
        result = await session.execute(
            select(Group).where(Group.id == group_id)
        )
        return result.scalar_one_or_none()


class MessageCRUD:
    @staticmethod
    async def create_message(session:AsyncSession, content: str, sender_id: int,
                             receiver_id: int = None, group_id: int = None):
        message = Message(
            content=content,
            sender_id=sender_id,
            receiver_id=receiver_id,
            group_id=group_id,
            is_group=bool(group_id)
        )

        session.add(message)
        await session.commit()
        return message

    @staticmethod
    async def create_private_message(session:AsyncSession, udata, sender_id):
        message = Message(
            content=udata['content'],
            sender_id=sender_id,
            receiver_id=udata['receiver_id'],
            #group_id=,
            #is_group=bool(group_id)
        )

        session.add(message)
        await session.commit()
        return message