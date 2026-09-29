import time
import statistics
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
api_url = "http://127.0.0.1:8000/location-profile"
timeout = 10
TOTAL_REQUESTS = 100

POI_LIMIT = 10

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_FILE = RESULTS_DIR / f"api_concurrency_{POI_LIMIT}_poi.json"

CONCURRENCY_LEVELS = [
    1,
    5,
    10,
    20,
]

ORIGINS = [
    (35.70, 51.40),
    (35.72, 51.42),
    (35.74, 51.38),
    (35.69, 51.44),
    (35.76, 51.41),
]


def percentile(values, p):
    values = sorted(values)

    index = (len(values) - 1) * p

    lower = int(index)
    upper = min(lower + 1, len(values) - 1)

    fraction = index - lower

    return (
            values[lower] * (1 - fraction)
            + values[upper] * fraction
    )


def send_request(lat, lon):
    start_time = time.perf_counter()
    try:
        response = requests.get(api_url, params={"lat": lat, "lon": lon}, timeout=timeout)
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        response.raise_for_status()
        return elapsed_ms, None
    except requests.RequestException as exc:
        return None, str(exc)


def request_benchmarks(concurrency):
    times = []
    errors = []
    start_time = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = []
        for i in range(TOTAL_REQUESTS):
            lat, lon = ORIGINS[i % len(ORIGINS)]
            future = executor.submit(send_request, lat, lon)
            futures.append(future)
        for future in as_completed(futures):
            elapsed_ms, error = future.result()
            if error:
                errors.append(error)
            else:
                times.append(elapsed_ms)
    total_seconds = time.perf_counter() - start_time
    return {
        "concurrency": concurrency,
        "runs": TOTAL_REQUESTS,
        "success": len(times),
        "errors": len(errors),
        "min": min(times) if times else None,
        "mean": statistics.mean(times) if times else None,
        "p50": percentile(times, 0.50) if times else None,
        "p95": percentile(times, 0.95) if times else None,
        "p99": percentile(times, 0.99) if times else None,
        "max": max(times) if times else None,
        "throughput_s": TOTAL_REQUESTS / total_seconds,
        "total_time_s": total_seconds,
    }

benchmark_results=[]
for concurrency in CONCURRENCY_LEVELS:
    print(f"running concurrency: {concurrency}...")
    result = request_benchmarks(concurrency)
    benchmark_results.append(result)
    print(
        f"""
    CONCURRENCY {result["concurrency"]}

    runs: {result["runs"]}
    success: {result["success"]}
    errors: {result["errors"]}

    min: {result["min"]:.2f} ms
    mean: {result["mean"]:.2f} ms
    p50: {result["p50"]:.2f} ms
    p95: {result["p95"]:.2f} ms
    p99: {result["p99"]:.2f} ms
    max: {result["max"]:.2f} ms

    throughput: {result["throughput_s"]:.2f} req/s
    total time: {result["total_time_s"]:.2f} s
    """
    )
output = {
    "benchmark": "location_profile_concurrency",
    "config": {
        "api_url": api_url,
        "total_requests": TOTAL_REQUESTS,
        "timeout_seconds": timeout,
        "poi_limit_per_layer": POI_LIMIT,
        "concurrency_levels": CONCURRENCY_LEVELS,
        "origins": [
            {
                "lat": lat,
                "lon": lon,
            }
            for lat, lon in ORIGINS
        ],
    },
    "results": benchmark_results,
}


RESULTS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

with open(
    RESULTS_FILE,
    "w",
    encoding="utf-8",
) as file:
    json.dump(
        output,
        file,
        indent=2,
        ensure_ascii=False,
    )


print(f"\nResult saved to: {RESULTS_FILE}")
