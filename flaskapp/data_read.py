from flaskapp.db import get_db
from flask import redirect, url_for, Blueprint, request
import datetime



bp = Blueprint("data_read", __name__)


@bp.route("/all_data", methods=["GET"])
def get_all_data():
    db= get_db()
    
    return {"data":[dict(x) for x in db.execute("SELECT * FROM flights").fetchall()]}


@bp.route("/recent_data", methods=["GET"])
def get_recent_data():
    db = get_db()

    query = f"""SELECT flight, registration, dest_icao, orig_icao, alt_baro, latitude, longitude
            FROM flights
            WHERE 1=1
            AND dest_icao IS NOT NULL
            AND orig_icao IS NOT NULL
            AND latitude is NOT NULL
            AND longitude is NOT NULL
            AND date_time > '{datetime.datetime.now() - datetime.timedelta(minutes=1)}'
            AND (flight is NOT NULL or registration is NOT NULL)"""
    
    results = db.execute(query).fetchall()

    return {"data": [dict(x) for x in results]}