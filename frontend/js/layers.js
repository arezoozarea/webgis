import { map } from "./map.js";

let currentProfile = null;
const PROFILE_LAYERS = {
    pharmacy: {
        sourceId: "pharmacy-profile-source",
        layerId: "pharmacy-profile-layer",
        color: "#E53935"
    },

    clinic: {
        sourceId: "clinic-profile-source",
        layerId: "clinic-profile-layer",
        color: "#8E24AA"
    },

    metro: {
        sourceId: "metro-profile-source",
        layerId: "metro-profile-layer",
        color: "#1E88E5"
    },
    parking: {
          sourceId: "parking-profile-source",
          layerId: "parking-profile-layer",
          color: "#FB8C00"
    },
    coffee:  {
        sourceId: "coffee-profile-source",
        layerId: "coffee-profile-layer",
        color: "#6D4C41"
    }
};


function createEmptyFeatureCollection() {
    return {
        type: "FeatureCollection",
        features: []
    };
}



export function initializeLayers() {
    initializeRouteLayer();
    initializeProfileLayers();
}


export function initializeProfileLayers() {
    initializeProfileLabelBackground();

    for (const config of Object.values(PROFILE_LAYERS)) {

        // -------------------------
        // Source
        // -------------------------

        if (!map.getSource(config.sourceId)) {
            map.addSource(config.sourceId, {
                type: "geojson",

                data: {
                    type: "FeatureCollection",
                    features: []
                }
            });
        }


        // -------------------------
        // Point
        // -------------------------

        if (!map.getLayer(config.layerId)) {
            map.addLayer({
                id: config.layerId,

                type: "circle",

                source: config.sourceId,

                layout: {
                    visibility: "none"
                },

                paint: {
                    "circle-radius": [
                        "interpolate",
                        ["linear"],
                        ["zoom"],

                        10, 5,
                        13, 6,
                        16, 7
                    ],

                    "circle-color": config.color,

                    "circle-stroke-color": "#ffffff",

                    "circle-stroke-width": 2,

                    "circle-opacity": 0.95
                }
            });
            map.addLayer({
                        id: `${config.layerId}-label`,

                          type: "symbol",

                          source: config.sourceId,

                          layout: {
                          visibility: "none",
                          "icon-image": "profile-label-bg",

                          "icon-size": 1,

                          "icon-anchor": "bottom",

                          "icon-offset": [
                                           0,
                                           -7
                                              ],

                           "icon-allow-overlap": false,
                           "icon-ignore-placement":false,

                           "text-field": ["get", "labelText"],

                           "text-size": 9,
                           "text-line-height":1.1,

                           "text-anchor": "bottom",

                           "text-offset": [0, -1.05],

                           "text-allow-overlap": true,
                           "text-ignore-placement": true,
                           "symbol-avoid-edges": false
                          },

                          paint: {
                                   "text-color": "#344054",

                                   "text-halo-color": "#ffffff",

                                   "text-halo-width": 2
                                   }
             });
  }
 }
}



function initializeRouteLayer() {
    map.addSource("route-source", {
        type: "geojson",
        data: {
            type: "Feature",
            properties: {},
            geometry: {
                type: "LineString",
                coordinates: []
            }
        }
    });

    map.addLayer({
        id: "route-layer",
        type: "line",
        source: "route-source",

        layout: {
            "line-join": "round",
            "line-cap": "round"
        },

        paint: {
            "line-color": "#2563eb",
            "line-width": ["interpolate",["linear"],["zoom"],
              10,3,
              14,5,
              17,7
             ],
            "line-opacity": 0.95
        }
    });
}

