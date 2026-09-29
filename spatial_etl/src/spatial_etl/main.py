from spatial_etl.config import IMPORT_CONFIG, DBS_CONFIG, VALIDATION_CONFIG
from spatial_etl.importer import import_directory
from spatial_etl.validator import validate_database
from spatial_etl.cleaner import clean_database

def run() -> None:
    import_directory(IMPORT_CONFIG,DBS_CONFIG)
    validate_database(DBS_CONFIG, VALIDATION_CONFIG)
    clean_database(DBS_CONFIG, VALIDATION_CONFIG)


if __name__ == "__main__":
    run()
