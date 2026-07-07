DROP TABLE IF EXISTS flights;

CREATE TABLE flights (
    date_time NUMERIC,
    flight TEXT,
    icao TEXT PRIMARY KEY,
    alt_baro NUMERIC,
    alt_geom NUMERIC,
    groundspeed NUMERIC,
    track NUMERIC,
    baro_rate NUMERIC,
    squawk TEXT,
    category TEXT,
    latitude NUMERIC,
    longitude NUMERIC,
    heading NUMERIC,
    registration TEXT,
    fr24_id TEXT,
    operating_as TEXT,
    plane_type TEXT,
    orig_icao TEXT,
    dest_icao TEXT,
    dest_icao_actual TEXT,
    datetime_takeoff NUMERIC,
    datetime_landing NUMERIC,
    flight_ended BOOLEAN
);