function profileItemsToGeoJson(items) {
    return {
        type: "FeatureCollection",

        features: items.map(item => {
            const distance =
                item.eta?.distance != null
                    ? Number(item.eta.distance)
                    : null;

            const duration =
                item.eta?.duration != null
                    ? Number(item.eta.duration)
                    : null;

            const durationText =
                duration != null
                    ? `${duration} min`
                    : "-";

            let distanceText = "-";

            if (distance != null) {
                distanceText =
                    distance >= 1000
                        ? `${(distance / 1000).toFixed(1)} km`
                        : `${Math.round(distance)} m`;
            }

            return {
                type: "Feature",

                geometry: {
                    type: "Point",
                    coordinates: [
                        Number(item.poi.lon),
                        Number(item.poi.lat)
                    ]
                },

                properties: {
                    poiId: item.poi.id,
                    poiName: item.poi.name,
                    distance,
                    duration,

                    // دو ردیف
                    labelText:
                        `${durationText}\n${distanceText}`
                }
            };
        })
    };
}


export function setLocationProfileData(profile) {
    currentProfile = profile;

    for (
        const [category, items]
        of Object.entries(profile)
    ) {
        const config =
            PROFILE_LAYERS[category];

        if (!config) {
            continue;
        }

        const source =
            map.getSource(config.sourceId);

        if (!source) {
            continue;
        }

        source.setData(
            profileItemsToGeoJson(items)
        );
    }
}
  

function initializeProfileLabelBackground() {
    if (map.hasImage("profile-label-bg")) {
        return;
    }

    const width = 62;
    const height = 32;

    const canvas = document.createElement("canvas");

    canvas.width = width;
    canvas.height = height;

    const ctx = canvas.getContext("2d");

    const radius = 7;

    ctx.beginPath();

    ctx.roundRect(
        1,
        1,
        width - 2,
        height - 2,
        radius
    );

    ctx.fillStyle = "rgba(255,255,255,0.96)";
    ctx.fill();

    ctx.strokeStyle = "#d8dee8";
    ctx.lineWidth = 1;
    ctx.stroke();

    map.addImage(
        "profile-label-bg",
        ctx.getImageData(
            0,
            0,
            width,
            height
        )
    );
}

export function clearLocationProfileData() {
    currentProfile = null;

    for (const config of Object.values(PROFILE_LAYERS)) {
        const source = map.getSource(config.sourceId);

        if (source) {
            source.setData({
                type: "FeatureCollection",
                features: []
            });
        }

        if (map.getLayer(config.layerId)) {
            map.setLayoutProperty(
                config.layerId,
                "visibility",
                "none"
            );
        }

        const labelLayerId = `${config.layerId}-label`;

        if (map.getLayer(labelLayerId)) {
            map.setLayoutProperty(
                labelLayerId,
                "visibility",
                "none"
            );
        }
    }
}

export function setRouteData(routeGeoJson) {
    const source = map.getSource("route-source");

    if (!source) {
        console.warn("route-source not found");
        return;
    }

    source.setData(routeGeoJson);
}


export function clearRoute() {
    setRouteData({
        type: "Feature",
        properties: {},
        geometry: {
            type: "LineString",
            coordinates: []
        }
    });
}

export function showProfileCategory(selectedCategory) {
    for (
        const [category, config]
        of Object.entries(PROFILE_LAYERS)
    ) {
        const visibility =
            category === selectedCategory
                ? "visible"
                : "none";

        // نقاط
        if (map.getLayer(config.layerId)) {
            map.setLayoutProperty(
                config.layerId,
                "visibility",
                visibility
            );
        }

        // Label همان نقاط
        const labelLayerId =
            `${config.layerId}-label`;

        if (map.getLayer(labelLayerId)) {
            map.setLayoutProperty(
                labelLayerId,
                "visibility",
                visibility
            );
        }
    }
}

export function fitProfileCategory(
    category,
    origin = null
) {
    if (!currentProfile) {
        return;
    }

    const items = currentProfile[category];

    if (!items || items.length === 0) {
        return;
    }

    const bounds =
        new maplibregl.LngLatBounds();

    // مبدا
    if (origin) {
        bounds.extend([
            Number(origin.lng),
            Number(origin.lat)
        ]);
    }

    // تمام نقاط دسته
    items.forEach(item => {
        bounds.extend([
            Number(item.poi.lon),
            Number(item.poi.lat)
        ]);
    });

    map.fitBounds(bounds, {
        padding: {
            top: 60,
            bottom: 60,
            left: 60,
            right: 60
        },

        maxZoom: 15,
        duration:0
    });
}



