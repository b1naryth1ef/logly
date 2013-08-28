import socket, json

class Server(object):
    def __init__(self, ip, port=9210):
        self.addr = (ip, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.c = {}

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
            print "Bad packet!"
        print data

    def start(self):
        self.sock.bind(self.addr)
        while True:
            data, addr = self.sock.recvfrom(1024)
            self.cache(addr, data)
            if "\n" in data:
                self.parse(self.get_cache(addr))

Server("localhost").start()