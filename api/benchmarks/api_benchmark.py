import statistics
import time
from collections import defaultdict
import json
from pathlib import Path
import requests


API_URL = "http://127.0.0.1:8000/location-profile"

ORIGINS = [
    (35.70, 51.40),
    (35.72, 51.42),
    (35.74, 51.38),
    (35.69, 51.44),
    (35.76, 51.41),
]

RUNS = 100
TIMEOUT = 10

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_FILE = RESULTS_DIR / "api_benchmark.json"

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


def summarize(values):
    return {
        "runs": len(values),
        "min": min(values),
        "mean": statistics.mean(values),
        "p50": percentile(values, 0.50),
        "p95": percentile(values, 0.95),
        "p99": percentile(values, 0.99),
        "max": max(values),
    }


latencies = []
latencies_by_origin = defaultdict(list)

errors = 0
errors_by_origin = defaultdict(int)


for i in range(RUNS):
    lat, lon = ORIGINS[i % len(ORIGINS)]

    start = time.perf_counter()

    try:
        response = requests.get(
            API_URL,
            params={
                "lat": lat,
                "lon": lon,
            },
            timeout=TIMEOUT,
        )

        elapsed_ms = (
            time.perf_counter() - start
        ) * 1000

        if response.ok:
            latencies.append(elapsed_ms)

            latencies_by_origin[
                (lat, lon)
            ].append(elapsed_ms)

        else:
            errors += 1
            errors_by_origin[(lat, lon)] += 1

            print(
                f"HTTP ERROR | "
                f"status={response.status_code} | "
                f"lat={lat} lon={lon} | "
                f"time={elapsed_ms:.2f} ms"
            )

    except requests.RequestException as exc:
        errors += 1
        errors_by_origin[(lat, lon)] += 1

        print(
            f"REQUEST ERROR | "
            f"lat={lat} lon={lon} | "
            f"{type(exc).__name__}: {exc}"
        )


print("\nOVERALL")

if latencies:
    overall = summarize(latencies)

    for key, value in overall.items():
        print(
            f"{key}: {value:.2f}"
            if isinstance(value, float)
            else f"{key}: {value}"
        )
else:
    overall = {}

print(f"errors: {errors}")
print(
    f"error rate: {(errors / RUNS) * 100:.2f}%"
)


print("\nBY ORIGIN")

origin_results = []

for origin in ORIGINS:
    values = latencies_by_origin[origin]
    origin_errors = errors_by_origin[origin]

    print(
        f"\nOrigin lat={origin[0]} lon={origin[1]}"
    )

    if not values:
        print("No successful requests")
        print(f"errors: {origin_errors}")

        origin_results.append({
            "lat": origin[0],
            "lon": origin[1],
            "stats": {},
            "errors": origin_errors,
            "error_rate": 100.0,
        })

        continue

    stats = summarize(values)

    for key, value in stats.items():
        print(
            f"{key}: {value:.2f}"
            if isinstance(value, float)
            else f"{key}: {value}"
        )

    total_origin_runs = len(values) + origin_errors

    error_rate = (
        origin_errors / total_origin_runs
    ) * 100

    print(f"errors: {origin_errors}")

    print(
        f"error rate: {error_rate:.2f}%"
    )

    origin_results.append({
        "lat": origin[0],
        "lon": origin[1],
        "stats": stats,
        "errors": origin_errors,
        "error_rate": error_rate,
    })


# -----------------------------
# Save benchmark result
# -----------------------------

result = {
    "benchmark": "location_profile_sequential",
    "config": {
        "api_url": API_URL,
        "runs": RUNS,
        "timeout_seconds": TIMEOUT,
        "origins": [
            {
                "lat": lat,
                "lon": lon,
            }
            for lat, lon in ORIGINS
        ],
    },
    "overall": {
        "stats": overall,
        "errors": errors,
        "error_rate": (errors / RUNS) * 100,
    },
    "by_origin": origin_results,
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
        result,
        file,
        indent=2,
        ensure_ascii=False,
    )


print(
    f"\nResult saved to: {RESULTS_FILE}"
)
