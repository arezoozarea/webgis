export const map = new maplibregl.Map({
    container: "map",

    center: [51.399, 35.701],
    zoom: 11,

    style: {
        version: 8,

        glyphs:
            "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",

        sources: {
            base: {
                type: "raster",

                tiles: [
                    "https://a.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png"
                ],

                tileSize: 256
            }
        },

        layers: [
            {
                id: "base",
                type: "raster",
                source: "base"
            }
        ]
    }
});


export let selectedOrigin = null;

export function setSelectedOrigin(lng, lat) {
    selectedOrigin = {
        lng,
        lat
    };
}

let originMarker = null;

export function showOriginMarker(lng, lat) {
    if (originMarker) {
        originMarker.setLngLat([lng, lat]);
        return;
    }

    originMarker = new maplibregl.Marker()
        .setLngLat([lng, lat])
        .addTo(map);
}


export function routeToGeoJson(polylines) {
    const coordinates = polylines.flatMap(encoded =>
        polyline.decode(encoded).map(([lat, lon]) => [lon, lat])
    );

    return {
        type: "Feature",
        properties: {},
        geometry: {
            type: "LineString",
            coordinates
        }
    };
}
