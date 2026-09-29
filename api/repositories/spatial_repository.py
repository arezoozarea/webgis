from sqlalchemy import text

from db import engine


class SpatialRepository:
    @staticmethod
    def get_nearby_metros(hospital_id: int, distance: int):

        sql = text(
            """ 
        WITH target_hospital AS (
            SELECT
                id,
                full_name,
                geom
            FROM public.hospitals
            WHERE id = :hospital_id
        )
        SELECT
            json_build_object(
                'type', 'FeatureCollection',
                'features',
                json_agg(
                    json_build_object(
                        'type', 'Feature',
                        'geometry', ST_AsGeoJSON(m.geom)::json,
                        'properties', json_build_object(
                            'hospital_id', h.id,
                            'hospital_name', h.full_name,
                            'metro_id', m.id,
                            'metro_name', m.full_name,
                            'distance',
                            ST_Distance(
                                m.geom::geography,
                                h.geom::geography
                            )
                        )
                    )
                )
            ) AS geojson
        FROM public.metro_stations m
        CROSS JOIN target_hospital h
        WHERE ST_DWithin(
            m.geom::geography,
            h.geom::geography,
            :distance
        )"""
        )

        with engine.connect() as conn:
            result = conn.execute(
                sql, {"hospital_id": hospital_id, "distance": distance}
            )
            row = result.fetchone()
            return row.geojson
    @staticmethod
    def get_neighborhood_streets(neighborhood_id: int):
        sql= text(
           """ WITH target_neighborhood AS (
            SELECT
                id,
                name,
                wkb_geometry
            FROM public.tehran_sublocals
            WHERE id = :neighborhood_id
        )

        SELECT
            json_build_object(
                'type', 'FeatureCollection',
                'features',
                json_agg(
                    json_build_object(
                        'type', 'Feature',
                        'geometry',
                        ST_AsGeoJSON(s.wkb_geometry)::json,
                        'properties',
                        json_build_object(
                            'street_id', s.id,
                            'street_name', s.name
                        )
                    )
                )
            ) AS geojson
        FROM public.tehran_streets s
        JOIN target_neighborhood n
            ON ST_Intersects(
                s.wkb_geometry,
                n.wkb_geometry
            );
                   """)
        with engine.connect() as conn:
            result = conn.execute(
                sql, {"neighborhood_id": neighborhood_id}
            )

            row = result.fetchone()

            return row.geojson
    @staticmethod
    def get_neighbor_restaurants(neighbor_id: int):
        sql= text(
            """
            WITH
	target_neighborhoods AS (
		SELECT
			id,
			name,
			wkb_geometry
		FROM public.tehran_sublocals where id= :neighbor_id)
        
        SELECT json_build_object(
		'type',
		'FeatureCollection',
		'features',
		json_agg(
			json_build_object(
				'type',
				'Feature',
				'geometry',
				st_asgeojson (r.geom)::JSON,
				'properties',
				json_build_object(
					'neighborhood_id',
					t.id,
					'neighborhood_name',
					t.name,
					'restaurant_id',
					r.id,
					'restaurant_name',
					r.name
				)
			)
		)) AS geojson
		FROM
			target_neighborhoods t
			JOIN public.tehran_restaurant r on ST_Within(r.geom,t.wkb_geometry)
        """)
        with engine.connect() as conn:
            result = conn.execute(sql,{"neighbor_id":neighbor_id})
            row  = result.fetchone()
            return row.geojson
    @staticmethod
    def nearest_metro_analysis(hospital_id: int):
        sql= text("""WITH
	nearest AS (
		SELECT
			h.id AS hospital_id,
			h.full_name AS hospital_name,
			h.geom AS hospital_geom,
			m.id AS metro_id,
			m.name AS metro_name,
			m.geom AS metro_geom,
			ST_Distance (h.geom::geography, m.geom::geography) AS distance
		FROM
			public.hospitals h
			CROSS JOIN LATERAL (
				SELECT
					id,
					name,
					geom
				FROM
					public.metro_stations
				ORDER BY
					geom <-> h.geom
				LIMIT 1
			) m
		WHERE h.id = :hospital_id
	),
	features AS (
		SELECT
			json_build_object(
				'type',
				'Feature',
				'geometry',
				ST_ASGeoJSON (hospital_geom)::JSON,
				'properties',
				json_build_object(
					'feature_type',
					'hospital',
					'hospital_id',
					hospital_id,
					'distance',
					distance
				)
			) AS feature
		FROM nearest
		UNION ALL
		SELECT
			json_build_object(
				'type',
				'Feature',
				'geometry',
				ST_ASGeoJSON (metro_geom)::JSON,
				'properties',json_build_object(
				'feature_type',
				'metro',
				'metro_id',
				metro_id,
				'metro_name',
				metro_name,
				'distance',
				distance)
			) AS feature
		FROM nearest
		UNION ALL
		SELECT
			json_build_object(
				'type',
				'Feature',
				'geometry',
				ST_ASGeoJSON (st_makeline (hospital_geom, metro_geom))::JSON,
				'properties',
				json_build_object(
					'feature_type',
					'link',
					'hospital_id',
					hospital_id,
					'hospital_name',
					hospital_name,
					'metro_id',
					metro_id,
					'metro_name',
					metro_name,
					'distance',
					distance
				)
			) AS feature
		FROM nearest
	)
        SELECT
	json_build_object(
		'type',
		'FeatureCollection',
		'features',
		COALESCE(json_agg(feature), '[]'::json)
	) AS geojson
        FROM
	features
            """)
        with engine.connect() as conn:

            result = conn.execute(
                sql, {"hospital_id": hospital_id})

            row = result.fetchone()

            return row.geojson 
    @staticmethod
    def hospitals_rank():
        sql= text("""WITH
        nearest_metro AS (
        SELECT
        h.id AS hospital_id,
        m.id AS nearest_metro_id,
        m.full_name AS nearest_metro_name,
        ST_Distance(m.geom::geography, h.geom::geography) AS nearest_metro_distance
        FROM public.hospitals h
        CROSS JOIN LATERAL (
        SELECT
            id,
            full_name,
            geom
        FROM public.metro_stations
        ORDER BY geom <-> h.geom
        LIMIT 1
        ) m
      ),

        nearest_parking AS (
        SELECT
        h.id AS hospital_id,
        p.id AS nearest_parking_id,
        p.name AS nearest_parking_name,
        ST_Distance(p.geom::geography, h.geom::geography) AS nearest_parking_distance
        FROM public.hospitals h
        CROSS JOIN LATERAL (
        SELECT
            id,
            name,
            geom
        FROM public.parkings
        ORDER BY geom <-> h.geom
        LIMIT 1
        ) p
    ),

        nearest_taxi AS (
        SELECT
        h.id AS hospital_id,
        t.id AS nearest_taxi_id,
        t.name AS nearest_taxi_name,
        ST_Distance(t.geom::geography, h.geom::geography) AS nearest_taxi_distance
        FROM public.hospitals h
        CROSS JOIN LATERAL (
        SELECT
            id,
            name,
            geom
        FROM public.taxi_stations
        ORDER BY geom <-> h.geom
        LIMIT 1
        ) t
    ),

        scored AS (
        SELECT
        h.id AS hospital_id,
        h.name AS hospital_name,
        h.geom AS hospital_geom,

        m.nearest_metro_id,
        m.nearest_metro_name,
        m.nearest_metro_distance,

        p.nearest_parking_id,
        p.nearest_parking_name,
        p.nearest_parking_distance,

        t.nearest_taxi_id,
        t.nearest_taxi_name,
        t.nearest_taxi_distance,

        CASE
            WHEN m.nearest_metro_distance <= 300 THEN 100
            WHEN m.nearest_metro_distance <= 500 THEN 80
            WHEN m.nearest_metro_distance <= 1000 THEN 50
            WHEN m.nearest_metro_distance <= 2000 THEN 20
            ELSE 0
        END AS nearest_metro_score,

        CASE
            WHEN p.nearest_parking_distance <= 300 THEN 100
            WHEN p.nearest_parking_distance <= 500 THEN 80
            WHEN p.nearest_parking_distance <= 1000 THEN 50
            WHEN p.nearest_parking_distance <= 2000 THEN 20
            ELSE 0
        END AS nearest_parking_score,

        CASE
            WHEN t.nearest_taxi_distance <= 100 THEN 100
            WHEN t.nearest_taxi_distance <= 200 THEN 80
            WHEN t.nearest_taxi_distance <= 500 THEN 50
            WHEN t.nearest_taxi_distance <= 1000 THEN 20
            ELSE 0
        END AS nearest_taxi_score

        FROM public.hospitals h
        LEFT JOIN nearest_metro m
        ON h.id = m.hospital_id
        LEFT JOIN nearest_parking p
        ON h.id = p.hospital_id
        LEFT JOIN nearest_taxi t
        ON h.id = t.hospital_id
    ),

        ranked AS (
        SELECT
        *,
        ROUND(
            (
                nearest_metro_score * 0.45
                + nearest_parking_score * 0.35
                + nearest_taxi_score * 0.20
            )::numeric,
            2
        ) AS final_score,

        DENSE_RANK() OVER (
            ORDER BY
                (
                    nearest_metro_score * 0.45
                    + nearest_parking_score * 0.35
                    + nearest_taxi_score * 0.20
                ) DESC
        ) AS rank
        FROM scored
    )

        SELECT
        json_build_object(
        'type', 'FeatureCollection',
        'features',
        COALESCE(
            json_agg(
                json_build_object(
                    'type', 'Feature',
                    'geometry', ST_AsGeoJSON(hospital_geom)::json,
                    'properties', json_build_object(
                        'hospital_id', hospital_id,
                        'hospital_name', hospital_name,

                        'nearest_metro_id', nearest_metro_id,
                        'nearest_metro_name', nearest_metro_name,
                        'nearest_metro_distance', nearest_metro_distance,
                        'nearest_metro_score', nearest_metro_score,

                        'nearest_parking_id', nearest_parking_id,
                        'nearest_parking_name', nearest_parking_name,
                        'nearest_parking_distance', nearest_parking_distance,
                        'nearest_parking_score', nearest_parking_score,

                        'nearest_taxi_id', nearest_taxi_id,
                        'nearest_taxi_name', nearest_taxi_name,
                        'nearest_taxi_distance', nearest_taxi_distance,
                        'nearest_taxi_score', nearest_taxi_score,

                        'final_score', final_score,
                        'rank', rank
                    )
                )
                ORDER BY rank
            ),
            '[]'::json
        )
        ) AS geojson
        FROM ranked;
        """)
        with engine.connect() as conn:
            result= conn.execute(sql)
            row = result.fetchone()
            return row.geojson

    @staticmethod
    def get_hospital_buffer(hospital_id: int, distance: int):

        sql = text(
            """
            SELECT json_build_object(
                'type', 'FeatureCollection',
                'features', json_agg(

                    json_build_object(
                        'type', 'Feature',

                        'geometry',
                        ST_AsGeoJSON(

                            ST_Buffer(
                                geom::geography,
                                :distance
                            )::geometry

                        )::json,

                        'properties',
                        json_build_object(
                            'hospital_id', id,
                            'distance', :distance
                        )
                    )
                )
            ) AS geojson

            FROM public.hospitals
            WHERE id = :hospital_id
        """
        )

        with engine.connect() as conn:

            result = conn.execute(
                sql, {"hospital_id": hospital_id, "distance": distance}
            )

            row = result.fetchone()

            return row.geojson
