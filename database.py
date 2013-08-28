from peewee import *
from datetime import *

db = SqliteDatabase('test.db', threadlocals=True)

class Base(Model):
    class Meta:
        database = db

class LineContent(Base):
    content = TextField()

class LogLine(Base):
    content = ForeignKeyField(LineContent)
    source = CharField()
    source_file = CharField()
    source_line = IntegerField()
    source_commit = CharField()
    line_type = CharField()
    etc_data = TextField()
    ignored = BooleanField()
    time = DateTimeField()

class Event(Base):
    name = CharField()
    status = CharField()

class EventLink(Base):
    line = ForeignKeyField(LogLine)
    event = ForeignKeyField(Event)


LineContent.create_table(True)
LogLine.create_table(True)
Event.create_table(True)
EventLink.create_table(True)
