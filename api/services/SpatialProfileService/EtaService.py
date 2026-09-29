import requests
from typing import Optional
import os
session= requests.Session()
BASE_URL = "https://api.parsimap.ir/direction/eta"
API_KEY = os.environ["PARSI_API_KEY"]
CONCURRENCY = 15
TIMEOUT = 5


def build_params(start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> dict:
    return {
        "key": API_KEY,
        "travel_mode": "driving",
        "traffic": "true",
        "waypoints": f"{start_lon},{start_lat}|{end_lon},{end_lat}",
        "request_id": "0123456789"
    }


def get_eta(start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> Optional[float]: 
    params = build_params(start_lat, start_lon, end_lat, end_lon)
    try:
        response = session.get(BASE_URL, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        legs = data.get("legs")
        if not legs:
            return None
        leg= legs[0]
        return {
            "distance": leg["distance"]["value"],
            "duration": round(leg["duration"]["value"] / 60, 1),
        }
    except (
             requests.RequestException,KeyError, ValueError,
             IndexError) as exc:
                            print( "ETA ERROR |" f"{type(exc).__name__}: {exc}")
        
                            return None
