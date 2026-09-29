from sqlalchemy import create_engine, text
BASELINE_SQL = text("""
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
WITH p AS (
    SELECT ST_Transform(
        ST_SetSRID(
            ST_MakePoint(:lon, :lat),
            4326
        ),
        32639
    ) AS geom
)
SELECT
    c.id
FROM customer_addresses c
CROSS JOIN p
WHERE
    c.geom IS NOT NULL
    AND ST_Distance(
        ST_Transform(c.geom, 32639),
        p.geom
    ) <= 2000
ORDER BY
    ST_Distance(
        ST_Transform(c.geom, 32639),
        p.geom
    )
LIMIT 10;
""")


OPTIMIZED_SQL = text("""
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
WITH p AS (
    SELECT ST_Transform(
        ST_SetSRID(
            ST_MakePoint(:lon, :lat),
            4326
        ),
        32639
    ) AS geom
)
SELECT
    c.id
FROM customer_addresses c
CROSS JOIN p
WHERE
    c.geom IS NOT NULL
    AND ST_DWithin(
        ST_Transform(c.geom, 32639),
        p.geom,
        2000
    )
ORDER BY
    ST_Transform(c.geom, 32639) <-> p.geom
LIMIT 10;
""")
