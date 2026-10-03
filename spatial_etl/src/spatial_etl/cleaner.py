from dataclasses import dataclass
from sqlalchemy import create_engine, text, Engine
from spatial_etl.config import (
    IDatabaseConfig,
    IValidationConfig,
    build_db_url,
)
from spatial_etl.validator import IValidationResult


@dataclass
class ICleanResult:
    source_table: str
    clean_table: str
    source_rows: int
    clean_rows: int
    repaired_rows: int
    rejected_rows: int
    quarantined_rows: int


def get_engine(config: IDatabaseConfig) -> Engine:
    return (create_engine(build_db_url(config)))


def create_clean_table(table_name: str) -> str:
    return f"clean_{table_name}"


def get_table_statistics(engine: Engine, schema: str, table_name: str) -> int:
    sql = text(f"""SELECT count(*) as table_count FROM {schema}.{table_name};""")
    with engine.connect() as conn:
        return conn.execute(sql).scalar_one()
def initialize_clean_table(
    engine: Engine,
    schema: str,
    source_table: str,
    clean_table: str,
) -> None:

    sql = text(f"""
        DROP TABLE IF EXISTS {schema}.{clean_table};

        CREATE TABLE {schema}.{clean_table}
        AS
        SELECT *
        FROM {schema}.{source_table};
    """)

    with engine.begin() as conn:
        conn.execute(sql)

def repair_invalid_geometries(
    engine: Engine,
    schema: str,
    table_name: str,
    geom: str,
) -> None:

    sql = text(f"""
        UPDATE {schema}.{table_name}
        SET {geom} = ST_MakeValid({geom})
        WHERE {geom} IS NOT NULL
          AND NOT ST_IsEmpty({geom})
          AND NOT ST_IsValid({geom});
    """)

    with engine.begin() as conn:
        result = conn.execute(sql)
        return ressult.rowcount


def remove_rejected_rows(
    engine: Engine,
    schema: str,
    table_name: str,
    geom: str,
) -> None:

    sql = text(f"""
        DELETE FROM {schema}.{table_name}
        WHERE {geom} IS NULL
           OR ST_IsEmpty({geom});
    """)

    with engine.begin() as conn:
        result= conn.execute(sql)
        return result.rowcount

def quarantine_out_of_bounds(
    engine: Engine,
    validation_config: IValidationConfig,
    source_table: str,
    clean_table: str,
    geom: str,
) -> None:

    quarantine_table = f"quarantine_{source_table}"

    sql = text(f"""
        DROP TABLE IF EXISTS
            {validation_config.schema}.{quarantine_table};

        CREATE TABLE
            {validation_config.schema}.{quarantine_table}
        AS
        SELECT *
        FROM {validation_config.schema}.{clean_table}
        WHERE {geom} IS NOT NULL
          AND NOT ST_IsEmpty({geom})
          AND (
              ST_X(ST_PointOnSurface({geom}))
                  NOT BETWEEN :min_lon AND :max_lon
              OR
              ST_Y(ST_PointOnSurface({geom}))
                  NOT BETWEEN :min_lat AND :max_lat
          );

        DELETE
        FROM {validation_config.schema}.{clean_table}
        WHERE {geom} IS NOT NULL
          AND NOT ST_IsEmpty({geom})
          AND (
              ST_X(ST_PointOnSurface({geom}))
                  NOT BETWEEN :min_lon AND :max_lon
              OR
              ST_Y(ST_PointOnSurface({geom}))
                  NOT BETWEEN :min_lat AND :max_lat
          );
    """)

    with engine.begin() as conn:
        result = conn.execute(
            sql,
            {
                "min_lon": validation_config.min_lon,
                "max_lon": validation_config.max_lon,
                "min_lat": validation_config.min_lat,
                "max_lat": validation_config.max_lat,
            },
        )
        return result.rowcount

def clean_table(
    engine: Engine,
    validation_config: IValidationConfig,
    validation_result: IValidationResult,
) -> ICleanResult:
    repaired_rows = 0
    rejected_rows = 0
    quarantined_rows = 0
    geom = validation_result.geometry_column
    source_table = validation_result.table_name
    cleaned_table = create_clean_table(source_table)

    source_rows = get_table_statistics(
        engine,
        validation_config.schema,
        source_table,
    )

    initialize_clean_table(
        engine=engine,
        schema=validation_config.schema,
        source_table=source_table,
        clean_table=cleaned_table,
    )

    if validation_result.invalid_geometry_count > 0:
        repaired_rows= repair_invalid_geometries(
            engine=engine,
            schema=validation_config.schema,
            table_name=cleaned_table,
            geom=geom,
        )

    if (
        validation_result.null_geometry_count > 0
        or validation_result.empty_geometry_count > 0
    ):
        rejected_rows= remove_rejected_rows(
            engine=engine,
            schema=validation_config.schema,
            table_name=cleaned_table,
            geom=geom,
        )

    if validation_result.wrong_srid_count > 0:
        print(
            f"[REPORT] {source_table}: "
            f"{validation_result.wrong_srid_count} rows "
            f"have unexpected SRID"
        )
    
    if validation_result.out_of_bounds_count > 0:

        quarantined_rows = quarantine_out_of_bounds(
        engine=engine,
        validation_config=validation_config,
        source_table=source_table,
        clean_table=cleaned_table,
        geom=geom,
       )
    clean_rows = get_table_statistics(
        engine,
        validation_config.schema,
        cleaned_table,
    )

    return ICleanResult(
        source_table=source_table,
        clean_table=cleaned_table,
        source_rows=source_rows,
        clean_rows=clean_rows,
        repaired_rows=repaired_rows,
        rejected_rows=rejected_rows,
        quarantined_rows=quarantined_rows,
  )


def clean_database(
    db_config: IDatabaseConfig,
    validation_config: IValidationConfig,
    validation_results: list[IValidationResult],
) -> list[ICleanResult]:

    engine = get_engine(db_config)

    try:
        results = [
            clean_table(
                engine,
                validation_config,
                validation_result,
            )
            for validation_result in validation_results
        ]

        print_results(results)
        return results

    finally:
        engine.dispose()

def print_results(results: list[ICleanResult]) -> None:
    print("")
    print("Clean summary")
    print("-------------")
    print(f"Tables:      {len(results)}")
    print(f"Source rows: {sum(r.source_rows for r in results)}")
    print(f"Clean rows:  {sum(r.clean_rows for r in results)}")
    print(f"Repaired:    {sum(r.repaired_rows for r in results)}")
    print(f"Rejected:    {sum(r.rejected_rows for r in results)}")
    print(f"Quarantined: {sum(r.quarantined_rows for r in results)}")
