create extension if not exists postgis;
CREATE TABLE hospitals (
    id SERIAL PRIMARY KEY,
    name TEXT,
    full_name text,
    lon DOUBLE PRECISION,
    lat DOUBLE PRECISION,
    geom GEOMETRY(Point, 4326)
);

CREATE TABLE metro_stations (
    id SERIAL PRIMARY KEY,
    name TEXT,
    full_name text,
    lon DOUBLE PRECISION,
    lat DOUBLE PRECISION,
    geom GEOMETRY(Point, 4326)
);
