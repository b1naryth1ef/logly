from flask import Flask, request, render_template
from database import *
from datetime import datetime
import time

app = Flask(__name__)

@app.route("/get")
def route_get():
    built_q = '&'.join(request.values.get("q").split(" "))
    print "Running query for %s" % built_q

    result = []
    for item in LineMsg.search(built_q):
        result += prefetch(LogLine.select(LogLine.time, LogLine.msg).where(LogLine.msg == item.id).limit(100))
    return render_template("index.html", results=result)

@app.route("/")
def route_root():
    print "Total LogLines: %s" % LogLine.select().count()
    print "Total LineMsgs: %s" % LineMsg.select().count()
    result = []
    for item in LogLine.select().order_by(LogLine.time.desc()).limit(100):
        result.append(item)
    return render_template("index.html", results=result)

@app.route('/test')
def route_test():
    LogLine.full_clean()
    return ":3"

if __name__ == "__main__":
    app.run(debug=True)
