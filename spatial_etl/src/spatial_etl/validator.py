from dataclasses import dataclass
from sqlalchemy import create_engine, text, Engine
from spatial_etl.config import (
    IValidationConfig,
    IDatabaseConfig,
    build_db_url,
)


@dataclass
class IValidationResult:
    table_name: str
    total_rows: int
    null_geometry_count: int
    empty_geometry_count: int
    invalid_geometry_count: int
    wrong_srid_count: int
    out_of_bounds_count: int


@dataclass
class ISpatialTableInfo:
    table_name: str
    geometry_column: str
    geometry_type: str


def get_engine(config: IDatabaseConfig) -> Engine:
    return (create_engine(build_db_url(config)))


def get_db_tables(engine: Engine, config: IValidationConfig) -> list[ISpatialTableInfo]:
    sql = text(
        """select f_table_name as table_name,f_geometry_column as geometry_column, type as geometry_type from geometry_columns where f_table_schema = :schema order by f_table_name """)
    with engine.connect() as conn:
        rows = conn.execute(sql, {"schema": config.schema}).mappings().all()
    return [
        ISpatialTableInfo(table_name=row["table_name"], geometry_column=row["geometry_column"], geometry_type=row["geometry_type"])
        for row in rows]


def validate_table(engine: Engine, config: IValidationConfig, table: ISpatialTableInfo) -> IValidationResult:
    table_name = table.table_name
    geom=table.geometry_column
    sql = text(f"""
        SELECT
            COUNT(*) AS total_rows,

            COUNT(*) FILTER (
                WHERE {geom} IS NULL
            ) AS null_geometry_count,

            COUNT(*) FILTER (
                WHERE {geom} IS NOT NULL
                  AND NOT ST_IsValid({geom})
            ) AS invalid_geometry_count,

            COUNT(*) FILTER (
                WHERE {geom} IS NOT NULL
                  AND ST_SRID({geom}) <> :expected_srid
            ) AS wrong_srid_count,
            count(*) filter(where not ST_IsEmpty({geom}) as empty_geometry_count, 
            COUNT(*) FILTER (
                WHERE {geom} IS NOT NULL
                  AND (
                    ST_X(ST_PointOnSurface({geom})) NOT BETWEEN :min_lon AND :max_lon
                    OR
                    ST_Y(ST_PointOnSurface({geom})) NOT BETWEEN :min_lat AND :max_lat
                  )
            ) AS out_of_bounds_count from {config.schema}.{table_name}""")
    with engine.connect() as conn:
        row = conn.execute(sql, {'expected_srid': config.expected_srid, "min_lon": config.min_lon,
                                 "max_lon": config.max_lon,
                                 "min_lat": config.min_lat,
                                 "max_lat": config.max_lat }).mappings().one()
    return IValidationResult(table_name=table_name,
        total_rows=row["total_rows"],
        null_geometry_count=row["null_geometry_count"],
        empty_geometry_count= row["empty_geometry_count"],
        invalid_geometry_count=row["invalid_geometry_count"],
        wrong_srid_count=row["wrong_srid_count"],
        out_of_bounds_count=row["out_of_bounds_count"])

def validate_database(dbs_config: IDatabaseConfig, validation_config: IValidationConfig) -> list[IValidationResult]:
    engine = get_engine(dbs_config)
    try:
        tables = get_db_tables(engine, validation_config)
        results = [validate_table(engine, validation_config, table) for table in tables]
        print_results(results)
        return results
    finally:
        engine.dispose()

def print_results(results: list[IValidationResult]) -> None:
    for result in results:
        print(f"Table: {result.table_name}")
        print(f"  Total rows:       {result.total_rows}")
        print(f"  Null geometry:    {result.null_geometry_count}")
        print(f"empty geometry: {result.empty_geometry_count}")
        print(f"  Invalid geometry: {result.invalid_geometry_count}")
        print(f"  Wrong SRID:       {result.wrong_srid_count}")
        print(f"  Out of bounds:    {result.out_of_bounds_count}")
        print("")
