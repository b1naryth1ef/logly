import os, datetime, pymongo
import logging, uuid
from entries import *

CONN = pymongo.MongoClient()
log = logging.getLogger("logly")

USE_CLEANUP_PROCESS = False

class Connection(object):
    def __init__(self, db, coll):
        self.db = db
        self.coll = coll

    def __enter__(self):
        return CONN[self.db][self.coll]

    # @TODO
    def __exit__(self, *args, **kwargs): pass


class DatabaseObject(object):
    db = "log"
    collection = ""
    conn = None

    @classmethod
    def getConnection(cls):
        if not cls.conn:
            cls.conn = Connection(cls.db, cls.collection)
        return cls.conn

    @classmethod
    def create_collection(cls):
        CONN[cls.db].create_collection(cls.collection)

    @classmethod
    def get(cls, id):
        with cls.getConnection() as c:
            q = c.find({"_id": id})
            if not q.count():
                return None
            return q[0]

    @classmethod
    def count(cls):
        with cls.getConnection() as c:
            return c.find().count()

class SingleMessage(DatabaseObject):
    collection = "singlemessage"

    @classmethod
    def create(cls, message, smart=True):
        """
        Creates a single message in the database.

        :param message: The (stringified) message
        :param smart: If true, will query the database first and try to
            find a match before inserting. This overrides the cleanup
            functionality and could (?) increase performance for some
            workloads.
        :returns: ID of new message, or the found id if `smart`
        """
        self = cls()

        message = message.replace(unicode(u"\uF8FF"), "\n")

        with self.getConnection() as c:
            if smart:
                q = c.find({"message": message})
                if q.count():
                    log.info("Found SingleMessage match, using...")
                    return q[0]['_id']
            return c.save({"message": message})

class LogEntry(DatabaseObject):
    collection = "logentry"

    @classmethod
    def create(cls, original):
        self = cls()

        mid = SingleMessage.create(original.get("message"), smart=(not USE_CLEANUP_PROCESS))
        if not len(original.get("entry_types")):
            original["entry_types"] = ["entry"]

        entries = dict([(i, ENTRY_TYPES[i].do_build(original)) for i in original.get("entry_types") if i in ENTRY_TYPES])

        data = {
            "message": mid,
            "types": original.get("entry_types"),
            "time": original.get("time"),
            "source": original.get("source"),
            "entries": entries,
            "log": original.get("log"),
            "tags": []
        }

        with self.getConnection() as c:
            c.save(data)

        data['message'] = original.get("message")

        return data

class User(DatabaseObject):
    collection = "users"

    @classmethod
    def create(cls, username, password, api_key=None):
        api_key = api_key or str(uuid.uuid4())
        with cls.getConnection() as c:
            id = c.save({
                "username": username,
                "password": password,
                "api_key": api_key
            })
        return id, api_key

    @classmethod
    def isValidKey(cls, key):
        with cls.getConnection() as c:
            return c.find({"api_key": key}).count() >= 1

if __name__ == "__main__":
    id, key = User.create("test", "")
    print "%s: %s" % (id, key)