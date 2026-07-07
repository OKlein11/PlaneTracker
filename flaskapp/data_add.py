import datetime
import logging

from flask import Blueprint, request

from . import fr24_client, repository
from .convert import icao_to_n
from .db import get_db

logger = logging.getLogger(__name__)

bp = Blueprint("data_add", __name__)


def _derive_registration(icao_hex_raw):
    if icao_hex_raw[0] == "a":
        return icao_to_n(icao_hex_raw).strip()
    return None


def _has_lookup_key(flight_row):
    registration = flight_row["registration"]
    return flight_row["flight"] is not None or (registration is not None and registration[0] == "N")


def _enrich_from_fr24(db, icao):
    flight_row = repository.get_flight(db, icao)
    if not _has_lookup_key(flight_row) or not fr24_client.should_attempt_lookup(flight_row):
        return

    repository.record_fr24_attempt(db, icao, datetime.datetime.now())
    fr24_data = fr24_client.lookup(flight=flight_row["flight"], registration=flight_row["registration"])
    if fr24_data is not None:
        repository.record_fr24_result(db, icao, fr24_data)
        logger.info("fr24 enrichment succeeded for icao=%s fr24_id=%s", icao, fr24_data.fr24_id)


@bp.route("/add_dump", methods=["POST"])
def add_dump():
    db = get_db()
    data = request.get_json()

    for adsb_record in data["aircraft"]:
        icao = adsb_record["hex"].strip()
        registration = _derive_registration(adsb_record["hex"])

        repository.upsert_flight(db, adsb_record, registration)
        _enrich_from_fr24(db, icao)

    return "", 201


@bp.route("/delete_old_data", methods=["GET"])
def delete_old_data():
    db = get_db()
    repository.delete_stale(db, minutes=10)
    return "Success", 200
