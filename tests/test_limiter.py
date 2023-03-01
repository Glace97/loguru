"""
    Tests the _limiter.Limiter class of loguru
"""

import time
import os
from pathlib import Path
from loguru._limiter import Limiter
from loguru import logger

def test_limiter_count():
    """
        Tests limit count
    """
    limiter = Limiter(limit=100)
    for i in range(1, 1000):
        if limiter.reached('hej'):
            assert i > 99
            break

def test_limiter_time():
    """
        Tests limiter time
    """
    message = 'hej'
    limiter = Limiter(limit=1, interval=0.005) # 0.1 seconds
    assert not limiter.reached(message), 'first'
    assert limiter.reached(message), 'second'
    time.sleep(0.01)
    assert not limiter.reached(message)
    limiter = Limiter(limit=1, interval=0.01) # 0.1 seconds
    assert not limiter.reached(message)
    time.sleep(0.005)
    assert limiter.reached(message)

def _count_lines_that_contains(filename, message, count):
    with open(filename, 'r', encoding='ascii') as file:
        lines = file.read().split('\n')
        counts = 0
        for line in lines:
            if message in line:
                counts += 1
        assert counts == count

def _generate_filename_message():
    random_suffix = os.urandom(8).hex()
    tempfilename = '/tmp/' + random_suffix + '.log'
    return Path(tempfilename), os.urandom(16).hex()

def test_logger_count_limit():
    """
        Tests count limit of logger limit
    """
    filename, message = _generate_filename_message()
    logger.limit(1)
    logger.add(filename)
    assert os.path.exists(filename)
    for _ in range(100):
        logger.info(message)
    _count_lines_that_contains(filename, message, 1)
    os.remove(filename)
    assert not os.path.exists(filename)
    logger.add(filename)
    assert os.path.exists(filename)
    # No limit
    logger.limit()
    for _ in range(100):
        logger.info(message)
    _count_lines_that_contains(filename, message, 100)
    os.remove(filename)

def _generate_hex(length=16):
    return os.urandom(length//2).hex()

def test_logger_time_limit():
    """
        Tests time limit of logger limit
    """
    filename, message = _generate_filename_message()
    logger.limit(1, 0.01)
    logger.add(filename)
    assert os.path.exists(filename)
    logger.info(message)
    for _ in range(100):
        logger.info(message)
    _count_lines_that_contains(filename, message, 1)
    os.remove(filename)
    logger.add(filename)
    _count_lines_that_contains(filename, message, 0)
    logger.limit(10, 0.1)
    for _ in range(50):
        time.sleep(0.001)
        logger.info(message)
    _count_lines_that_contains(filename, message, 10)
    os.remove(filename)

def test_window():
    """
        Tests window of limiter
    """
    limiter = Limiter(0, 0.1, True)
    message = _generate_hex()
    assert limiter.reached(message)
    limiter = Limiter(2, 0.1, True)
    assert not limiter.reached(message)
    time.sleep(0.05)
    assert not limiter.reached(message)
    assert limiter.reached(message)
    time.sleep(0.05)
    assert not limiter.reached(message), 'expected buffer empty'

def test_logger_window(writer):
    """
        Test window functioning for logger
    """
    # clean writer
    writer.clear()
    assert len(writer.written) == 0

    # 1 2  ... 3 | 4 5
    logger.limit(3, 0.1, sliding=True)
    logger.add(writer)
    message = _generate_hex()
    # write two instantly
    logger.info(message)
    logger.info(message)
    assert len(writer.written) == 2
    # one 'lagging'
    time.sleep(0.05)
    logger.info(message)
    assert len(writer.written) == 3
    # sleep sufficiently to pass window
    time.sleep(0.05)
    # should be space for two more now
    logger.info(message)
    logger.info(message)
    logger.info(message)
    assert len(writer.written) == 5, 'expected window to limit'

    # clean writer
    writer.clear()
    assert len(writer.written) == 0

    # Now without sliding
    logger.limit(3, 0.1, sliding=False)
    message = _generate_hex()
    # write two instantly
    logger.info(message) # 1
    logger.info(message) # 2
    assert len(writer.written) == 2
    # one 'lagging'
    time.sleep(0.05)
    logger.info(message) # 3
    assert len(writer.written) == 3
    # sleep sufficiently to pass window
    time.sleep(0.05)
    logger.info(message) # 4, only 1 in buffer
    logger.info(message) # 5
    logger.info(message) # 6
    assert len(writer.written) == 6

def test_logger_limit_copy(writer):
    """
        Test limit copy function
    """
    # clean writer
    writer.clear()
    assert len(writer.written) == 0
    logger.add(writer)
    message = _generate_hex()
    for _ in range(10):
        logger.info(message)
    assert len(writer.written) == 10
    # make a hard copy of handlers
    new_logger = logger.limit(0, copy=2)
    for _ in range(10):
        new_logger.info(message)
    assert len(writer.written) == 10
    # now alter to accept 1
    new_logger.limit(1)
    for _ in range(10):
        new_logger.info(message)
    assert len(writer.written) == 11
    # testing soft copy, core is not copied
    new_logger = new_logger.limit(copy=1)
    for _ in range(10):
        new_logger.info(message)
    assert len(writer.written) == 11
    new_logger.add(writer)
    new_logger.info(message)
    assert len(writer.written) == 12

def _count_in(writer, what) -> int:
    count = 0
    for line in writer.written:
        if what in line:
            count += 1
    return count

def test_limiter_message(writer):
    """
        Test limit copy function
    """
    # clean writer
    writer.clear()
    assert len(writer.written) == 0
    logger.add(writer)
    message = _generate_hex()
    overflow = _generate_hex()
    logger.limit(1, message=overflow)
    logger.info(message)
    assert _count_in(writer, message) == 1
    logger.info(message)
    logger.info(message)
    assert _count_in(writer, message) == 1, 'expected exactly one message'
    assert _count_in(writer, overflow) == 1, 'expected exactly one overflow message'
