from flaskapp.db import get_db
from flask import redirect, url_for, Blueprint, request
import datetime

DUMP_TO_SQL_MAP = {
    "hex": "icao",
    "flight": "ident",
    "alt_baro": "alt_baro",
    "alt_geom": "alt_geom",
    "gs": "groundspeed",
    "track": "track",
    "baro_rate": "baro_rate",
    "squawk": "squawk",
    "category": "category",
    "lat": "latitude",
    "long": "longitude"
}


bp = Blueprint("data_add", __name__)


@bp.route("/add_dump", methods=["POST"])
def add_dump():
    print("Test")
    if request.method == "POST":
        db = get_db()

        data = request.get_json()
        print(data)
        for flight in data["aircraft"]:
            keys = ""
            values = []
            for dump, sql in DUMP_TO_SQL_MAP.items():
                if dump in flight.keys():
                    keys += f", {sql}"
                    values.append(flight[dump])
            print(values)
            print(keys)
            keys += f", datetime"
            values.append(datetime.datetime.now())
            db.execute(f"INSERT INTO flights ({keys}) VALUES (?,?)")
        db.commit()

