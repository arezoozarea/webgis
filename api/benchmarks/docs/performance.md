# Performance Benchmarks

This document summarizes the performance benchmarks performed on the WebGIS API.

The benchmarks focus on:

- PostGIS spatial query performance
- `/location-profile` endpoint performance
- API behavior under concurrent load
- ETA service performance
- The effect of ETA fan-out on endpoint performance

Raw benchmark results are stored in:

```text
benchmarks/results/
```

---

## 1. Spatial Query Optimization

The nearest-location query was tested against a dataset containing approximately **857,000 geographic points**.

### Baseline

The initial implementation calculated distance using `ST_Distance` and `ST_Transform`.

Without a suitable spatial index for the transformed geometry, PostgreSQL performed a parallel sequential scan over the dataset.

Representative execution time:

**~226 ms**

### Optimization

The query was optimized using:

- `ST_DWithin` for index-supported distance filtering
- PostGIS KNN operator (`<->`) for nearest-neighbor ordering
- A GiST expression index on the transformed geometry

```sql
CREATE INDEX customer_addresses_utm_gist
ON customer_addresses
USING GIST (ST_Transform(geom, 32639));
```

The optimized query uses a GiST Index Scan instead of scanning the entire dataset.

Representative execution time:

**~0.50 ms**

This represents an improvement of approximately **450×** for the measured query.

Repeated benchmark runs also showed sub-millisecond execution for the optimized query in most cases.

Raw results:

```text
benchmarks/results/nearest_benchmark.json
```

---

## 2. Location Profile Endpoint

The `/location-profile` endpoint combines spatial database queries with ETA calculations.

For each request, the endpoint:

1. Finds nearby POIs from several spatial layers.
2. Requests ETA information for the selected POIs.
3. Sorts the POIs based on travel duration.
4. Returns the combined location profile.

The database query itself is fast after spatial optimization, but each profile request can generate multiple external ETA requests.

This fan-out is an important factor in overall endpoint performance.

---

## 3. API Concurrency — 5 POIs per Layer

The endpoint was tested using:

- 100 total requests
- 5 geographic origins
- concurrency levels of 1, 5, 10, and 20
- 5 POIs per spatial layer

All 100 requests completed successfully at every tested concurrency level.

| Concurrency | Mean | P50 | P95 | Max | Throughput |
|---:|---:|---:|---:|---:|---:|
| 1 | 103.95 ms | 102.02 ms | 117.36 ms | 136.25 ms | 9.61 req/s |
| 5 | 189.95 ms | 189.64 ms | 254.04 ms | 268.49 ms | 26.05 req/s |
| 10 | 353.18 ms | 344.23 ms | 479.38 ms | 530.43 ms | **27.71 req/s** |
| 20 | 705.62 ms | 697.81 ms | 986.53 ms | 1209.21 ms | 26.87 req/s |

Throughput increases significantly between concurrency 1 and 5.

From concurrency 5 to 10, throughput increases only slightly:

```text
26.05 → 27.71 req/s
```

Increasing concurrency from 10 to 20 does not improve throughput:

```text
27.71 → 26.87 req/s
```

Meanwhile, p95 latency increases from approximately:

```text
479 ms → 987 ms
```

The results indicate a throughput plateau around the tested concurrency range of **10**. Beyond this range, additional concurrency primarily increases request latency.

Raw results:

```text
benchmarks/results/api_concurrency_5_poi.json
```

---

## 4. API Concurrency — 10 POIs per Layer

The same benchmark was repeated with 10 POIs selected from each spatial layer.

| Concurrency | Mean | P50 | P95 | Max | Throughput |
|---:|---:|---:|---:|---:|---:|
| 1 | 130.67 ms | 127.52 ms | 148.83 ms | 187.30 ms | 7.65 req/s |
| 5 | 372.47 ms | 364.58 ms | 494.16 ms | 580.74 ms | 13.28 req/s |
| 10 | 674.09 ms | 651.28 ms | 1012.13 ms | 1194.58 ms | **14.47 req/s** |
| 20 | 1400.71 ms | 1313.31 ms | 2298.55 ms | 4742.41 ms | 10.73 req/s |

