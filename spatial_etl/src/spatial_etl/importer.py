import csv
import subprocess
import time
from collections.abc import Generator
from dataclasses import dataclass
from pathlib import Path

from spatial_etl.config import IImportConfig,IDatabaseConfig


SUPPORTED_EXTENSIONS = {
    ".geojson",
    ".json",
    ".csv",
}

CSV_X_COLUMNS = {
    "lon",
    "lng",
    "longitude",
}

CSV_Y_COLUMNS = {
    "lat",
    "latitude",
}


@dataclass
class IImportSummary:
    imported: int = 0
    failed: int = 0
    skipped: int = 0


def discover_files(data_dir: Path) -> Generator[Path, None, None]:
    for file_path in data_dir.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield file_path


def normalize_table_name(file_path: Path) -> str:
    return (
        file_path.stem
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )


def build_pg_connection(config: IDatabaseConfig) -> str:
    return (
        f"PG:host={config.db_host} "
        f"port={config.db_port} "
        f"dbname={config.db_name} "
        f"user={config.db_user} "
        f"password={config.db_password}"
    )


def validate_file(file_path: Path) -> None:
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if file_path.stat().st_size == 0:
        raise ValueError(f"File is empty: {file_path}")

    if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {file_path}")


def validate_csv_columns(file_path: Path) -> None:
    if file_path.suffix.lower() != ".csv":
        return

    with file_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.reader(csv_file)
        header = next(reader, None)

    if not header:
        raise ValueError(f"CSV has no header: {file_path}")

    normalized_columns = {
        column.strip().lower()
        for column in header
    }

    has_x = bool(normalized_columns & CSV_X_COLUMNS)
    has_y = bool(normalized_columns & CSV_Y_COLUMNS)

    if not has_x or not has_y:
        raise ValueError(
            f"CSV must contain coordinate columns. "
            f"Expected one of X={CSV_X_COLUMNS}, Y={CSV_Y_COLUMNS}. "
            f"Found={normalized_columns}"
        )


def build_ogr_command(
    file_path: Path,
    table_name: str,
    dbs_config: IDatabaseConfig,
    import_config: IImportConfig
) -> list[str]:
    command = [
        "ogr2ogr",
        "-f",
        "PostgreSQL",
        build_pg_connection(dbs_config),
        str(file_path),
        "-nln",
        f"{import_config.schema}.{table_name}",
        "-overwrite",
        "-lco",
        "GEOMETRY_NAME=geom",
    ]

    if file_path.suffix.lower() == ".csv":
        command.extend(
            [
                "-oo",
                "X_POSSIBLE_NAMES=LON,lon,lng,LNG,longitude,LONGITUDE",
                "-oo",
                "Y_POSSIBLE_NAMES=LAT,lat,latitude,LATITUDE",
                "-a_srs",
                "EPSG:4326",
            ]
        )

    return command


def import_file(file_path: Path, dbs_config: IDatabaseConfig, import_config: IImportConfig) -> None:
    validate_file(file_path)
    validate_csv_columns(file_path)

    table_name = normalize_table_name(file_path)

    command = build_ogr_command(
        file_path=file_path,
        table_name=table_name,
        dbs_config=dbs_config,
        import_config=import_config
    )

    print(f"[IMPORT] {file_path} -> {import_config.schema}.{table_name}")

    subprocess.run(
        command,
        check=True,
    )

    print(f"[SUCCESS] {import_config.schema}.{table_name}")


def import_directory(import_config: IImportConfig, dbs_config: IDatabaseConfig) -> IImportSummary:
    started_at = time.perf_counter()

    summary = IImportSummary()

    files = list(discover_files(import_config.data_dir))

    if not files:
        print(f"[SKIP] No supported files found in {import_config.data_dir}")
        summary.skipped += 1
        return summary

    for file_path in files:
        try:
            import_file(
                file_path=file_path,
                dbs_config=dbs_config,import_config=import_config
            )

            summary.imported += 1

        except subprocess.CalledProcessError as ex:
            summary.failed += 1

            print(f"[FAILED] ogr2ogr failed: {file_path}")
            print(f"[ERROR] {ex}")

        except Exception as ex:
            summary.failed += 1

            print(f"[FAILED] {file_path}")
            print(f"[ERROR] {ex}")

    duration = round(time.perf_counter() - started_at, 2)

    print("")
    print("Import summary")
    print("--------------")
    print(f"Imported: {summary.imported}")
    print(f"Failed:   {summary.failed}")
    print(f"Skipped:  {summary.skipped}")
    print(f"Duration: {duration}s")

    return summary
