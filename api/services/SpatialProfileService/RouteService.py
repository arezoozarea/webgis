import requests
import os

class RouteService():
    ROUTE_URL = "https://api.parsimap.ir/direction/route"
    API_KEY = os.environ["PARSI_API_KEY"]
    CONCURRENCY = 15
    TIMEOUT = 30.0

    @classmethod
    def get_route(cls, origin_lat: float, origin_lon: float, destination_lat: float, destination_lon: float) -> dict:
        try:
            response = requests.get(
                cls.ROUTE_URL,
                params={
                    "key": cls.API_KEY,
                    "travel_mode": "driving",
                    "alternatives": 1,
                    "steps": "true",
                    "traffic": "true",
                    "waypoints": (
                        f"{origin_lon},{origin_lat}|"
                        f"{destination_lon},{destination_lat}"
                    ),
                    "request_id": "false",
                },
                timeout=cls.TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
            route = data["routes"][0]
            leg = route["legs"][0]
            steps = leg["steps"]
            result = {"success": True, "distance": sum(step["distance"]["value"] for step in steps),
                      "duration": sum(step["duration"]["value"] for step in steps),
                      "polylines": [step["polyline"]["points"] for step in steps if
                                    step.get("polyline", {}).get("points")], "error": None}
            return result
        except requests.Timeout:
            return {
                "success": False,
                "distance": None,
                "duration": None,
                "polylines": [],
                "error": "ROUTE_TIMEOUT",
            }
        except requests.RequestException:
            return {
                "success": False,
                "distance": None,
                "duration": None,
                "polylines": [],
                "error": "ROUTE_REQUEST_FAILED",
            }
        except (KeyError, IndexError, TypeError, ValueError):
            return {
                "success": False,
                "distance": None,
                "duration": None,
                "polylines": [],
                "error": "ROUTE_INVALID_RESPONSE",
            }
