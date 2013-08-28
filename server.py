from database import *
from datetime import datetime
from collections import deque
import socket, json, thread, time

def push_match_queue(id): pass

class Server(object):
    def __init__(self, ip, port=9210, threads=4):
        self.addr = (ip, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.c = {}
        self.q = deque()
        self.threads = threads or 1
        self.totals = 0
        self.totalsx = 0

    def cache(self, addr, data):
        if addr in self.c:
            self.c[addr] += data
        else:
            self.c[addr] = data

    def get_cache(self, addr):
        data = self.c[addr]
        del self.c[addr]
        return data

    def parse(self, data):
        try:
            data = json.loads(data.strip())
        except:
            print "Bad packet! (%s)" % data
            return

        msg = LineMsg(msg=data['msg'])
        msg.save()

        line = LogLine(
            msg=msg,
            source=data['source'],
            source_file=data['path'],
            source_line=data['line'],
            source_function=data['function'],
            source_commit=data['git']['commit'],
            source_branch=data['git']['branch'],
            line_type=data['levelname'],
            time=datetime.fromtimestamp(data['time']),
            source_clean=bool(data['git']['status'][0]))
        line.save()

    def parse_thread(self, id):
        while True:
            if len(self.q):
                self.parse(self.q.popleft())
                self.totals += 1
            else: time.sleep(1)

    def start(self):
        for i in range(0, self.threads):
            thread.start_new_thread(self.parse_thread, (i,))

        self.sock.bind(self.addr)
        while True:
            data, addr = self.sock.recvfrom(1024)
            self.cache(addr, data)
            if "\n" in data:
                self.q.append(self.get_cache(addr))
                s.totalsx += 1

s = Server("localhost")

try:
    s.start()
except:
    print s.totals
    print s.totalsx
