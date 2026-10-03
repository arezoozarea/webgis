FROM apache/airflow:3.3.1

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gdal-bin \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow
