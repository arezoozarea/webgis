from fastapi import APIRouter
from services.SpatialProfileService.SpatialProfile import get_location_profile
from constants.location_layer import ILocationRequest

router = APIRouter(
    prefix="/location-profile",
    tags=["Location Profile"],
)




@router.get("")
def location_profile(lat: float, lon: float):
    request = ILocationRequest(start_lat= lat,start_lon= lon)
    return get_location_profile(request)
