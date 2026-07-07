from flaskapp.db import get_db
from flask import redirect, url_for, Blueprint, request
from .convert import icao_to_n
import datetime
from fr24sdk.client import Client, FlightSummaryResource
from . import secrets 
import time

DUMP_TO_SQL_MAP = {
    "hex": "icao",
    "flight": "flight",
    "alt_baro": "alt_baro",
    "alt_geom": "alt_geom",
    "gs": "groundspeed",
    "track": "track",
    "baro_rate": "baro_rate",
    "squawk": "squawk",
    "category": "category",
    "lat": "latitude",
    "lon": "longitude"
}


bp = Blueprint("data_add", __name__)


@bp.route("/add_dump", methods=["POST"])
def add_dump():
    print("Test")
    if request.method == "POST":
        db = get_db()

        data = request.get_json()
        for flight in data["aircraft"]:
            print("2", flight["hex"])
            print("3", flight["hex"].strip())
            values = []
            for key in DUMP_TO_SQL_MAP.keys():
                if key in flight.keys():
                    if key == "hex":

                        values.append(flight[key].strip())
                        if flight["hex"][0] == "a" :
                            values.append(icao_to_n(flight[key]).strip())
                        else:
                            values.append(None)
                    else:
                        if type(flight[key]) == type("str"):
                            values.append(flight[key].strip())
                        else:
                            values.append(flight[key])
                else:
                    values.append(None)
            values.append(datetime.datetime.now())


            flight_from_db = db.execute("SELECT registration, flight FROM flights WHERE icao=?", [flight["hex"].strip()]).fetchone()
            if flight_from_db is None:

                db.execute(f"""INSERT INTO flights (
                icao, 
                registration,
                flight, 
                alt_baro, 
                alt_geom, 
                groundspeed, 
                track, 
                baro_rate, 
                squawk, 
                category, 
                latitude, 
                longitude,
                date_time
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?);""", values)
                
                db.commit()
            else:
                values.append(flight["hex"].strip())
                db.execute("""UPDATE flights SET
                           icao=?,
                           registration=?,
                           flight=?,
                           alt_baro=?,
                           alt_geom=?,
                           groundspeed=?,
                           track=?,
                           baro_rate=?,
                           squawk=?,
                           category=?,
                           latitude=?,
                           longitude=?,
                           date_time=?
                           WHERE icao=?;
                           """, values
                )
                db.commit()
            flight_from_db =  db.execute("SELECT fr24_id, flight, registration FROM flights WHERE icao=?", [flight["hex"].strip()]).fetchone()
            print(dict(flight_from_db))
            if flight_from_db["fr24_id"] is None:
                if flight_from_db["flight"] is not None or (flight_from_db["registration"] is not None and flight_from_db["registration"][0] == "N"):
                    try:
                        fr24_data = flight_from_fr24(flight=flight_from_db["flight"], registration=flight_from_db["registration"])
                        if fr24_data != {}:
                            db.execute("""UPDATE flights SET
                                    fr24_id=?,
                                    operating_as=?,
                                    plane_type=?,
                                    orig_icao=?,
                                    dest_icao=?,
                                    dest_icao_actual=?,
                                    datetime_takeoff=?,
                                    datetime_landing=?,
                                    flight_ended=?
                                    WHERE icao=?;
                                    """,
                                    [
                                        fr24_data.fr24_id,
                                        fr24_data.operating_as,
                                        fr24_data.type,
                                        fr24_data.orig_icao,
                                        fr24_data.dest_icao,
                                        fr24_data.dest_icao_actual,
                                        fr24_data.datetime_takeoff,
                                        fr24_data.datetime_landed,
                                        fr24_data.flight_ended,
                                        flight["hex"].strip()
                                    ])
                            db.commit()
                    except Exception as e: 
                        print("Weird FR24 API error",flight["flight"], flight["hex"], e)



    return "",201


 
def flight_from_fr24(flight=None,registration=None):

    client = Client(api_token=secrets.FR24_API_KEY)
    time.sleep(1)
    now = datetime.datetime.now()
    from_dt = now - datetime.timedelta(1)
    to_dt = now + datetime.timedelta(1)
    if flight is not None:
        summary = client.flight_summary.get_light(flights=[flight], 
                                              flight_datetime_from= from_dt.replace(microsecond=0),
                                              flight_datetime_to=to_dt.replace(microsecond=0),
                                              sort="desc")
    elif registration is not None:
        
        summary = client.flight_summary.get_light(registrations=[registration], 
                                              flight_datetime_from=from_dt.replace(microsecond=0),
                                              flight_datetime_to=to_dt.replace(microsecond=0),
                                              sort="desc")

    else: 
        return {}
    if len(summary.data) == 0 and flight is not None:
        summary = client.flight_summary.get_light(callsigns=[flight], 
                                              flight_datetime_from= from_dt.replace(microsecond=0),
                                              flight_datetime_to=to_dt.replace(microsecond=0),
                                              sort="desc")

    if len(summary.data) != 0:
        return summary.data[0]
    else: 
        return {}
    

@bp.route("/delete_old_data", methods=["GET"])
def delete_old_data():
    db = get_db()
    db.execute(f"""
               DELETE FROM flights
               WHERE 1=1
               AND date_time < '{datetime.datetime.now() - datetime.timedelta(minutes=10)}'    
                """
    )
    db.commit()
    return "Success",200
    