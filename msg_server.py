import asyncio
import websockets
import json
import hashlib
import os
from datetime import datetime, timezone
from marshmallow import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from app.crud import UserCRUD, GroupCRUD, MessageCRUD
from app.msg_schemas import (
    AuthSchema,
    CreateGroupSchema,
    PrivateMessageSchema,
    UserSchema,
    GroupSchema,
    GroupMessageSchema,
    GetUserContactsSchema,
    UserContactsSchema, UserContactsClass, OneContactClass, UserContactsClass,
)
from app.database import engine, Base
from app.msg_models import Message,UserContact,User, RelationshipStatus
from enum import Enum


# Для хранения состояния соединения
class ConnectionState:

    class ConnectionStateEnum(Enum):
        Connected = 1
        Authorized = 2
    def __init__(self):
        self.state: ConnectionState = self.ConnectionStateEnum.Connected
        self.userId: int = -1

# асинхронная сессия
GetSession = async_sessionmaker(engine, expire_on_commit=False)

class MessengerServer:
    def __init__(self):
        # список активных соединений вместе с номером пользователя (user_id) это словарь user-ID->websocket
        self.active_connections = {}
        # для работы с БД асинхронная сессия
        self.async_session = async_sessionmaker(engine, expire_on_commit=False)

    # region Database Initialization
    async def init_db(self):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database initialized")
    # endregion

    # region Connection Handling обработка входящих подключений
    async def handle_connection(self, websocket):
        try:
            state = ConnectionState()
            state.ConnectionStateEnum = ConnectionState.ConnectionStateEnum.Connected;
            print(f"connect from {websocket}")
            #Получение пакета
            async for message in websocket:
                await self.route_message(websocket, message, state)
        except websockets.ConnectionClosed:
            await self.handle_disconnect(websocket)

    # обработка отключений
    async def handle_disconnect(self, websocket):
        user_id = next((uid for uid, ws in self.active_connections.items() if ws == websocket), None)
        if user_id:
            del self.active_connections[user_id]
            print(f"User {user_id} disconnected")

    # endregion

    # region определение обработчика сообщения
    async def route_message(self, websocket, raw_data: dict, state :ConnectionState):
        try:
            data = json.loads(raw_data)
            message_type: str = data.get('type')

            schema = self.get_schema_for_type(message_type)
            if not schema:
                await self.send_error(websocket, f"Invalid message type: {message_type}")
                return

            print(f"получили сообщение типа {message_type}")
            # разобранный по правилам схемы dict из JSON
            validated = schema.load(data)

            # получение обработка по имени
            handler = getattr(self, f"handle_{validated['type']}", None)

            if state.state == ConnectionState.ConnectionStateEnum.Connected:
                if message_type in {"login", "register"}:
                    await handler(websocket, validated, state)
                else:
                    await self.send_error(websocket, f"Unauthorized")
                    return


            # ВЫЗОВ Обработчика
            if handler:
                await handler(websocket, validated,state)
            else:
                await self.send_error(websocket, f"Unhandled message type: {message_type}")

        except json.JSONDecodeError:
            await self.send_error(websocket, "Invalid JSON format")
        except ValidationError as e:
            await self.send_error(websocket, f"Validation error: {e.messages}")
        except Exception as e:
            await self.send_error(websocket, f"Server error: {str(e)}")

    # по словарю получаем, какая схема JSON какому типу сообщения нужна
    def get_schema_for_type(self, message_type):
        return {
            'register': AuthSchema(),
            'login': AuthSchema(),
            'create_group': CreateGroupSchema(),
            'private_message': PrivateMessageSchema(),
            'group_message': GroupMessageSchema(),
            'get_user_contacts' : GetUserContactsSchema()
        }.get(message_type)

    # endregion

    # region Response Helpers
    async def send_success(self, websocket, message_type, data:dict=None):
        response = {
            "type": message_type,
            "status": "success",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        if data:
            response["data"] = data
        await websocket.send(json.dumps(response))

    async def send_error(self, websocket, message):
        error_msg = {
            "type": "error",
            "status": "error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": message
        }
        await websocket.send(json.dumps(error_msg))

    # endregion

    # region Обработчики
    async def handle_register(self, websocket, data, state : ConnectionState):
        try:
            async with self.async_session() as session:
                # Генерация нового salt для каждого пользователя
                salt = os.urandom(32)

                # Создание пользователя с раздельным хранением salt и хеша
                user_data = {
                    "username": data['username'],
                    "salt": salt.hex(),
                    "password_hash": self.hash_password(data['password'], salt),
                    "email" : data['email']
                }

                user = await UserCRUD.create_user(session, user_data)
                self.active_connections[user['id']] = websocket

                user.remove('password_hash')
                user.remove('salt')

                await self.send_success(websocket, "auth_success", user)
                state.state = ConnectionState.ConnectionStateEnum.Authorized
                state.userId = user['id']
        except Exception as e:
            await self.send_error(websocket, str(e))
            """ типа комментарий """

    # Обработка входа
    async def handle_login(self, websocket, data:dict, state: ConnectionState):
        try:
            # правильное получени сесии асихронной работы с БД
            async with self.async_session() as session:
                # Получаем пользователя как SQLAlchemy модель
                user_model: User = await UserCRUD.get_user_by_username(session, data['username'])

                # Конвертируем модель в словарь через схему
                user_dict = UserSchema().dump(user_model)
                salt = bytes.fromhex(user_dict['salt'])

                # Проверяем пароль
                test_hash = self.hash_password(data['password'], salt)

                if user_dict['password_hash'] == test_hash:
                    self.active_connections[user_dict['id']] = websocket
                    del user_dict['password_hash']
                    del user_dict['salt']
                    state.state = ConnectionState.ConnectionStateEnum.Authorized
                    state.userId = user_model.id

                    await self.send_success(websocket, "auth_success", user_dict)
                    return

            await self.send_error(websocket, "Invalid credentials")

        except Exception as e:
            await self.send_error(websocket, str(e))

    # создание группы не доделано пока и не понятно зачем
    async def handle_create_group(self, websocket, data,state: ConnectionState):
        try:
            async for session in self.session:
                group = await GroupCRUD.create_group(session, data)
                await self.send_success(websocket, "group_created", group)

        except Exception as e:
            await self.send_error(websocket, str(e))

    """
    Обработка сообщения для другого получателя
    """
    async def handle_private_message(self, websocket, data,state: ConnectionState):
        try:
            user_id = list(self.active_connections.keys()) # Для определения текущего пользователя
            [list(self.active_connections.values()).index(websocket)]

            async with self.async_session() as session:
                message = await MessageCRUD.create_private_message(session, data, user_id[0])

                await self.send_private_message(message, session)
                await self.send_success(websocket, "message_sent", data)

        except Exception as e:
            await self.send_error(websocket, str(e))
    """
    отправляет частное сообщение
    """
    async def send_private_message(self, message: Message, session: AsyncSession):
        """
        Отправляет приватное сообщение конкретному пользователю
        и обновляет статус доставки
        """
        try:
            # Сериализация сообщения
            message_data = {
                "type": "private_message",
                "id": message.id,
                "sender_id": message.sender_id,
                "receiver_id" : message.receiver_id,
                "content": message.content,
                "created_at": message.created_at.isoformat(),
                "is_group": False
            }

            # Получаем соединение получателя
            receiver_ws = self.active_connections.get(message.receiver_id)

            if receiver_ws:
                try:
                    # Отправляем сообщение через WebSocket
                    await receiver_ws.send(json.dumps(message_data))

                    # Обновляем статус доставки в БД
                    #async with self.async_session() as session:
                    #    async with session.begin():
                    message.is_delivered = True
                    message.delivered_at = datetime.now(timezone.utc)
                    #session.add(message)
                    await session.commit()

                except websockets.ConnectionClosed:
                    # Обработка закрытого соединения
                    #async with self.async_session() as session:
                    #    async with session.begin():
                    message.is_delivered = False
                    #session.add(message)
                    await session.commit()

                    # Удаляем из активных подключений
                    del self.active_connections[message.receiver_id]
                    print(f"User {message.receiver_id} disconnected")

            else:
                # Помечаем сообщение как недоставленное
                #async with self.async_session() as session:
                    #async with session.begin():
                message.is_delivered = False
#                session.add(message)
                await session.commit()

        except Exception as e:
            print(f"Error sending private message: {str(e)}")
            # Логирование ошибки или повторная попытка отправки

    """
        получение и обоработка контактов пользователя
     """

    async def handle_get_user_contacts(self, websocket, data,state: ConnectionState):
        try:
            async with self.async_session() as session:
                try:
                    # Получаем контакты пользователя
                    result = await session.execute(
                        select(UserContact, User.username)
                        .join(User, UserContact.contact_id == User.id)  # JOIN с таблицей пользователей
                        .where(UserContact.user_id == state.userId)
                    )

                    contacts=  result.all()

                    ch = UserContactsSchema()

                    cons : UserContactsClass = UserContactsClass()


                    for cor in contacts:
                        con = OneContactClass()
                        con.status = cor.UserContact.status.value
                        con.custom_nickname = cor.UserContact.custom_nickname
                        con.user_id = cor.UserContact.contact_id
                        con.user_name = cor.username

                        cons.contacts.append(con)
                except Exception as e:
                    print(e)
                data = ch.dumps(cons)
                await websocket.send(data)
        except Exception as e:
            await self.send_error(websocket, str(e))


    # endregion

    # region Utility Methods
    @staticmethod
    def hash_password(password: str, salt: bytes) -> str:
        """Генерация хеша пароля с использованием предоставленного salt"""
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000
        )
        return key.hex()
    # endregion


