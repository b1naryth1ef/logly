import socket, logging, json, os

class Client(object):
    def __init__(self, ip, port):
        self.dest = (ip, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send(self, data):
        self.sock.sendto(data+"\n", self.dest)


class LoglyHandler(logging.Handler):
    def __init__(self, host, port=9210, should_hash=True):
        logging.Handler.__init__(self)
        self.client = Client(host, port)

        self.hash = should_hash

        if self.hash:
            self.get_general_info()

    def get_general_info(self):
        self.git_branch = os.popen("git branch").read().split("*")[-1].split("\n")[0].strip()
        self.git_commit = os.popen("git log --pretty=format:'%h' -n 1").read().strip()
        self.git_status = [0, 0]

        for line in os.popen("git status --porcelain").read().split("\n"):
            if not line: continue
            if line[1] == '?':
                self.git_status[1] += 1
            if line[1] == 'M':
                self.git_status[0] += 1

    def emit(self, record):
        if not self.hash:
            self.get_general_info()

        pak = {
            "msg": record.msg,
            "levelname": record.levelname,
            "path": record.pathname,
            "line": record.lineno,
            "function": record.funcName,
            "time": record.created,
            "git": {
                "branch": self.git_branch,
                "commit": self.git_commit,
                "status": self.git_status
            }
        }

        if isinstance(pak['msg'], Exception):
            pak['msg'] = "%s: %s" % (pak['msg'].__class__.__name__, str(pak['msg']))
        self.client.send(json.dumps(pak))
