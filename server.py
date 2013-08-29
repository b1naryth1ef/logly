from database import *
from datetime import datetime
from collections import deque
import socket, json, thread, time

class Server(object):
    def __init__(self, ip, port=9210, threads=2):
        self.addr = (ip, port)
        self.threads = threads or 1

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.q = deque()

    def parse(self, data):
        """
        Attempts to parse a json-formatted
        log line and add it to the database.
        Keep in mind, this says fuck it to
        doing any pre-queries or any duplication
        matching, in favor of slow loading that
        stuff later.
        """
        try:
            data = json.loads(data.strip())
        except:
            print "Bad packet! (%s)" % data
            return

        LogLine.from_json(data)

    def parse_thread(self, id, main=False, debug=False):
        """
        A thread which grabs log entries off of
        the internal queue, and attempts to parse them.
        Keep in mind this doesn't have to be super fast,
        becuase we're buffering log lines.
        """
        while True:
            if main and debug:
                print "Messages Left In Queue: %s" % len(self.q)

            if len(self.q):
                self.parse(self.q.popleft())
            else:
                time.sleep(.5)

    def start(self, debug=False):
        """
        A loop which grabs log entires from UDP and
        stores them in the internal queue for parsing.
        """
        if debug: print "Debug Enabled!"
        for i in range(0, self.threads):
            thread.start_new_thread(self.parse_thread, (i, i == 0, debug))

        self.sock.bind(self.addr)
        while True:
            data, addr = self.sock.recvfrom(1024)
            self.q.append(data)
            if debug:
                print "Pushed queue size to: %s" % len(self.q)
                if len(self.q) > 5000:
                    print "WARNING: Queue is larger than 5,000 items, maybe increase threads for server?"

s = Server("localhost")
s.start(debug=True)

