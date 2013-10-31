from flask import Flask, request, render_template
from database import *
import time, socket, redis, thread

app = Flask(__name__)

class Server(object):
    """
    Represents a TCP client server for streaming of new messages using
    redis pub/sub.

    TODO: rewrite this in a decent framework and abstract from web end
        later on...
    """
    def __init__(self, host="localhost", port=9215):
        self.host = host
        self.port = port
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind((self.host, self.port))
        self.s.listen(1)
        self.redis = redis.Redis()

    def handle(self, c, a):
        data = c.recv(1024)
        if not User.isValidKey(data):
            print "Invalid API key %s!" % data
            return
        ps = self.redis.pubsub()
        ps.subscribe("logly")
        for item in ps.listen():
            self.s.sendall(str(item['data']))

    def spawn(self):
        thread.start_new_thread(self.run, ())

    def run(self):
        while True:
            conn, addr = self.s.accept()
            thread.start_new_thread(self.handle, (conn, addr))
        self.s.close()

@app.route("/")
def route_root():
    results = []
    with LogEntry.getConnection() as c:
        for r in c.find().sort("time", -1).limit(150):
            r['message'] = SingleMessage.get(r['message'])
            r['message']['message'] = r['message']['message'].replace("\n", "<br>")
            results.append(r)

    return render_template("index.html", results=results)

if __name__ == "__main__":
    s = Server()
    s.run()
    #app.run(debug=True)
