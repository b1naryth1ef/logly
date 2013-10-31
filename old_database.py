import os, datetime
from peewee import *

db = PostgresqlDatabase("logly_dev", threadlocals=True, user="bro")

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
        GitBaseLogType.from_json(self, data) # Explicit :)
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

        # Select duplicates
        DUPE_QUERY = """SELECT msg, count(1) FROM linemsg
                     GROUP BY msg
                     HAVING count(1)>1"""

        print "Attempting to prune our database..."

        # Excute query, check if we even have any duplicates
        q = cls.get_db().execute_sql(DUPE_QUERY)
        if not q.rowcount:
            print "Looks like the database is already clean!"

        # Iterate over duplicates (in form [LineMsg.msg, count])
        for msg, count in q.fetchall():
            print "Found %s duplicates line %s, attempting to clean them up..." % (count, msg)

            # Get any LineMsg's that match msg
            q = LineMsg.select(LineMsg.id).where(LineMsg.msg == msg)

            # Hackey fix to weird peewee primatives, could result in memory issues?
            entires = [i.id for i in q]

            # Change all loglines to use the first entry
            print "Adjusted %s loglines to one LineMsg" % LogLine.select().where(LogLine.msg << entires).count()
            LogLine.update(msg=entires[0]).where(LogLine.msg << entires).execute()

            # Remove all logmessages that arent the first entry
            print "Removed %s duplicate rows" % LineMsg.select().where(LineMsg.id << entires[1:]).count()
            LineMsg.delete().where(LineMsg.id << entires[1:]).execute()

        print "Boom! Your database is spiffy!"

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
