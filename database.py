from peewee import *
from datetime import *

#db = SqliteDatabase('test.db', threadlocals=True)
db = PostgresqlDatabase("test")

class Base(Model):
    class Meta:
        database = db

    @staticmethod
    def get_db():
        return db

class LineMsg(Base):
    msg = TextField()

    @staticmethod
    def search(text, smart=False):
        q = LineMsg.select().where(LineMsg.msg ** text)
        if not q.count(): return []
        if not smart: return q
        res = []
        for item in q:
            for i in LogLine.select().where(msg=item):
                res.append(i)
        return res

    @classmethod
    def setup(cls):
        print "Setting up!"
        db.execute_sql("""
            ALTER TABLE linemsg
              ADD tsv TSVector""")
        db.execute_sql("""
            CREATE TRIGGER TS_tsv
              BEFORE INSERT OR UPDATE ON linemsg
                FOR EACH ROW EXECUTE PROCEDURE
                    tsvector_update_trigger(tsv, 'pg_catalog.english', msg);""")
        db.execute_sql("""
            CREATE INDEX tsv_GIN ON linemsg
              USING GIN(tsv);""")

class LogLine(Base):
    msg = ForeignKeyField(LineMsg)
    source = CharField()
    source_file = CharField()
    source_line = IntegerField()
    source_commit = CharField()
    source_function = CharField()
    source_branch = CharField()
    source_clean = BooleanField
    line_type = CharField()
    time = DateTimeField()
    new = BooleanField(default=True)

    @classmethod
    def full_clean(cls):
        """
        This functions attempts to find line messages that are repeated
        in the database, and changes LogLine references to match a single
        database entry. This can cut down insanely on the number of lines we actually store.
        """
        total = 0
        for item in LogLine.select(LogLine.id, LogLine.msg).join(LineMsg).where(LogLine.new == True):
            q = LineMsg.select(LineMsg.id).where((LineMsg.msg == item.msg.msg) & (LineMsg.id != item.msg.id))
            if q.count() > 1:
                print "Attempting to consoldate duplicate messages"
                for item in q[1:]:
                    logline = LogLine.select(LogLine.id).where(LogLine.msg == item)
                    if logline.count():
                        logline = logline[0]
                    else:
                        print "Nothing here..."
                        continue
                    logline.msg = q[0]
                    logline.new = False
                    logline.save()
                    item.delete()
                    total += 1
                    print "Removed 1 item, consolidation baby!"
        print "Pruned: %s" % total

if __name__ == "__main__":
    db.execute_sql("DROP TABLE linemsg CASCADE")
    db.execute_sql("DROP TABLE logline CASCADE")
    LineMsg.create_table(True)
    LogLine.create_table(True)
    LineMsg.setup()
