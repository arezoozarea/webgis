from dataclasses import dataclass
from sqlalchemy import create_engine, text, Engine
from spatial_etl.config import (
    IDatabaseConfig,
    IValidationConfig,
    build_db_url,
)
from spatial_etl.validator import ISpatialTableInfo, get_db_tables


@dataclass
class ICleanResult:
    source_table: str
    clean_table: str
    source_rows: int
    clean_rows: int


def get_engine(config: IDatabaseConfig) -> Engine:
    return (create_engine(build_db_url(config)))


def create_clean_table(table_name: str) -> str:
    return f"clean_{table_name}"


def get_table_statistics(engine: Engine, schema: str, table_name: str) -> int:
    sql = text(f"""SELECT count(*) as table_count FROM {schema}.{table_name};""")
    with engine.connect() as conn:
        return conn.execute(sql).scalar_one()


def clean_table(engine: Engine, validation_config: IValidationConfig, table: ISpatialTableInfo) -> ICleanResult:
    geom = table.geometry_column
    source_table = table.table_name
    cleaned_table = create_clean_table(source_table)
    source_rows = get_table_statistics(engine, validation_config.schema, source_table)

    sql = text(f""" drop table if exists {validation_config.schema}.{cleaned_table};
    create table {validation_config.schema}.{cleaned_table} as select * from {validation_config.schema}.{source_table} where {geom} is not null
    and ST_Srid({geom})= :expected_srid and ST_IsValid({geom}) and ST_X(ST_PointOnSurface({geom})) between :min_lon and :max_lon and ST_Y(ST_PointOnSurface({geom}))
     between :min_lat and :max_lat ;
     create index if not exists idx_{cleaned_table}_{geom} on {validation_config.schema}.{cleaned_table} using GIST({geom});""")
    with engine.begin() as conn:
        conn.execute(sql, {"expected_srid": validation_config.expected_srid, "min_lat": validation_config.min_lat,
                           "max_lat": validation_config.max_lat, "min_lon": validation_config.min_lon,
                           "max_lon": validation_config.max_lon})

    clean_rows = get_table_statistics(engine, validation_config.schema, cleaned_table)
    return ICleanResult(source_table=source_table, clean_table=cleaned_table, source_rows=source_rows,
                        clean_rows=clean_rows)


def clean_database(db_config: IDatabaseConfig, validation_config: IValidationConfig) -> list[ICleanResult]:
    engine = get_engine(db_config)
    try:
        tables = get_db_tables(engine, validation_config)
        results = [clean_table(engine, validation_config, table) for table in tables if
                   not table.table_name.startswith('clean_')]
        print_results(results)
        return results
    finally:
        engine.dispose()


def print_results(results: list[ICleanResult]) -> None:
    for result in results:
        print("--------")
        print("clean_result")
        print(
            f"{result.source_table} with {result.source_rows} rows -> {result.clean_table} with {result.clean_rows} rows")
