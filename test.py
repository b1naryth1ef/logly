import logging
import string
import random
import time
from client import LoglyHandler

log = logging.getLogger()
log.setLevel(logging.DEBUG)
log.addHandler(LoglyHandler("localhost", 9210))

rows = 5000

# This generates a random-string for a log line
def test_function_1():
    log.debug(''.join([random.choice(string.ascii_letters) for i in range(0, 500)]))

# This generates some duplicated text data
def test_function_2():
    for i in range(1, 7000):
        log.info("asdfasdfasdfasdfasdasdfasdfasdfasdfasdfasdff")

# start = time.time()
# for i in range(0, rows):
#     test_function_1()
# end = time.time()

# print "Ran %s rows in %s" % (rows, end-start)
# print "So: %s per row" % ((end-start)/rows)

test_function_2()
