from pathlib import Path

from peewee import *
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = Path(__file__).resolve().parent
db = SqliteDatabase(str(BASE_DIR / "database.db"), pragmas={"foreign_keys": 1})


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    username = CharField(unique=True)
    email = CharField(unique=True)
    password_hash = CharField()
    is_admin = BooleanField(default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Category(BaseModel):
    name = CharField(unique=True)


class Event(BaseModel):
    title = CharField()
    short_description = CharField()
    description = TextField()
    date = DateField()
    time = TimeField()
    location = CharField()
    organizer = CharField()
    max_participants = IntegerField(default=30)
    category = ForeignKeyField(Category, backref="events")


class Registration(BaseModel):
    user = ForeignKeyField(User, backref="registrations")
    event = ForeignKeyField(Event, backref="registrations")

    class Meta:
        indexes = (
            (("user", "event"), True),
        )


def create_tables():
    db.connect(reuse_if_open=True)
    db.create_tables([User, Category, Event, Registration])
    db.close()
