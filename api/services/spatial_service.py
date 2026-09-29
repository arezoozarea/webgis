
from repositories.spatial_repository import SpatialRepository


class SpatialService:

    @staticmethod
    def get_nearby_metros(
        hospital_id: int,
        distance: int
    ):

        return SpatialRepository.get_nearby_metros(
            hospital_id,
            distance
        )
    @staticmethod
    def get_hospital_buffer(
        hospital_id: int,
        distance: int
    ):

        return SpatialRepository.get_hospital_buffer(
            hospital_id,
            distance
        )
    
    @staticmethod
    def get_neighborhood_streets(
        neighborhood_id: int
    ):
        return SpatialRepository.get_neighborhood_streets(
            neighborhood_id
        )
    @staticmethod
    def get_neighbor_restaurants(
        neighbor_id: int
    ): 
        return SpatialRepository.get_neighbor_restaurants(
            neighbor_id
        )
    @staticmethod
    def nearest_metro_analysis(
        hospital_id: int
    ):
        return SpatialRepository.nearest_metro_analysis(
            hospital_id
        )

    @staticmethod
    def  hospitals_rank():
        return SpatialRepository.hospitals_rank()
