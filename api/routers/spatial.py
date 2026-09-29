from fastapi import APIRouter

from services.spatial_service import SpatialService

router = APIRouter()


@router.get("/nearby-metros")
def get_nearby_metros(
    hospital_id: int,
    distance: int = 500
):

    return SpatialService.get_nearby_metros(
        hospital_id,
        distance
    )
@router.get("/hospital-buffer")
def get_hospital_buffer(
    hospital_id: int,
    distance: int = 500
):

    return SpatialService.get_hospital_buffer(
        hospital_id,
        distance
    )

@router.get("/neighborhood-streets")
def get_neighborhood_streets(
    neighborhood_id: int
):
    return SpatialService.get_neighborhood_streets(
        neighborhood_id
    )
@router.get("/neighbor-restaurants")
def get_neighbor_restaurants(
    neighbor_id: int
):
    return SpatialService.get_neighbor_restaurants(
        neighbor_id
    )
@router.get("/nearest-metro-analysis")
def nearest_metro_analysis(
    hospital_id: int
):
    return SpatialService.nearest_metro_analysis(
        hospital_id
    )
@router.get("/hospitals-rank")
def hispitals_rank(
    ):
    return SpatialService.hospitals_rank(
        
    )
