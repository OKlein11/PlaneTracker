import datetime

from flaskapp.fr24_client import MAX_ATTEMPTS, RETRY_INTERVAL, should_attempt_lookup

NOW = datetime.datetime(2026, 1, 1, 12, 0, 0)


def _row(fr24_id=None, attempts=0, last_attempt_at=None):
    return {
        "fr24_id": fr24_id,
        "fr24_lookup_attempts": attempts,
        "fr24_last_attempt_at": last_attempt_at,
    }


def test_no_attempt_once_succeeded():
    row = _row(fr24_id="abc123", attempts=1, last_attempt_at=NOW)
    assert should_attempt_lookup(row, now=NOW) is False


def test_attempts_before_first_try():
    row = _row(attempts=0)
    assert should_attempt_lookup(row, now=NOW) is True


def test_gives_up_after_max_attempts():
    row = _row(attempts=MAX_ATTEMPTS, last_attempt_at=NOW - datetime.timedelta(hours=1))
    assert should_attempt_lookup(row, now=NOW) is False


def test_withholds_retry_within_backoff_window():
    row = _row(attempts=1, last_attempt_at=NOW - (RETRY_INTERVAL / 2))
    assert should_attempt_lookup(row, now=NOW) is False


def test_retries_after_backoff_window_elapses():
    row = _row(attempts=1, last_attempt_at=NOW - RETRY_INTERVAL)
    assert should_attempt_lookup(row, now=NOW) is True


def test_retries_when_last_attempt_missing():
    row = _row(attempts=1, last_attempt_at=None)
    assert should_attempt_lookup(row, now=NOW) is True
