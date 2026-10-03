from sqlalchemy import create_engine, text

from spatial_etl.config import IDatabaseConfig, build_db_url
from spatial_etl.validator import IValidationResult


def save_validation_log(
    db_config: IDatabaseConfig,
    run_id: str,
    results: list[IValidationResult],
) -> None:

    engine = create_engine(build_db_url(db_config))

    sql = text("""
        INSERT INTO public.etl_validation_log
        (
            run_id,
            table_name,
            total_rows,
            null_geometry_count,
            empty_geometry_count,
            invalid_geometry_count,
            wrong_srid_count,
            out_of_bounds_count
        )
        VALUES
        (
            :run_id,
            :table_name,
            :total_rows,
            :null_geometry_count,
            :empty_geometry_count,
            :invalid_geometry_count,
            :wrong_srid_count,
            :out_of_bounds_count
        );
    """)

    try:
        with engine.begin() as conn:

            for result in results:

                # فقط جدول‌هایی که مشکل دارند
                if result.issue_count == 0:
                    continue

                conn.execute(
                    sql,
                    {
                        "run_id": run_id,
                        "table_name": result.table_name,
                        "total_rows": result.total_rows,
                        "null_geometry_count": result.null_geometry_count,
                        "empty_geometry_count": result.empty_geometry_count,
                        "invalid_geometry_count": result.invalid_geometry_count,
                        "wrong_srid_count": result.wrong_srid_count,
                        "out_of_bounds_count": result.out_of_bounds_count
                    },
                )

    finally:
        engine.dispose()
