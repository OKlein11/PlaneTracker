import datetime
import logging
import time

from pydantic import ValidationError

from fr24sdk.client import Client
from fr24sdk.exceptions import ApiError, TransportError

from . import secrets

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 4
RETRY_INTERVAL = datetime.timedelta(minutes=2)

_client = None


def get_client():
    global _client
    if _client is None:
        _client = Client(api_token=secrets.FR24_API_KEY)
    return _client


def should_attempt_lookup(flight_row, now=None):
    """Decide whether `flight_row` (a `flights` table row) is due for an fr24 lookup.

    Already-successful lookups are never repeated. A failed lookup is retried
    at most every RETRY_INTERVAL, and gives up entirely after MAX_ATTEMPTS.
    """
    now = now or datetime.datetime.now()

    if flight_row["fr24_id"] is not None:
        return False
    if flight_row["fr24_lookup_attempts"] == 0:
        return True
    if flight_row["fr24_lookup_attempts"] >= MAX_ATTEMPTS:
        return False

    last_attempt_at = flight_row["fr24_last_attempt_at"]
    if last_attempt_at is None:
        return True
    return now - last_attempt_at >= RETRY_INTERVAL


def lookup(flight=None, registration=None):
    """Look up flight summary data from fr24 by flight number or registration.

    Falls back to a callsign search if a flight-number search comes up empty.
    Returns None if nothing is found (or no query key was given).
    """
    if flight is None and registration is None:
        return None

    client = get_client()
    time.sleep(1)
    now = datetime.datetime.now()
    from_dt = (now - datetime.timedelta(1)).replace(microsecond=0)
    to_dt = (now + datetime.timedelta(1)).replace(microsecond=0)

    try:
        if flight is not None:
            summary = client.flight_summary.get_light(
                flights=[flight],
                flight_datetime_from=from_dt,
                flight_datetime_to=to_dt,
                sort="desc",
            )
        else:
            summary = client.flight_summary.get_light(
                registrations=[registration],
                flight_datetime_from=from_dt,
                flight_datetime_to=to_dt,
                sort="desc",
            )

        if len(summary.data) == 0 and flight is not None:
            summary = client.flight_summary.get_light(
                callsigns=[flight],
                flight_datetime_from=from_dt,
                flight_datetime_to=to_dt,
                sort="desc",
            )
    except (ApiError, TransportError, ValidationError) as e:
        logger.warning("fr24 lookup failed for flight=%s registration=%s: %s", flight, registration, e)
        return None

    if len(summary.data) == 0:
        return None
    return summary.data[0]
