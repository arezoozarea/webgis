
from spatial_etl.cleaner import clean_database
from spatial_etl.config import (
    DBS_CONFIG,
    IMPORT_CONFIG,
    VALIDATION_CONFIG,
)
from spatial_etl.importer import import_directory
from spatial_etl.validator import validate_database
from uuid import uuid4 
from spatial_etl.audit import save_validation_log 

def main():
    run_id= uuid4()
    print(f"ETL run: {run_id}")
    print("=== IMPORT ===")

    import_result = import_directory(
        import_config=IMPORT_CONFIG,
        dbs_config=DBS_CONFIG,
    )

    print(import_result)

    print("=== VALIDATE RAW ===")

    validation_results = validate_database(
        dbs_config=DBS_CONFIG,
        validation_config=VALIDATION_CONFIG,
        clean_only= False
    )
    save_validation_log(
    db_config=DBS_CONFIG,
    run_id=run_id,
    results=validation_results,
    )

    print("=== CLEAN ===")

    clean_results = clean_database(
        db_config=DBS_CONFIG,
        validation_config=VALIDATION_CONFIG,
        validation_results=validation_results,
    )
    print("=== VALIDATE CLEAN ===")

    clean_validation_results = validate_database(
        dbs_config=DBS_CONFIG,
        validation_config=VALIDATION_CONFIG,
        clean_only=True,
)


if __name__ == "__main__":
    main()