The saturation behavior is more pronounced with the larger POI count.

At concurrency 20:

- mean latency exceeds 1.4 seconds
- p95 latency reaches approximately 2.3 seconds
- maximum latency reaches approximately 4.7 seconds
- throughput decreases to 10.73 req/s

This indicates performance degradation rather than additional throughput at higher concurrency.

Raw results:

```text
benchmarks/results/api_concurrency_10_poi.json
```

---

## 5. Effect of ETA Fan-out

With five spatial layers, increasing the POI limit from 5 to 10 approximately doubles the number of ETA operations required by each profile request.

```text
5 POIs × 5 layers  = 25 ETA calls/profile
10 POIs × 5 layers = 50 ETA calls/profile
```

The effect is particularly visible at concurrency 10:

| Metric | 5 POIs | 10 POIs | Change |
|---|---:|---:|---:|
| ETA calls/profile | 25 | 50 | +100% |
| Throughput | 27.71 req/s | 14.47 req/s | -47.8% |
| Mean latency | 353 ms | 674 ms | +90.9% |
| P95 latency | 479 ms | 1012 ms | +111.2% |

Doubling the ETA fan-out therefore corresponded to approximately:

- **48% lower endpoint throughput**
- **91% higher mean latency**
- **111% higher p95 latency**

This experiment provides strong evidence that ETA fan-out is a major contributor to `/location-profile` performance under concurrent load.

The POI reduction is used here as a diagnostic experiment rather than as a final scaling strategy.

---

## 6. Direct ETA Benchmark
The ETA integration was benchmarked independently from `/location-profile` to determine whether individual ETA requests were responsible for the endpoint bottleneck.

The benchmark used:
- 100 ETA requests
- 5 different routes
- concurrency levels of 1, 5, 10, and 20


| Concurrency | Mean | P50 | P95 | P99 | Max | Throughput |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 22.12 ms | 18.86 ms | 41.02 ms | 70.12 ms | 104.85 ms | 44.96 req/s |
| 5 | 21.03 ms | 16.24 ms | 19.19 ms | 133.28 ms | 135.89 ms | 231.83 req/s |
| 10 | 23.98 ms | 17.39 ms | 28.42 ms | 147.71 ms | 149.55 ms | **398.34 req/s** |
| 20 | 40.24 ms | 17.52 ms | 237.91 ms | 257.80 ms | 258.23 ms | 369.87 req/s |

The ETA service scales effectively up to concurrency 10 in this benchmark.

At concurrency 10, it achieved approximately **398 req/s**, with a p95 latency of approximately **28 ms**.

Increasing concurrency to 20 did not improve throughput:

```text
398.34 → 369.87 req/s

## 7. Sequential API Benchmark

A separate sequential benchmark measures `/location-profile` without concurrent API requests.

It provides a baseline for comparing normal request latency against the concurrent benchmarks.

Raw results:

```text
benchmarks/results/api_benchmark.json
```

---

## 8. Conclusions

The benchmarks highlight three main performance characteristics.

### Spatial queries are no longer the primary bottleneck

Using GiST indexing, `ST_DWithin`, and KNN nearest-neighbor ordering reduced the measured spatial query from approximately **226 ms to 0.50 ms**.

### Endpoint throughput reaches a plateau under concurrent load

With 5 POIs per layer, throughput reaches approximately **27 req/s** around concurrency 10.

Increasing concurrency beyond this point increases latency without increasing throughput.

### ETA fan-out has a significant effect on endpoint performance

Increasing the POI limit from 5 to 10 doubles the approximate number of ETA calls per profile.

At concurrency 10, this reduced throughput from:

```text
27.71 → 14.47 req/s
```

while p95 latency increased from:

```text
479 → 1012 ms
```

The results indicate that future performance improvements should focus primarily on the way ETA operations are composed and executed within `/location-profile`, rather than on further optimization of the nearest-neighbor PostGIS query.
