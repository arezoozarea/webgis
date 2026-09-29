from constants.location_layer import  ILocationPoint
from sqlalchemy import text
from db import engine
from constants.constant_layer import spatial_layers

def get_nearest_points(start_lat: float, start_lon: float, layer: str,
                      limit: int = 10) -> list[ILocationPoint]:
    table = spatial_layers.get(layer)
    if table is None:
        raise ValueError(f"Unknown spatial layer: {layer}")
    sql = text(f"""
    SELECT
        id AS end_id,
        name AS end_name,
        ST_Y(geom) AS end_lat,
        ST_X(geom) AS end_lon
    FROM public.{table}
    WHERE geom IS NOT NULL
    ORDER BY geom <-> ST_SetSRID(
        ST_MakePoint(:start_lon, :start_lat),
        4326
    )
    LIMIT :limit
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql, {"start_lon": start_lon, "start_lat": start_lat,
                                  "limit": limit}).mappings().all()
        return [ILocationPoint(end_id=row['end_id'], end_name=row['end_name'], end_lat=row['end_lat'],
                               end_lon=row['end_lon']) for row in rows]
