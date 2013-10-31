from entries import *
import socket, logging, json, os


class Client(object):
    def __init__(self, ip, port):
        self.dest = (ip, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send(self, data):
        self.sock.sendto(data+"\n", self.dest)

class LoglyHandler(logging.Handler):
    def __init__(self, host, source="", port=9210, handlers=[]):
        logging.Handler.__init__(self)
        self.client = Client(host, port)
        self.source = source or socket.gethostname()
        self.handlers = handlers

    def emit(self, record):
        if not self.hash:
            self.get_general_info()

        data = {
            "message": record.msg,
            "entry_types": self.handlers,
            "time": record.created,
            "source": self.source,
        }

        for item in self.handlers:
            if item in ENTRY_TYPES:
                item = ENTRY_TYPES[item]
                data[item.key] = item.do_send(record=record)

        if isinstance(data['msg'], Exception):
            data['msg'] = "%s: %s" % (data['msg'].__class__.__name__, str(data['msg']))
        self.client.send(json.dumps(data))