function initializeTileLayers() {

    map.addSource("hospitals", {
        type: "vector",
        tiles: [
            "http://172.30.240.40:7800/public.hospitals/{z}/{x}/{y}.pbf"
        ]
    });

    map.addLayer({
        id: "hospitals",
        type: "circle",
        source: "hospitals",
        "source-layer": "public.hospitals",
        paint: {
            "circle-radius": 6,
            "circle-color": "#ff0000"
        }
    });

    map.addSource("metros", {
        type: "vector",
        tiles: [
            "http://172.30.240.40:7800/public.metro_stations/{z}/{x}/{y}.pbf"
        ]
    });

    map.addLayer({
        id: "metros",
        type: "circle",
        source: "metros",
        "source-layer": "public.metro_stations",
        paint: {
            "circle-radius": 6,
            "circle-color": "#0000ff"
        }
    });
}




function initializeAnalysisLayers() {

    map.addSource("buffer-source", {
        type: "geojson",
        data: {
            type: "FeatureCollection",
            features: []
        }
    });

    map.addLayer({
        id: "buffer-layer",
        type: "fill",
        source: "buffer-source",
        paint: {
            "fill-color": "#0080ff",
            "fill-opacity": 0.25
        }
    });

    map.addSource(
    "intersection-source",
    {
        type: "geojson",
        data: {
            type: "FeatureCollection",
            features: []
        }
    });
    map.addLayer({
        id: "intersection-layer",
        type: "line",
        source: "intersection-source",
        paint: {
        "line-width": 4,
        "line-color": "#ffff00"
        }
    });
    map.addSource(
    "neighbor-restaurants",
    {
        type:"geojson",
        data: {
            type: "FeatureCollection",
            features: []
        }
    });
    map.addLayer({
        id: "within-restaurant-layer",
        type: "circle",
        source: "neighbor-restaurants",
        paint: {
        "circle-radius": 8,
        "circle-color": "#ff0000",
        "circle-stroke-width": 2,
        "circle-stroke-color": "#ffffff" 
        }
    });
    map.addSource(
    "hospitals-rank-source",
    {
        type:"geojson",
        data:{
            type:"FeatureCollection",
            features:[]
        }
    });
    map.addLayer({
        id:"hospitals-rank-layer",
        type: "circle",
        source: "hospitals-rank-source",
        paint: {"circle-radius": [
            "interpolate",
            ["linear"],
            ["get", "final_score"],
            0, 4,
            25, 7,
            50, 10,
            75, 14,
            100, 20
        ],
        "circle-color": [
            "interpolate",
            ["linear"],
            ["get", "final_score"],
            0, "#d7191c",
            50, "#fdae61",
            100, "#1a9641"
        ],
        "circle-opacity": 0.8,
        "circle-stroke-width": 1.5,
        "circle-stroke-color": "#ffffff"
     }
    });
    map.addSource(
    "nearest-analysis-source",
    {
        type: "geojson",
        data: {
            type:"FeatureCollection",
            features: []
        }
    });
    
    map.addLayer({
        id: "nearest-link-layer",
        type: "line",
        source:"nearest-analysis-source",
        filter:["==",["get", "feature_type"], "link"],
        paint:{
        "line-width": 3,
        "line-color": "#ffff00"
              }
    });
    map.addLayer({
        id: "nearest-hospital-layer",
        type: "circle",
        source:"nearest-analysis-source",
        filter: ["==",["get", "feature_type"],"hospital"],
        paint: {
        "circle-radius": 8,
        "circle-color": "#ff0000",
        "circle-stroke-width": 2,
        "circle-stroke-color": "#ffffff"
                }
    });
    map.addLayer({
        id: "nearest-metro-layer",
        type: "circle",
        source: "nearest-analysis-source",
        filter: ["==", ["get", "feature_type"], "metro"],
        paint: {
        "circle-radius": 8,
        "circle-color": "#0066ff",
        "circle-stroke-width": 2,
        "circle-stroke-color": "#ffffff"
        }
    });
}