# инициализация данных чтобы не возиться каждый раз
async def InitDBSampleData():
    try:
        async with GetSession() as session:
            # Получаем контакты пользователя
            result = await session.execute(
                select(User)
                .where(User.username == "user1")
            )
            user = result.first();
            if not user:
                # Генерация нового salt для каждого пользователя
                salt = os.urandom(32)
                # Создание пользователя с раздельным хранением salt и хеша
                user = User()
                user.username="user1"
                user.email="user1@email.com"
                user.password_hash = MessengerServer.hash_password("user1user1", salt)
                user.salt= salt.hex()

                session.add(user)

                salt = os.urandom(32)
                # Создание пользователя с раздельным хранением salt и хеша
                user2 = User()
                user2.username="user2"
                user2.email="user2@email.com"
                user2.password_hash = MessengerServer.hash_password("user2user2", salt)
                user2.salt= salt.hex()

                session.add(user2)

                # добывка контакта
                contact = UserContact()
                contact.user = user
                contact.contact = user2
                contact.status = RelationshipStatus.APPROVED

                session.add(contact)
                await session.commit()

                print(f"users added")
    except Exception as e:
        print(e)


## асинхронная главная процедура
async def main():

    # init db

    await InitDBSampleData();

    # создаём объект сервера
    server = MessengerServer()
    # инициализация БД
    await server.init_db()

    # делаем аснхронную карутину для обработки поступающих соединений
    async with websockets.serve(server.handle_connection, "localhost", 8765):
        print("Messenger Server running on ws://localhost:8765")
        await asyncio.Future()




if __name__ == "__main__":


    asyncio.run(main())