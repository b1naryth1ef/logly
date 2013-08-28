from flask import Flask, request
from database import *
from datetime import datetime
import time

app = Flask(__name__)

@app.route("/get")
def route_get():
    #LineMsg.setupz()
    print LineMsg.select().count()
    q = '&'.join(request.values.get("q").split(" "))
    start = time.time()
    q = LineMsg.get_db().execute_sql("""SELECT COUNT(*) FROM linemsg WHERE tsv @@ to_tsquery('english', '%s');""" % q)
    end = time.time()
    print "Search took: %s" % str(end-start)
    print q.fetchone() #.rowcount
    # q = LineMsg.raw("""""
    #             SELECT * FROM linemsg
    #             WHERE to_tsvector(msg)
    #                 @@ to_tsquery('test')
    #             """"")
    # for x in q:
    #     print x
    return ":3"

@app.route('/test')
def route_test():
    LogLine.full_clean()
    return ":3"

if __name__ == "__main__":
    app.run(debug=True)
