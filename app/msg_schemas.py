#Здесь лежат схемы JSON
from marshmallow import Schema, fields, validate, EXCLUDE
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from datetime import datetime

from sqlalchemy import false

from .msg_models import User



class Auth:
    def __init__(self):
        self.type = ""
        self.username =""
        self.password=""
        self.email=""

class AuthSchema(Schema):
    type = fields.Str(required=True, validate=validate.OneOf(["register", "login"]))  # Добавляем поле type
    username = fields.Str(required=True, validate=validate.Length(min=3, max=50))
    password = fields.Str(required=True, validate=validate.Length(min=8))
    email = fields.Str(required=False)

    class Meta:
        unknown = EXCLUDE  # Игнорировать лишние поля

class CreateGroupSchema(Schema):
    type = fields.Str(required=True, validate=validate.Equal("create_group"))  # Пример для других схем
    name = fields.Str(required=True, validate=validate.Length(min=3, max=50))
    members = fields.List(fields.Int(), required=True)

    class Meta:
        unknown = EXCLUDE


class UserSchema(SQLAlchemyAutoSchema):
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True, validate=validate.Length(min=3, max=50))
    created_at = fields.DateTime(format="iso", dump_only=True)

    class Meta:
        unknown = EXCLUDE
        model = User
        include_fk = True
        load_instance = True  # Для автоматической конвертации в модель

class GroupSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=3, max=50))
    creator_id = fields.Int(required=True)
    created_at = fields.DateTime(format="iso", dump_only=True)
    members = fields.List(fields.Int(), dump_only=True)

    class Meta:
        unknown = EXCLUDE

class GroupMessageSchema(Schema):
    id = fields.Int(dump_only=True)
    content = fields.Str(required=True, validate=validate.Length(min=1, max=500))
    is_group = fields.Bool(dump_only=True)
    sender_id = fields.Int(dump_only=True)
    receiver_id = fields.Int(allow_none=True)
    group_id = fields.Int(allow_none=True)
    created_at = fields.DateTime(format="iso", dump_only=True)

    class Meta:
        unknown = EXCLUDE


class PrivateMessageSchema(Schema):
    type = fields.Str(required=True, validate=validate.Equal("private_message"))
    sender_id = fields.Int(required=True)
    receiver_id = fields.Int(required=True)
    content = fields.Str(required=True, validate=validate.Length(min=1, max=500))


    class Meta:
        unknown = EXCLUDE


# получение списка контактов

# Команда Для получения списка контактов и групп
class GetUserContactsSchema(Schema):
    type = fields.Str(required=True, validate=validate.Equal("get_user_contacts"))  # Пример для других схем

    class Meta:
        unknown = EXCLUDE


class OneContactSchema(Schema):
    user_id = fields.Int(required=True)
    user_name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    custom_nickname = fields.Str(required=False, allow_none=True)
    status = fields.Str(required=True, validate=validate.Length(min=1, max=15))

    class Meta:
        unknown = EXCLUDE

# группа
class OneGroupSchema(Schema):
    group_id = fields.Int(required=True)
    group_name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    custom_groupname = fields.Str(required=False, allow_none=True)
    status = fields.Str(required=True, validate=validate.Length(min=1, max=15))

    class Meta:
        unknown = EXCLUDE

# схема ответа
class UserContactsSchema(Schema):
    type = fields.Str(required=True, validate=validate.Equal("user_contacts"))
    contacts = fields.List(fields.Nested(OneContactSchema), required=False)
    groups = fields.List(fields.Nested(OneGroupSchema), required=False)

    class Meta:
        unknown = EXCLUDE

class OneGroupClass:
    def __init__(self):
        self.group_id : int
        self.group_name :str
        self.custom_groupname : str
        self.status: str

class OneContactClass:
    user_id:int
    user_name:str
    custom_nickname:str
    status:str

# схема ответа
class UserContactsClass:
    def __init__(self):
        self.type: str = "user_contacts"
        self.contacts : list[OneContactClass] = list()
        self.groups : list[OneGroupClass] = list()

# конец получение списка контактов