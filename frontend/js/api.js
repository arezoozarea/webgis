import { map } from "./map.js";
const API_BASE_URL =
    "http://172.30.240.40:8000";

export async function loadBuffer(
    hospitalId,distance
) {

    const response = await fetch(
        `${API_BASE_URL}/hospital-buffer?hospital_id=${hospitalId}&distance=${distance}`
    );

    const geojson =
        await response.json();
    console.log("buffer geojson",geojson);
    map
        .getSource("buffer-source")
        .setData(geojson);
}

export async function loadNearbyMetros(
    hospitalId
) {

    const response = await fetch(
        `${API_BASE_URL}/nearby-metros?hospital_id=${hospitalId}`
    );

    const geojson =
        await response.json();
    console.log("nearby geojson",geojson);

    map
        .getSource("nearby-metros-source")
        .setData(geojson);
}
export async function loadNeighborhoodStreets(
    neighborhoodId
) {

    const response =
        await fetch(
            `${API_BASE_URL}/neighborhood-streets?neighborhood_id=${neighborhoodId}`
        );

    const geojson =
        await response.json();
    console.log("neighborstreet geojson",geojson);
    map
        .getSource(
            "intersection-source"
        )
        .setData(geojson);
}

export async function  loadNearestMetroAnalysis (
    hospitalId 
) {
    const response = 
        await fetch(
            `${API_BASE_URL}/nearest-metro-analysis?hospital_id=${hospitalId}`
        );
    const geojson = 
        await response.json();

    console.log("nearest geojson",geojson);
    map
        .getSource(
            "nearest-analysis-source"
        )
        .setData(geojson);
}
export async function loadNeighborRestaurants(
    neighborId
)  {
     const response = 
        await fetch(
            `${API_BASE_URL}/neighbor-restaurants?neighbor_id=${neighborId}`
        );
     const geojson = 
        await response.json();
     console.log("insiderestaurant geojson",geojson);
     map
        .getSource(
            "neighbor-restaurants"
         )
         .setData(geojson);
}
export async function loadHospitalsRank(
    
)   {
      const response = 
        await fetch(
            `${API_BASE_URL}/hospitals-rank?`
        );
      const geojson = 
        await response.json();
      console.log("rank geojson",geojson);
      map
        .getSource(
            "hospitals-rank-source"
        )
        .setData(geojson);
}
export async function loadLocationProfile(lat, lon) {
    const params = new URLSearchParams({
        lat: lat.toString(),
        lon: lon.toString()
    });

    const response = await fetch(
        `${API_BASE_URL}/location-profile?${params.toString()}`
    );

    if (!response.ok) {
        const error = await response.json().catch(() => null);

        throw new Error(
            error?.detail || "Failed to load location profile"
        );
    }

    return await response.json();
}

export async function loadRoute(originLat, originLon,destinationLat,destinationLon)
        {
         const params = new URLSearchParams({ origin_lat: originLat.toString(),
          origin_lon: originLon.toString(),
          destination_lat: destinationLat.toString(),
          destination_lon: destinationLon.toString() });

         const response = await fetch(
               `${API_BASE_URL}/routes?${params.toString()}`);
         if (!response.ok) {
            const error = await response.json().catch(() => null)
            throw new Error(
                 error ? error.detail : "Failed to load route"
                );
         }
         return await response.json();
}
