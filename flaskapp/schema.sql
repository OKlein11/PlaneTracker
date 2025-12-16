DROP TABLE IF EXISTS flights;

CREATE TABLE flights (
    date_time NUMERIC,
    ident TEXT PRIMARY KEY,
    icao TEXT,
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
);