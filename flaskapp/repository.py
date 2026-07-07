import datetime

# Maps dump1090 aircraft.json fields to `flights` table columns.
ADSB_FIELD_MAP = {
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
    "lon": "longitude",
}


def upsert_flight(db, adsb_record, registration):
    columns = {"registration": registration, "date_time": datetime.datetime.now()}
    for adsb_key, column in ADSB_FIELD_MAP.items():
        value = adsb_record.get(adsb_key)
        columns[column] = value.strip() if isinstance(value, str) else value

    db.execute(
        """
        INSERT INTO flights (
            icao, registration, flight, alt_baro, alt_geom, groundspeed,
            track, baro_rate, squawk, category, latitude, longitude, date_time
        ) VALUES (
            :icao, :registration, :flight, :alt_baro, :alt_geom, :groundspeed,
            :track, :baro_rate, :squawk, :category, :latitude, :longitude, :date_time
        )
        ON CONFLICT(icao) DO UPDATE SET
            registration=excluded.registration,
            flight=excluded.flight,
            alt_baro=excluded.alt_baro,
            alt_geom=excluded.alt_geom,
            groundspeed=excluded.groundspeed,
            track=excluded.track,
            baro_rate=excluded.baro_rate,
            squawk=excluded.squawk,
            category=excluded.category,
            latitude=excluded.latitude,
            longitude=excluded.longitude,
            date_time=excluded.date_time
        """,
        columns,
    )
    db.commit()


def get_flight(db, icao):
    return db.execute("SELECT * FROM flights WHERE icao = :icao", {"icao": icao}).fetchone()


def record_fr24_attempt(db, icao, now):
    db.execute(
        """
        UPDATE flights
        SET fr24_lookup_attempts = fr24_lookup_attempts + 1,
            fr24_last_attempt_at = :now
        WHERE icao = :icao
        """,
        {"now": now, "icao": icao},
    )
    db.commit()


def record_fr24_result(db, icao, fr24_data):
    db.execute(
        """
        UPDATE flights SET
            fr24_id=:fr24_id,
            operating_as=:operating_as,
            plane_type=:plane_type,
            orig_icao=:orig_icao,
            dest_icao=:dest_icao,
            dest_icao_actual=:dest_icao_actual,
            datetime_takeoff=:datetime_takeoff,
            datetime_landing=:datetime_landing,
            flight_ended=:flight_ended
        WHERE icao=:icao
        """,
        {
            "fr24_id": fr24_data.fr24_id,
            "operating_as": fr24_data.operating_as,
            "plane_type": fr24_data.type,
            "orig_icao": fr24_data.orig_icao,
            "dest_icao": fr24_data.dest_icao,
            "dest_icao_actual": fr24_data.dest_icao_actual,
            "datetime_takeoff": fr24_data.datetime_takeoff,
            "datetime_landing": fr24_data.datetime_landed,
            "flight_ended": fr24_data.flight_ended,
            "icao": icao,
        },
    )
    db.commit()


def get_recent(db, minutes=1):
    cutoff = datetime.datetime.now() - datetime.timedelta(minutes=minutes)
    query = """
        SELECT flight, registration, dest_icao, orig_icao, alt_baro, latitude, longitude
        FROM flights
        WHERE dest_icao IS NOT NULL
          AND orig_icao IS NOT NULL
          AND latitude IS NOT NULL
          AND longitude IS NOT NULL
          AND date_time > :cutoff
          AND (flight IS NOT NULL OR registration IS NOT NULL)
    """
    return db.execute(query, {"cutoff": cutoff}).fetchall()


def delete_stale(db, minutes=10):
    cutoff = datetime.datetime.now() - datetime.timedelta(minutes=minutes)
    db.execute("DELETE FROM flights WHERE date_time < :cutoff", {"cutoff": cutoff})
    db.commit()
