import logging
import string
import random
import time
from client import LoglyHandler

log = logging.getLogger()
log.setLevel(logging.DEBUG)
log.addHandler(LoglyHandler("localhost", log="test"))

rows = 50000

# This generates a random-string for a log line
def test_function_1():
    log.debug(''.join([random.choice(string.ascii_letters) for i in range(0, 500)]))

# This generates some duplicated text data
def test_function_2():
    for i in range(1, 1000):
        log.info("asdfasdfasdfasdfasdasdfasdfasdfasdfasdfasdff")

# start = time.time()
# for i in range(0, rows):
#     test_function_1()
# end = time.time()

# print "Ran %s rows in %s" % (rows, end-start)
# print "So: %s per row" % ((end-start)/rows)

# print "Attempting to log %s rows..." % rows
# start = time.time()
# for i in range(0, rows):
#     test_function_1()
# print "Done in %s seconds" % (time.time()-start)

log.info("Hello World!\n This is a test")

try:
    raise Exception("YOLO SWAK")
except Exception as e:
    log.exception(e)