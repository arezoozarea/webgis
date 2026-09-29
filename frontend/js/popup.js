import {
    map,
    selectedOrigin,
    routeToGeoJson
} from "./map.js";

import {
    loadRoute
} from "./api.js";

import {
    setRouteData
} from "./layers.js";


let activePopup = null;

const PROFILE_LAYER_IDS = [
    "pharmacy-profile-layer",
    "clinic-profile-layer",
    "metro-profile-layer",
    "parking-profile-layer",
    "coffee-profile-layer"
];


function formatDuration(value) {
    if (value === null || value === undefined) {
        return "نامشخص";
    }

    return `${value} دقیقه`;
}


function formatDistance(value) {
    if (value === null || value === undefined) {
        return "نامشخص";
    }

    if (value >= 1000) {
        return `${(value / 1000).toFixed(1)} کیلومتر`;
    }

    return `${Math.round(value)} متر`;
}


function fitMapToRoute(routeGeoJson) {
    const coordinates =
        routeGeoJson &&
        routeGeoJson.geometry &&
        routeGeoJson.geometry.coordinates;

    if (
        !Array.isArray(coordinates) ||
        coordinates.length === 0
    ) {
        return;
    }

    const bounds =
        new maplibregl.LngLatBounds();

    coordinates.forEach(coordinate => {
        bounds.extend(coordinate);
    });

    map.fitBounds(bounds, {
        padding: {
            top: 45,
            bottom: 45,
            left: 45,
            right: 45
        },
        maxZoom: 16,
        duration: 900
    });
}


function createPopupContent(
    props,
    destinationLat,
    destinationLon
) {
    const container =
        document.createElement("div");

    container.className = "poi-popup";

    const durationText =
        formatDuration(props.duration);

    const distanceText =
        formatDistance(props.distance);

    container.innerHTML = `
        <div class="poi-popup__title">
            ${props.poiName || "بدون نام"}
        </div>

        <div class="poi-popup__metrics">

            <div class="poi-popup__metric">
                <span>زمان</span>
                <strong>${durationText}</strong>
            </div>

            <div class="poi-popup__metric">
                <span>فاصله</span>
                <strong>${distanceText}</strong>
            </div>

        </div>

        <button
            type="button"
            class="poi-popup__route-button"
        >
            نمایش مسیر
        </button>

        <div
            class="poi-popup__message"
            aria-live="polite"
        ></div>
    `;

    const routeButton =
        container.querySelector(
            ".poi-popup__route-button"
        );

    const messageElement =
        container.querySelector(
            ".poi-popup__message"
        );

    routeButton.addEventListener(
        "click",
        async () => {
            if (!selectedOrigin) {
                messageElement.textContent =
                    "ابتدا مبدا را انتخاب کنید.";

                return;
            }

            routeButton.disabled = true;
            routeButton.textContent =
                "در حال دریافت...";

            messageElement.textContent = "";

            try {
                const route = await loadRoute(
                    selectedOrigin.lat,
                    selectedOrigin.lng,
                    destinationLat,
                    destinationLon
                );

                if (
                    !route ||
                    !Array.isArray(route.polylines) ||
                    route.polylines.length === 0
                ) {
                    throw new Error(
                        "Route polyline is empty"
                    );
                }

                const routeGeoJson =
                    routeToGeoJson(
                        route.polylines
                    );

                setRouteData(routeGeoJson);

                if (activePopup) {
                    activePopup.remove();
                    activePopup = null;
                }

                fitMapToRoute(routeGeoJson);

            } catch (error) {
                console.error(
                    "Failed to load route:",
                    error
                );

                routeButton.disabled = false;
                routeButton.textContent =
                    "تلاش مجدد";

                messageElement.textContent =
                    "دریافت مسیر با خطا مواجه شد.";
            }
        }
    );

    return container;
}


function registerLayerPopup(layerId) {
    map.on("mouseenter", layerId, () => {
        map.getCanvas().style.cursor =
            "pointer";
    });

    map.on("mouseleave", layerId, () => {
        map.getCanvas().style.cursor = "default";
    });

    map.on(
        "click",
        layerId,
        event => {
            const feature =
                event.features &&
                event.features[0];

            if (!feature) {
                return;
            }

            const props =
                feature.properties || {};

            const coordinates =
                feature.geometry &&
                feature.geometry.coordinates;

            if (
                !Array.isArray(coordinates) ||
                coordinates.length < 2
            ) {
                console.error(
                    "POI coordinates are invalid"
                );

                return;
            }

            const destinationLon =
                Number(coordinates[0]);

            const destinationLat =
                Number(coordinates[1]);

            if (
                !Number.isFinite(destinationLon) ||
                !Number.isFinite(destinationLat)
            ) {
                console.error(
                    "POI coordinates are invalid"
                );

                return;
            }

            if (activePopup) {
                activePopup.remove();
            }

            const popupContent =
                createPopupContent(
                    props,
                    destinationLat,
                    destinationLon
                );

            activePopup =
                new maplibregl.Popup({
                    closeButton: true,
                    closeOnClick: false,
                    offset: 8,
                    maxWidth: "170px"
                })
                    .setLngLat([
                        destinationLon,
                        destinationLat
                    ])
                    .setDOMContent(
                        popupContent
                    )
                    .addTo(map);
        }
    );
}


export function initializePopups() {
    for (
        const layerId
        of PROFILE_LAYER_IDS
    ) {
        if (!map.getLayer(layerId)) {
            console.warn(
                `Popup layer not found: ${layerId}`
            );

            continue;
        }

        registerLayerPopup(layerId);
    }
}

