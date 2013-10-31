import os, datetime, pymongo
import logging
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
        with self.getConnection() as c:
            if smart:
                q = c.find({"message": message})
                if q.count():
                    log.info("Found SingleMessage match, using")
                    return q.find()[0]._id
            c.save({"message": message})

class LogEntry(DatabaseObject):
    collection = "logentry"

    @classmethod
    def create(cls, original, message, entry_types, time, source):
        self = cls()

        mid = SingleMessage.create(message, smart=(not USE_CLEANUP_PROCESS))
        if not len(entry_types):
            entry_types = [EntryType]

        entries = [ENTRY_TYPES[i].do_build(original) for i in entry_types if i in ENTRY_TYPES]

        with self.getConnection() as c:
            c.save({
                "message": mid,
                "types": entry_types,
                "time": time,
                "source": source,
                "entries": entries
            })
