import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class IDatabaseConfig:
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str


@dataclass(frozen=True)
class IImportConfig:
    data_dir: Path
    schema: str


@dataclass(frozen=True)
class IValidationConfig:
    schema: str
    expected_srid: int
    min_lon: float
    max_lon: float
    min_lat: float
    max_lat: float


DBS_CONFIG = IDatabaseConfig(
    db_host=os.environ["POSTGRES_HOST"],
    db_port=int(os.environ["POSTGRES_PORT"]),
    db_name=os.environ["POSTGRES_DB"],
    db_user=os.environ["POSTGRES_USER"],
    db_password=os.environ["POSTGRES_PASSWORD"],
)


IMPORT_CONFIG = IImportConfig(
    data_dir=Path(os.environ["SPATIAL_DATA_DIR"]),
    schema="public",
)


VALIDATION_CONFIG = IValidationConfig(
    schema="public",
    expected_srid=4326,
    min_lon=51.0,
    max_lon=51.8,
    min_lat=35.4,
    max_lat=35.95,
)


def build_db_url(config: IDatabaseConfig) -> str:
    return (
        f"postgresql://{config.db_user}:{config.db_password}"
        f"@{config.db_host}:{config.db_port}/{config.db_name}"
    )
