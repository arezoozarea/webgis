import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
from services.SpatialProfileService.EtaService import get_eta


TOTAL_REQUESTS = 100
CONCURRENCY_LEVELS = [1, 5, 10, 20]
RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_FILE = RESULTS_DIR / "eta_benchmark.json"
# start_lat, start_lon, end_lat, end_lon
ROUTES = [
    (35.70, 51.40, 35.72, 51.42),
    (35.72, 51.42, 35.74, 51.38),
    (35.74, 51.38, 35.69, 51.44),
    (35.69, 51.44, 35.76, 51.41),
    (35.76, 51.41, 35.70, 51.40),
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


def send_eta_request(route):
    start_lat, start_lon, end_lat, end_lon = route

    start = time.perf_counter()

    try:
        result = get_eta(
            start_lat=start_lat,
            start_lon=start_lon,
            end_lat=end_lat,
            end_lon=end_lon,
        )

        elapsed_ms = (
            time.perf_counter() - start
        ) * 1000

        if result is None:
            return None, "ETA returned None"

        return elapsed_ms, None

    except Exception as exc:
        elapsed_ms = (
            time.perf_counter() - start
        ) * 1000

        return None, f"{type(exc).__name__}: {exc}"


def run_benchmark(concurrency):
    times = []
    errors = []

    benchmark_start = time.perf_counter()

    with ThreadPoolExecutor(
        max_workers=concurrency
    ) as executor:

        futures = []

        for i in range(TOTAL_REQUESTS):

            route = ROUTES[i % len(ROUTES)]

            future = executor.submit(
                send_eta_request,
                route,
            )

            futures.append(future)

        for future in as_completed(futures):

            elapsed_ms, error = future.result()

            if error:
                errors.append(error)
            else:
                times.append(elapsed_ms)

    total_seconds = (
        time.perf_counter() - benchmark_start
    )

    print()
    print(f"CONCURRENCY {concurrency}")
    print()

    print(f"runs: {TOTAL_REQUESTS}")
    print(f"success: {len(times)}")
    print(f"errors: {len(errors)}")
    print()

    if times:
        print(f"min: {min(times):.2f} ms")
        print(f"mean: {statistics.mean(times):.2f} ms")
        print(f"p50: {percentile(times, 0.50):.2f} ms")
        print(f"p95: {percentile(times, 0.95):.2f} ms")
        print(f"p99: {percentile(times, 0.99):.2f} ms")
        print(f"max: {max(times):.2f} ms")

    print()

    throughput = TOTAL_REQUESTS / total_seconds

    print(
        f"throughput: {throughput:.2f} req/s"
    )

    print(
        f"total time: {total_seconds:.2f} s"
    )

    if errors:
        print()
        print("ERRORS:")

        for error in errors[:10]:
            print(error)
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
        "throughput": throughput,
        "total_time": total_seconds,
    }


def main():

    benchmark_results = []

    for concurrency in CONCURRENCY_LEVELS:

        print(
            f"\nrunning concurrency: "
            f"{concurrency}..."
        )

        result = run_benchmark(concurrency)

        benchmark_results.append(result)

    output = {
        "benchmark": "eta_concurrency",
        "config": {
            "total_requests": TOTAL_REQUESTS,
            "concurrency_levels": CONCURRENCY_LEVELS,
            "routes": [
                {
                    "start_lat": start_lat,
                    "start_lon": start_lon,
                    "end_lat": end_lat,
                    "end_lon": end_lon,
                }
                for (
                    start_lat,
                    start_lon,
                    end_lat,
                    end_lon,
                ) in ROUTES
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

    print(
        f"\nResult saved to: {RESULTS_FILE}"
    )

if __name__ == "__main__":
    main()
