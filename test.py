import logging
from client import LoglyHandler

log = logging.getLogger()
log.setLevel(logging.DEBUG)
log.addHandler(LoglyHandler("", 9210))

def test_function_1():
    log.debug("This is a debug test")

def test_function_2():
    log.info("This is an info test")

def test_function_3():
    log.warning("This is a warning test")

def test_function_4():
    log.error("This is an error test")

def test_function_5():
    try:
        1/0
    except Exception as e:
        log.exception(e)

test_function_1()
test_function_2()
test_function_3()
test_function_4()
test_function_5()
