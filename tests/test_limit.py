from time import sleep
from loguru import logger


def test_limit_log_once(writer):
    overflow_msg = "overflow test"
    logger.add(writer, format="{message}")
    limit_logger = logger.limit(
        frequency_limit=1, time_limit=1, overflow_msg=overflow_msg
    )

    for _ in range(5):
        limit_logger.debug("test")

    lines = writer.read().strip().splitlines()

    assert lines[0] == "test"
    assert len(lines) == 2
    assert lines[-1] == overflow_msg


def test_limit_log_n_times(writer):
    # Check the logs are printed maximum of N times up until time limit is reached
    # And that new logs are printed after a new start_time is set
    n = 10
    overflow_msg = "overflow test"
    logger.add(writer, format="{message}")
    limit_logger = logger.limit(
        frequency_limit=n, time_limit=1, overflow_msg=overflow_msg
    )

    for _ in range(2 * n):
        limit_logger.info("test")

    lines = writer.read().strip().splitlines()

    assert lines[0] == "test"
    assert len(lines) == n + 1
    assert lines[-1] == overflow_msg


def test_limit_timestamps_not_full(writer):
    # Check that the window slides over maximum a couple of time stamps
    n = 2
    time_limit = 1 / 6000  # minutes
    overflow_msg = "overflow test"
    logger.add(writer, format="{message}")
    limit_logger = logger.limit(
        frequency_limit=n, time_limit=time_limit, overflow_msg=overflow_msg
    )

    for _ in range(n + 1):
        limit_logger.success("test")

    sleep(0.02)
    # At this point, the previous log should be ejected in _log, and a new time period starts

    for _ in range(2 * n):
        limit_logger.warning("test")

    lines = writer.read().strip().splitlines()
    print("LINES", lines)
    assert lines[0] == "test"
    assert len(lines) == 2 * (n + 1)  # 1 debug log + (n debug logs + 1 overflow log)
    assert lines[-1] == overflow_msg


def test_limit_timestamps_full(writer):
    # Check that the window slides over maximum number of time stamps
    n = 2
    time_limit = 1 / 6000  # minutes
    overflow_msg = "overflow test"
    logger.add(writer, format="{message}")
    limit_logger = logger.limit(
        frequency_limit=n, time_limit=time_limit, overflow_msg=overflow_msg
    )

    for _ in range(2 * n):
        limit_logger.error("test")

    sleep(0.02)

    for _ in range(2 * n):
        limit_logger.critical("test")

    lines = writer.read().strip().splitlines()

    assert lines[0] == "test"
    assert len(lines) == (n + 1) * 2
    assert lines[-1] == overflow_msg


def test_limit_no_overflow_msg_provided(writer):
    logger.add(writer, format="{message}")
    limit_logger = logger.limit(frequency_limit=1, time_limit=1)
    default_overflow_msg = "Overflow, future logs will be suppressed"
    for _ in range(3):
        limit_logger.debug("test")

    lines = writer.read().strip().splitlines()

    assert lines[0] == "test"
    assert len(lines) == 2
    assert lines[-1] == default_overflow_msg
