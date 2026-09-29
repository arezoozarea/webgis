from dataclasses import dataclass


@dataclass(frozen=True)
class ILocationRequest:
    start_lat: float
    start_lon: float


@dataclass(frozen=True)
class ILocationPoint:
    end_id: int
    end_lat: float
    end_lon: float
    end_name: str

@dataclass(frozen=True)
class ILocationTable:
    name: str
    id_column: str
    name_column: str
    geom_column: str
