# Nearest POI Performance Benchmark

## Scenario

Find the top 10 nearest points within a 2 km radius over a large spatial dataset.

## Benchmark Setup

- Dataset rows: 856991
- Random origins: 100
- CRS for distance calculation: EPSG:32639
- PostgreSQL JIT: disabled

## Results

| Metric | Baseline | Optimized |
|---|---:|---:|
| Min | 143.635 ms | 0.105 ms |
| Mean | 168.966 ms | 0.600 ms |
| p50 | 169.225 ms | 0.558 ms |
| p95 | 190.900 ms | 1.181 ms |
| p99 | 197.937 ms | 1.403 ms |
| Max | 201.895 ms | 1.816 ms |

## Improvement

p95 latency improved by approximately **161.6x**.

## Query Strategy

### Baseline

- `ST_Distance`
- Parallel sequential scan
- Distance calculation across the dataset
- Top-N sort

### Optimized

- `ST_DWithin`
- GiST expression index on `ST_Transform(geom, 32639)`
- KNN `<->` ordering
- Index-driven candidate search
