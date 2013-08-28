import logging
import string
import random
import time
from client import LoglyHandler

log = logging.getLogger()
log.setLevel(logging.DEBUG)
log.addHandler(LoglyHandler("", 9210))

def test_function_1():
    log.debug(''.join([random.choice(string.ascii_letters) for i in range(0, 500)]))

def test_function_2():
    for i in range(1, 50):
        log.info("test")

# start = time.time()
# for i in range(0, 500):
#     test_function_1()
# end = time.time()

# print "Ran %s rows in %s" % (500, end-start)
# print "So: %s per row" % ((end-start)/500)

test_function_2()