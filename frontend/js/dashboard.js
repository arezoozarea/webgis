export function updateHospitalDashboard(props) {
    document.getElementById("dashboard-empty").classList.add("hidden");
    document.getElementById("dashboard-content").classList.remove("hidden");

    setText("hospital-name", props.hospital_name);
    setText("hospital-score", props.final_score);
    setText("hospital-rank", props.rank);

    setText("nearest-metro", props.nearest_metro_name);
    setText("metro-distance", formatMeters(props.nearest_metro_distance));
    setText("metro-score", props.nearest_metro_score);

    setText("nearest-parking", props.nearest_parking_name);
    setText("parking-distance", formatMeters(props.nearest_parking_distance));

    setText("taxi-distance", formatMeters(props.nearest_taxi_distance));
}

function setText(id, value) {
    const element =
        document.getElementById(id);

    if (!element) {
        console.warn(`Missing element: ${id}`);
        return;
    }

    element.textContent =
        value ?? "-";
}

function formatMeters(value) {
    if (value === null || value === undefined) {
        return "-";
    }

    return `${Math.round(Number(value))} متر`;
}
