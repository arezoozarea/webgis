import { map,selectedOrigin,setSelectedOrigin, showOriginMarker } from "./map.js";
import { loadLocationProfile } from "./api.js";
import { initializeLayers, setLocationProfileData,
       showProfileCategory, fitProfileCategory, clearRoute,clearLocationProfileData } from "./layers.js";
import { initializePopups } from "./popup.js";

map.on("load", () => {

    initializeLayers();
    initializePopups();
});



const categoryButtons =
    document.querySelectorAll("[data-category]");

categoryButtons.forEach(button => {
    button.addEventListener("click", () => {
        const category = button.dataset.category;

        clearRoute();

        showProfileCategory(category);

        fitProfileCategory(
            category,
            selectedOrigin
        );

        categoryButtons.forEach(item => {
            item.classList.remove("active");
        });

        button.classList.add("active");
    });
});


map.on("click", async (event) => {
    const clickedProfileFeatures =
        map.queryRenderedFeatures(event.point, {
            layers: [
                "pharmacy-profile-layer",
                "clinic-profile-layer",
                "metro-profile-layer",
                "parking-profile-layer",
                "coffee-profile-layer"
            ]
        });

    // کلیک روی POI نباید مبدا جدید ایجاد کند
    if (clickedProfileFeatures.length > 0) {
        return;
    }

    const lat = event.lngLat.lat;
    const lon = event.lngLat.lng;

    // اول اطلاعات مربوط به مبدا قبلی کاملاً پاک شود
    clearRoute();
    clearLocationProfileData();

    // بعد مبدا جدید ثبت شود
    setSelectedOrigin(lon, lat);
    showOriginMarker(lon, lat);

    // active قبلی دسته‌ها پاک شود
    categoryButtons.forEach(button => {
        button.classList.remove("active");
    });

    const mapHint =
        document.querySelector(".map-hint");

    if (mapHint) {
        mapHint.style.display = "none";
    }

    try {
        const profile =
            await loadLocationProfile(
                lat,
                lon
            );

        setLocationProfileData(profile);

    } catch (error) {
        console.error(
            "Failed to load location profile:",
            error
        );
    }
});
