import os, datetime
from peewee import *

db = PostgresqlDatabase("logly", threadlocals=True, user="bro", host=os.getenv("HOST"), password=os.getenv("PSQLPASS"))

class Base(Model):
    class Meta:
        database = db

    @staticmethod
    def get_db():
        return db

class LineMsg(Base):
    """
    Represents the actual log lines as
    they are stored in the database.
    Should NEVER have an exact duplicate post
    running LogLine.full_clean().
    """
    msg = TextField()

    @classmethod
    def search(cls, q, limit=100):
        """
        Search takes in a query and limit, and provides
        in-text searching of the log index. .search should
        NOT do any joining to keep things explicit and clean.
        """
        q = cls.raw("SELECT id FROM linemsg WHERE tsv @@ to_tsquery('english', '%s');" % (q)).execute()
        for obj in q:
            yield obj

    @classmethod
    def setup(cls):
        """
        Setup builds text searching fields and indexes
        for the first time. It should really only be run
        on the first go, but it won't hurt things if you
        run it over and over again (AFAIK).
        """
        print "Setting up index..."
        # First we add a TSVector field to the linemsg type
        db.execute_sql("""
            ALTER TABLE linemsg
              ADD tsv TSVector""")

        # Now we update TSVector on insert/updates
        db.execute_sql("""
            CREATE TRIGGER TS_tsv
              BEFORE INSERT OR UPDATE ON linemsg
                FOR EACH ROW EXECUTE PROCEDURE
                    tsvector_update_trigger(tsv, 'pg_catalog.english', msg);""")

        # Finally we create an index for the tsv field
        db.execute_sql("""
            CREATE INDEX tsv_GIN ON linemsg
              USING GIN(tsv);""")

class GitBaseLogType(Base):
    source_commit = CharField()
    source_branch = CharField()
    source_clean = BooleanField()

    @staticmethod
    def from_json(self, data):
        self.source_commit = data['git']['commit']
        self.source_branch = data['git']['branch']
        self.source_clean = bool(data['git']['status'][0])

class PythonLogType(GitBaseLogType):
    source_file = CharField()
    source_line = IntegerField()
    source_function = CharField()

    @staticmethod
    def from_json(self, data):
        GitBaseLogType.from_json(self, data) #Explicit :)
        self.source_file = data['path']
        self.source_line = data['line']
        self.source_function = data['function']

types = {
    "python" : PythonLogType
}

class LogLine(Base):
    """
    Represents an actual logged-line, tracks
    git and traceback information. This refernces
    LineMsg instead of holding any actual raw log data,
    allowing us to greatly minimize DB size by consolidating log
    lines.
    """
    msg = ForeignKeyField(LineMsg)
    source = CharField()
    entry = IntegerField(null=True) # -> ID
    ltype = CharField()
    time = DateTimeField()
    new = BooleanField(default=True)

    @classmethod
    def from_json(cls, data):
        msg = LineMsg(msg=data['msg'])
        msg.save()

        entry = None
        if data['type'] in types:
            e = types[data['type']]()
            e.from_json(e, data)
            e.save()
            entry = e.id

        line = LogLine(
            msg=msg,
            entry=entry,
            source=data['source'],
            ltype=data['type'],
            time=datetime.datetime.fromtimestamp(data['time']))
        line.save()

    @classmethod
    def full_clean(cls):
        """
        This functions attempts to find line messages that are repeated
        in the database, and changes LogLine references to match a single
        database entry. This can cut down insanely on the number of lines we actually store.
        Ideally the final app will schedule this task.
        """
        total = 0

        # First find any new LogLines that haven't been parsed
        for item in LogLine.select(LogLine.id, LogLine.msg).join(LineMsg).where(LogLine.new == True):

            # Now lets search inside these LogItems to get any duplicated LineMsg's
            q = LineMsg.select(LineMsg.id).where((LineMsg.msg == item.msg.msg) & (LineMsg.id != item.msg.id))

            # If we have duplicates, lets consolidate them
            if q.count() > 1:
                # Lets iterate over LineMsg that is duplicated, skipping the first item (we use that as the consolidation point)
                for subitem in q[1:]:
                    # Lets grab any actual LogLines referencing this line (keeping in mind any consolidation thats happened in the past)
                    for logline in LogLine.select(LogLine.id).where(LogLine.msg == subitem):
                        logline.msg = q[0]
                        logline.save()
                        total += 1
                    subitem.delete()
            # Make sure to mark the origin line as parsed
            item.new = False
            item.save()
        print "Pruned %s log lines" % total

if __name__ == "__main__":
    if raw_input("Reset (DELETE ERYTHING) database? (y) ").lower() == 'y':
        print "RM -RF ALL THE THINGSSSSSS"
        db.execute_sql("DROP TABLE IF EXISTS linemsg CASCADE")
        db.execute_sql("DROP TABLE IF EXISTS logline CASCADE")
        LineMsg.create_table(True)
        LogLine.create_table(True)
        LineMsg.setup()
    else:
        print "Fine... don't rm -rf... how about we clean instead? :D"
        LogLine.full_clean()
