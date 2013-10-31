import socket, json

class Client(object):
    def __init__(self, host="localhost", port=9215):
        self.host = host
        self.port = port
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.host, self.port))

    def loop(self, key):
        self.s.sendall(key)
        while True:
            data = self.s.recv(1025)
            if data:
                yield json.loads(data)

c = Client()
for item in c.loop("9a502606-d56a-4128-98dc-719a583ebf1c"):
    print item