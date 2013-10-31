import subprocess

class EntryType(object):
    cache = False
    key = "entry"

    def __init__(self):
        self.cached_data = None

    @classmethod
    def expect(cls, obj, item):
        if not item in obj:
            raise Exception("%s expects item %s, which was not found inside `%s`" % (
                cls.__name__,
                item,
                obj))
        return obj.get(item)

    @classmethod
    def run(cls, command, wait=True):
        proc = subprocess.Popen(command, stdout=subprocess.PIPE)
        if wait:
            proc.wait()
        return proc

    def build(self, data):
        return {}

    @classmethod
    def do_build(cls, data):
        self = cls()
        return self.build(data)

    def do_send(self, **kwargs):
        if (self.cache and not self.cached_data) or not self.cache:
            data = self.send(**kwargs)
            if self.cache:
                self.cached_data = data
        return data

    def send(self, **kwargs): pass

class GitEntryType(object):
    """
    An entry type that logs information about the current working directories
    git repository.
    """

    cache = True
    key = "git"

    def build(self, data):
        data = self.expect(data, self.key)

        return {
            "commit": data.get("commit"),
            "branch": data.get("branch"),
            "status": data.get("status")
        }

    def send(self, **kwargs):
        data = {}
        data["branch"] = self.run("git branch").stdout.read().split("*")[-1].split("\n")[0].strip()
        data['commit'] = self.run("git log --pretty=format:'%h' -n 1").stdout.read().strip()
        data['status'] = {"modified": 0, "new": 0}
        for line in self.run("git status --porcelain").stdout.read().split("\n"):
            if not line: continue
            if line[1] == '?':
                data['status']['new'] += 1
            elif line[1] == 'M':
                data['status']['modified'] += 1
        return data

ENTRY_TYPES = {
    "entry": EntryType,
    "git": GitEntryType
}