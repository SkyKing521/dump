import asyncio
import websockets
import json
import sys
from datetime import datetime

from marshmallow import ValidationError

from app.msg_schemas import (
    UserContactsSchema,
    AuthSchema,
    Auth,
    UserContactsClass,
    OneContactClass,
    PrivateMessageSchema,
    GroupMessageSchema
)


class MessengerClient:
    def __init__(self):
        self.websocket = None
        self.user_id : int = None
        self.username : str = None
        self.contacts : list[OneContactClass] = list()


    # функция для определения схемы сообщения

    # соединение с сервером
    async def connect(self, server_url: str = "ws://localhost:8765"):
        self.websocket = await websockets.connect(server_url)

    # регистрация нового пользователя
    async def register(self, username: str, password: str, email: str)->int:
        auth = Auth()
        auth.type = "register"
        auth.password = password
        auth.username = username
        auth.email = email
        sh = AuthSchema()
        res = sh.dumps(auth)
        await self.websocket.send(res)
        try:
            response = await self.websocket.recv()
            data= json.loads(response)
            if data['type']=='auth_success':
                self.user_id = data['data']['id']
                print(f"зашли как с {username} ИД {self.user_id}")
                return self.user_id
            else:
                return -1
        except Exception as e:
            print(e)
            return -1

    # для логина по имеющемуся пользователю
    async def login(self, username: str, password: str):
        auth = Auth()
        auth.type = "login"
        auth.password = password
        auth.username = username
        sh = AuthSchema()
        res = sh.dumps(auth)
        await self.websocket.send(res)
        try:
            response = await self.websocket.recv()
            data= json.loads(response)
            if data['type']=='auth_success':
                self.user_id = data['data']['id']
                print(f"зашли как с {username} ИД {self.user_id}")
                return self.user_id
            else:
                return -1
        except Exception as e:
            print(e)
            return -1

    # обработка сообщения
    async def process_incoming_messages(self, msg_to_skip: int):
        try:
            i = 0
            async for message in self.websocket:
                i+=1
                if  i== msg_to_skip:
                    break

            async for message in self.websocket:
                await self.process_server_message(self.websocket, message)
        except websockets.ConnectionClosed:
            print("\nСоединение с сервером разорвано")

    # маршрутизация обработчика сообщения
    async def process_server_message(self, websocket, message):
        try:
            data = json.loads(message)
            if data.get('type') == 'error':
                print(f"\nОшибка: {data.get('message')}")
                return

            message_type: str = data.get('type')

            schema = self.get_schema_for_type(message_type)
            if not schema:
                return

            print(f"получили сообщение типа {message_type}")
            # разобранный по правилам схемы dict из JSON
            validated = schema.load(data)

            # получение обработка по имени
            handler = getattr(self, f"handle_{validated['type']}", None)

            # if data.get('type') == 'auth_success':
            # elif data.get('type') == 'private_message':
            # elif data.get('type') == 'group_message':
            # elif data.get('type') == 'user_contacts':
            #     self.print_contacts(data)
            # else:
            #     return
                # ВЫЗОВ Обработчика
            if handler:
                await handler(websocket, validated)
            else:
                print(f"Unhandled message type: {message_type}")

        except json.JSONDecodeError:
            print( "Invalid JSON format")
        except ValidationError as e:
            print( f"Validation error: {e.messages}")
        except Exception as e:
            print( f"Server error: {str(e)}")

    #region handlers
        # по словарю получаем, какая схема JSON какому типу сообщения нужна
    def get_schema_for_type(self, message_type):
        return {
            'auth_success': AuthSchema(),
            'private_message' : PrivateMessageSchema(),
            'group_message' : GroupMessageSchema(),
            'user_contacts' : UserContactsSchema()
        }.get(message_type)

    # обработка личного сообщения
    async def handle_private_message(self, websocket, data: dict):
            print(f"\n[ЛС от {data['sender_id']}]: {data['content']}")

    # обработка группового сообщения
    async def handle_group_message(self, websocket,data: dict):
        print(f"\n[Группа {data['group_id']}]: {data['sender_id']}: {data['content']}")

    # Printing contacts
    async def handle_user_contacts(self, websocket,data: dict):
        print("Контакты")
        for cn in data['contacts']:
            c = OneContactClass()
            c.user_id = cn['user_id']
            c.user_name=cn['user_name']
            c.custom_nickname = cn['custom_nickname']
            c.status = cn['status']
            self.contacts.append(c)
            print(f"user_name {cn['user_name']}, user_id {cn['user_id']}")
        for gp in data['groups']:
            print(f"user_name {gp['group_name']}, user_id {gp['group_id']}")

    #endrefion

    # sending private message
    async def send_private_message(self, receiver: str, content: str):
        await self.websocket.send(json.dumps({
            'type': 'private_message',
            'sender_id' : self.user_id,
            'receiver_id': receiver,
            'content': content
        }))

    # sending contacts response
    async def get_contacts(self):
        await self.websocket.send(json.dumps({
            'type': 'get_user_contacts',
        }))


    # sending group message
    async def send_group_message(self, group_id: int, content: str):
        await self.websocket.send(json.dumps({
            'type': 'group_message',
            'group_id': group_id,
            'content': content
        }))

# Это основная функция системы
async def main():
    client = MessengerClient()
    await client.connect()

    action_done = 0
    tries : int = 0;
    while  action_done==0:
    # Выбор действия
        action = input("Регистрация (r) или Вход (l)? ").lower()
        username = input("Имя пользователя: ")
        password = input("Пароль: ")
        email = username+'@email.com'

        if action == 'r':
            response = await client.register(username, password,email)
            tries+=1
        elif action == 'l':
            response = await client.login(username, password)
            tries+=1
        else:
            print("Неизвестное действие")


        if response<0:
            print(f'Ещё раз ввести надо')
        else:
            action_done = 1 # выходим, раз есть авторизация


    # Запуск обработки сообщений
    asyncio.create_task(client.process_incoming_messages(tries))

    print("Доступные команды:")
    print("/list получить список контактов пользователя")
    print("/msg <получатель> <сообщение> - личное сообщение")
    print("/group <id группы> <сообщение> - сообщение в группу")
    print("/exit - выход")

    # Основной цикл ввода команд
    while True:
        try:
            command = await asyncio.get_event_loop().run_in_executor(
                None, input, f"[{client.username}] > "
            )
            if command.startswith('/list'):
                await client.get_contacts()
            elif command.startswith('/msg'):
                _, receiver, *content = command.split()
                await client.send_private_message(receiver, ' '.join(content))

            elif command.startswith('/group'):
                _, group_id, *content = command.split()
                await client.send_group_message(int(group_id), ' '.join(content))


            elif command == '/exit':
                await client.websocket.close()
                break

            else:
                print("Доступные команды:")
                print("/list получить список контактов пользователя")
                print("/msg <получатель> <сообщение> - личное сообщение")
                print("/group <id группы> <сообщение> - сообщение в группу")
                print("/exit - выход")

        except KeyboardInterrupt:
            await client.websocket.close()
            break


if __name__ == "__main__":
    asyncio.run(main())