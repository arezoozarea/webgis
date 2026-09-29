from fastapi import APIRouter, Query
from services.SpatialProfileService.RouteService import RouteService

router = APIRouter(prefix="/routes", tags=["routes"])


@router.get("/",summary="Get driving route",
    operation_id="getDrivingRoute") 

def get_route(
        origin_lat: float = Query(..., ge=-90, le=90),
        origin_lon: float = Query(..., ge=-180, le=180),
        destination_lat: float = Query(..., ge=-90, le=90),
        destination_lon: float = Query(..., ge=-180, le=180)):
    result = RouteService.get_route(
        origin_lat=origin_lat,
        origin_lon=origin_lon,
        destination_lat=destination_lat,
        destination_lon=destination_lon,
    )

    return {
        "distance": result["distance"],
        "duration": result["duration"],
        "polylines": result["polylines"],
    }
