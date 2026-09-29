import json
import statistics
from pathlib import Path
import os
from sqlalchemy import create_engine, text

from benchmarks.queries import BASELINE_SQL, OPTIMIZED_SQL


DATABASE_URL = os.environ["BENCHMARK_DATABASE_URL"]

engine = create_engine(DATABASE_URL)


RESULTS_DIR = Path("benchmarks/results")
DOCS_DIR = Path("docs")


def percentile(values, p):
    values = sorted(values)

    index = (len(values) - 1) * p

    lower = int(index)

    upper = min(
        lower + 1,
        len(values) - 1,
    )

    fraction = index - lower

    return (
        values[lower] * (1 - fraction)
        + values[upper] * fraction
    )


def run_benchmark(conn, query, origins):
    execution_times = []

    for lon, lat in origins:
        result = conn.execute(
            query,
            {
                "lon": lon,
                "lat": lat,
            },
        ).scalar()

        plan = result[0]

        execution_times.append(
            plan["Execution Time"]
        )

    return {
        "runs": len(execution_times),
        "min": min(execution_times),
        "mean": statistics.mean(execution_times),
        "p50": percentile(execution_times, 0.50),
        "p95": percentile(execution_times, 0.95),
        "p99": percentile(execution_times, 0.99),
        "max": max(execution_times),
    }


with engine.connect() as conn:

    conn.execute(
        text("SET jit = off")
    )

    # تعداد واقعی رکوردها
    dataset_rows = conn.execute(
        text("""
            SELECT COUNT(*)
            FROM customer_addresses
            WHERE geom IS NOT NULL
        """)
    ).scalar_one()

    # 100 مبدا واقعی
    origins = conn.execute(
        text("""
            SELECT
                ST_X(geom) AS lon,
                ST_Y(geom) AS lat
            FROM customer_addresses
            WHERE geom IS NOT NULL
            ORDER BY random()
            LIMIT 100
        """)
    ).all()

    print("Running baseline...")

    baseline = run_benchmark(
        conn,
        BASELINE_SQL,
        origins,
    )

    print("Running optimized...")

    optimized = run_benchmark(
        conn,
        OPTIMIZED_SQL,
        origins,
    )

    conn.execute(
        text("RESET jit")
    )


p95_improvement = (
    baseline["p95"]
    / optimized["p95"]
)


print("\nBASELINE")

for key, value in baseline.items():
    print(f"{key}: {value}")


print("\nOPTIMIZED")

for key, value in optimized.items():
    print(f"{key}: {value}")


print(
    "\nP95 improvement:",
    p95_improvement,
    "x",
)


benchmark_result = {
    "dataset_rows": dataset_rows,
    "origins": len(origins),
    "baseline": baseline,
    "optimized": optimized,
    "p95_improvement": p95_improvement,
}


RESULTS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

DOCS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# JSON
with open(
    RESULTS_DIR / "nearest_benchmark.json",
    "w",
    encoding="utf-8",
) as f:
    json.dump(
        benchmark_result,
        f,
        indent=2,
    )


# Markdown documentation
with open(
    DOCS_DIR / "performance.md",
    "w",
    encoding="utf-8",
) as f:

    f.write(
        "# Nearest POI Performance Benchmark\n\n"
    )

    f.write(
        "## Scenario\n\n"
    )

    f.write(
        "Find the top 10 nearest points within a 2 km radius "
        "over a large spatial dataset.\n\n"
    )

    f.write(
        "## Benchmark Setup\n\n"
    )

    f.write(
        f"- Dataset rows: {dataset_rows}\n"
    )

    f.write(
        f"- Random origins: {len(origins)}\n"
    )

    f.write(
        "- CRS for distance calculation: EPSG:32639\n"
    )

    f.write(
        "- PostgreSQL JIT: disabled\n\n"
    )

    f.write(
        "## Results\n\n"
    )

    f.write(
        "| Metric | Baseline | Optimized |\n"
    )

    f.write(
        "|---|---:|---:|\n"
    )

    f.write(
        f"| Min | {baseline['min']:.3f} ms | "
        f"{optimized['min']:.3f} ms |\n"
    )

    f.write(
        f"| Mean | {baseline['mean']:.3f} ms | "
        f"{optimized['mean']:.3f} ms |\n"
    )

    f.write(
        f"| p50 | {baseline['p50']:.3f} ms | "
        f"{optimized['p50']:.3f} ms |\n"
    )

    f.write(
        f"| p95 | {baseline['p95']:.3f} ms | "
        f"{optimized['p95']:.3f} ms |\n"
    )

    f.write(
        f"| p99 | {baseline['p99']:.3f} ms | "
        f"{optimized['p99']:.3f} ms |\n"
    )

    f.write(
        f"| Max | {baseline['max']:.3f} ms | "
        f"{optimized['max']:.3f} ms |\n"
    )

    f.write(
        "\n## Improvement\n\n"
    )

    f.write(
        "p95 latency improved by approximately "
        f"**{p95_improvement:.1f}x**.\n\n"
    )

    f.write(
        "## Query Strategy\n\n"
    )

    f.write(
        "### Baseline\n\n"
    )

    f.write(
        "- `ST_Distance`\n"
        "- Parallel sequential scan\n"
        "- Distance calculation across the dataset\n"
        "- Top-N sort\n\n"
    )

    f.write(
        "### Optimized\n\n"
    )

    f.write(
        "- `ST_DWithin`\n"
        "- GiST expression index on "
        "`ST_Transform(geom, 32639)`\n"
        "- KNN `<->` ordering\n"
        "- Index-driven candidate search\n"
    )
