from uuid import uuid4

from airflow.sdk import DAG, task

from spatial_etl.audit import save_validation_log
from spatial_etl.cleaner import clean_database
from spatial_etl.config import (
    DBS_CONFIG,
    IMPORT_CONFIG,
    VALIDATION_CONFIG,
)
from spatial_etl.importer import import_directory
from spatial_etl.validator import validate_database


with DAG(
    dag_id="spatial_etl_pipeline",
    schedule=None,
    catchup=False,
    tags=["postgis", "spatial-etl"],
):

    @task
    def import_data():
        result = import_directory(
            import_config=IMPORT_CONFIG,
            dbs_config=DBS_CONFIG,
        )

        if result.failed > 0:
            raise RuntimeError(
                f"Import failed for {result.failed} file(s)"
            )


    @task
    def validate_raw() -> str:
        results = validate_database(
            dbs_config=DBS_CONFIG,
            validation_config=VALIDATION_CONFIG,
            clean_only=False,
        )

        run_id = str(uuid4())

        save_validation_log(
            db_config=DBS_CONFIG,
            run_id=run_id,
            results=results,
        )

        return run_id


    @task
    def clean_data():
        validation_results = validate_database(
            dbs_config=DBS_CONFIG,
            validation_config=VALIDATION_CONFIG,
            clean_only=False,
        )

        clean_database(
            db_config=DBS_CONFIG,
            validation_config=VALIDATION_CONFIG,
            validation_results=validation_results,
        )


    @task
    def validate_clean():
        validate_database(
            dbs_config=DBS_CONFIG,
            validation_config=VALIDATION_CONFIG,
            clean_only=True,
        )


    imported = import_data()
    raw_validated = validate_raw()
    cleaned = clean_data()
    clean_validated = validate_clean()

    imported >> raw_validated >> cleaned >> clean_validated
