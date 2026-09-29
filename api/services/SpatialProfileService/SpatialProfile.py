from repositories.SpatialProfileRepository.nearest_location import get_nearest_points
from services.SpatialProfileService.EtaService import get_eta
from constants.location_layer import ILocationRequest
from constants.constant_layer import spatial_layers

import time
from concurrent.futures import ThreadPoolExecutor


def get_location_profile(start_point: ILocationRequest):
    result = {}

    total_start = time.perf_counter()

    for layer in spatial_layers:
        layer_start = time.perf_counter()

        nearest_start = time.perf_counter()

        locations = get_nearest_points(
            start_lat=start_point.start_lat,
            start_lon=start_point.start_lon,
            layer=layer,
            limit=10,
        )

        nearest_ms = (
            time.perf_counter() - nearest_start
        ) * 1000


        def fetch_eta(location):
            eta_start = time.perf_counter()

            eta = get_eta(
                start_lat=start_point.start_lat,
                start_lon=start_point.start_lon,
                end_lat=location.end_lat,
                end_lon=location.end_lon,
            )

            eta_ms = (
                time.perf_counter() - eta_start
            ) * 1000
            if eta_ms> 500:

                print(
                    f"SLOW ETA | "
                    f"layer={layer} | "
                    f"poi={location.end_id} | "
                    f"time={eta_ms:.2f} ms"
                 )

            return {
                "poi": {
                    "id": location.end_id,
                    "name": location.end_name,
                    "lat": location.end_lat,
                    "lon": location.end_lon,
                },
                "eta": {
                    "distance":
                        eta["distance"]
                        if eta else None,
                    "distanceUnit": "meter",
                    "duration":
                        eta["duration"]
                        if eta else None,
                    "durationUnit": "minute",
                    "error":
                        None
                        if eta
                        else "ETA_SERVICE_UNAVAILABLE",
                }
            }


        eta_start = time.perf_counter()

        with ThreadPoolExecutor(max_workers=10) as executor:
            layer_result = list(
                executor.map(
                    fetch_eta,
                    locations
                )
            )

        eta_batch_ms = (
            time.perf_counter() - eta_start
        ) * 1000


        layer_result.sort(
            key=lambda item:
                item["eta"]["duration"]
                if item["eta"]["duration"] is not None
                else float("inf")
        )

        result[layer] = layer_result


        layer_total_ms = (
            time.perf_counter() - layer_start
        ) * 1000

        print(
            f"LAYER | "
            f"{layer} | "
            f"nearest={nearest_ms:.2f} ms | "
            f"eta_batch={eta_batch_ms:.2f} ms | "
            f"total={layer_total_ms:.2f} ms"
        )


    total_ms = (
        time.perf_counter() - total_start
    ) * 1000

    print(
        f"LOCATION_PROFILE TOTAL: "
        f"{total_ms:.2f} ms"
    )

    return result
