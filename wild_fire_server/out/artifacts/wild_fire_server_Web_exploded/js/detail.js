/**
 * This is the main entry point for all JavaScript on the page.
 * It waits for the HTML document to be fully loaded and parsed.
 */
document.addEventListener("DOMContentLoaded", () => {
    setupHamburgerMenu();
    setupHeaderScroll();
    kakao.maps.load(initMap);
});

// Global variables to store the initial prediction data for reactive updates
let currentPredictionData = null;
let currentPredictionCenter = null;
let currentFirePolygon = null;
let currentInfoOverlay = null;
let currentWindArrowOverlay = null; // New global variable for the wind direction arrow
let abortController = null; // New global variable for AbortController
let clickMarker = null; // Moved to global scope

// Approximate coordinates for regions (for map centering)
const regionCoordinates = {
    "춘천시": { lat: 37.8813, lng: 127.7298 },
    "원주시": { lat: 37.3422, lng: 127.9200 },
    "강릉시": { lat: 37.7519, lng: 128.8762 },
    "동해시": { lat: 37.5236, lng: 129.1167 },
    "태백시": { lat: 37.1636, lng: 128.9850 },
    "속초시": { lat: 38.2000, lng: 128.5917 },
    "삼척시": { lat: 37.4486, lng: 129.1642 },
    "홍천군": { lat: 37.8850, lng: 127.8900 },
    "횡성군": { lat: 37.4922, lng: 128.1950 },
    "영월군": { lat: 37.1850, lng: 128.4680 },
    "평창군": { lat: 37.3722, lng: 128.3950 },
    "정선군": { lat: 37.3800, lng: 128.6600 },
    "철원군": { lat: 38.1467, lng: 127.3100 },
    "화천군": { lat: 38.1000, lng: 127.7000 },
    "양구군": { lat: 38.0800, lng: 127.9000 },
    "인제군": { lat: 38.0700, lng: 128.1700 },
    "고성군": { lat: 38.3700, lng: 128.4000 },
    "양양군": { lat: 38.0700, lng: 128.6200 }
};

/**
 * Initializes the map and all functionalities that depend on the map.
 */
function initMap() {
    const mapContainer = document.getElementById("map");
    const mapOption = {
        center: new kakao.maps.LatLng(37.8228, 128.1555),
        level: 9
    };
    const map = new kakao.maps.Map(mapContainer, mapOption);

    // let clickMarker = null; // Removed from here
    let searchMarkers = [];
    const selectedRegions = []; // For the region tags below the chart

    // A. Click listener for fire prediction
    kakao.maps.event.addListener(map, 'click', async (mouseEvent) => {
        const latlng = mouseEvent.latLng;
        
        // Immediately show loading overlay and clear previous elements
        document.getElementById("loadingOverlay").style.display = "flex";
        if (clickMarker) clickMarker.setMap(null);
        if (currentFirePolygon) currentFirePolygon.setMap(null);
        if (currentInfoOverlay) currentInfoOverlay.setMap(null);
        if (currentWindArrowOverlay) currentWindArrowOverlay.setMap(null);

        clickMarker = new kakao.maps.Marker({
            position: latlng,
            map: map,
            image: new kakao.maps.MarkerImage(
                'https://t1.daumcdn.net/localimg/localimages/07/mapapidoc/marker_red.png', // A simple red dot
                new kakao.maps.Size(15, 15),
                { offset: new kakao.maps.Point(7, 7) } // Center the dot
            )
        });
        currentPredictionCenter = latlng; // Store the center for redrawing

        abortController = new AbortController(); // Initialize new AbortController for this request
        const signal = abortController.signal;
        const requestId = `req-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`; // Unique ID for this request

        try {
            const now = new Date();
            now.setDate(now.getDate() - 4); // Go back 4 days for data availability
            const fireDate = now.toISOString().slice(0, 10); // Format as "YYYY-MM-DD"
            
            // Initial prediction is always for 12 hours
            const initialDuration = 12; 
            document.getElementById("durationSelect").value = initialDuration; // Set dropdown to 12h

            const response = await fetch(`/fire-predict?lat=${latlng.getLat()}&lng=${latlng.getLng()}&fireDate=${fireDate}&fireTime=1200&duration=${initialDuration}&requestId=${requestId}`, { signal });
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP error! status: ${response.status}, details: ${errorText}`);
            }
            const prediction = await response.json();
            
            console.log("✅ Prediction data received from servlet:", prediction);
            currentPredictionData = prediction; // Store the full prediction data

            // Display initial 12-hour prediction
            currentFirePolygon = displayFirePrediction(map, latlng.getLat(), latlng.getLng(), prediction.predicted_distance_m, prediction.wind_direction_deg, prediction.predicted_speed_category);
            currentInfoOverlay = displayInfoOverlay(map, latlng, prediction.predicted_area_ha, prediction.predicted_distance_m, prediction.wind_direction_deg, prediction.predicted_speed_category);
            currentWindArrowOverlay = displayWindDirectionArrow(map, latlng, prediction.wind_direction_deg); // Display the arrow
            
            // Show duration controls and update display
            document.querySelector(".prediction-controls").style.display = "flex";
            document.getElementById("predictedDurationDisplay").innerText = `예측 시간: ${initialDuration}시간`;

            // Update charts for initial 12-hour prediction
            const distanceData = formatDataForDistanceChart(prediction.predicted_area_ha, initialDuration);
            const speedData = formatDataForSpeedChart(prediction.predicted_speed_category);
            createDistanceChart(distanceData);
            createSpeedLevelChart(speedData);

        } catch (error) {
            if (error.name === 'AbortError') {
                console.log("Prediction aborted by user.");
                // No alert needed for user-initiated abort
            } else {
                console.error("Error fetching fire prediction:", error);
                alert("산불 예측 데이터를 가져오는 데 실패했습니다.");
            }
            resetMapAndUI(map); // Reset UI on any error or abort
        } finally {
            // Hide loading overlay
            document.getElementById("loadingOverlay").style.display = "none";
            abortController = null; // Clear the controller
        }
    });

    // B. Region selection button listener
    document.getElementById("selectRegionBtn").addEventListener("click", () => {
        const selectedRegion = document.getElementById("regionSelect").value;
        if (!selectedRegion) {
            alert("지역을 선택해주세요.");
            return;
        }

        const coords = regionCoordinates[selectedRegion];
        if (coords) {
            map.setCenter(new kakao.maps.LatLng(coords.lat, coords.lng));
            map.setLevel(7); // Adjust zoom level for region view
            // Clear any previous prediction elements when moving to a new region
            if (clickMarker) clickMarker.setMap(null);
            if (currentFirePolygon) currentFirePolygon.setMap(null);
            if (currentInfoOverlay) currentInfoOverlay.setMap(null);
            if (currentWindArrowOverlay) currentWindArrowOverlay.setMap(null);
            document.querySelector(".prediction-controls").style.display = "none"; // Hide duration controls
            document.getElementById("predictedDurationDisplay").innerText = "";
            // Reset global prediction data (optional, but good for consistency)
            currentPredictionData = null;
            currentPredictionCenter = null;
            currentFirePolygon = null;
            currentInfoOverlay = null;
            currentWindArrowOverlay = null;
            // Reset charts (optional, depending on desired behavior)
            createDistanceChart({ labels: [], datasets: [] });
            createSpeedLevelChart({ labels: [], datasets: [] });
        } else {
            alert("선택된 지역의 좌표 정보가 없습니다.");
        }
    });

    // C. Reset button listener
    document.getElementById("resetBtn").addEventListener("click", () => {
        resetMapAndUI(map); // Use the centralized reset function
    });

    // D. Duration selection listener (reactive update)
    document.getElementById("durationSelect").addEventListener("change", () => {
        if (!currentPredictionData || !currentPredictionCenter) {
            alert("먼저 지도에 산불 위치를 지정하여 예측을 실행해주세요.");
            return;
        }

        const selectedDuration = parseInt(document.getElementById("durationSelect").value);
        const initialPredictedDistance12h = currentPredictionData.predicted_distance_m;
        const windDirection = currentPredictionData.wind_direction_deg;
        const speedCategory = currentPredictionData.predicted_speed_category;

        // Calculate new distance based on selected duration (linear scaling)
        const newPredictedDistance = (initialPredictedDistance12h / 12) * selectedDuration;

        // Update the polygon on the map
        if (currentFirePolygon) currentFirePolygon.setMap(null); // Clear old polygon
        currentFirePolygon = displayFirePrediction(map, currentPredictionCenter.getLat(), currentPredictionCenter.getLng(), newPredictedDistance, windDirection, speedCategory);

        // Update the info overlay
        if (currentInfoOverlay) currentInfoOverlay.setMap(null); // Clear old overlay
        // Recalculate area for the new duration for display in overlay
        const newPredictedAreaHa = (currentPredictionData.predicted_area_ha / 12) * selectedDuration;
        console.log(`Duration changed to ${selectedDuration}h: Initial 12h Area: ${currentPredictionData.predicted_area_ha.toFixed(2)} ha, New Area: ${newPredictedAreaHa.toFixed(2)} ha, New Distance: ${newPredictedDistance.toFixed(1)} m`);
        currentInfoOverlay = displayInfoOverlay(map, currentPredictionCenter, newPredictedAreaHa, newPredictedDistance, windDirection, speedCategory);

        // Update the distance chart
        const distanceData = formatDataForDistanceChart(currentPredictionData.predicted_area_ha, selectedDuration);
        createDistanceChart(distanceData);

        // Update the predicted duration display
        document.getElementById("predictedDurationDisplay").innerText = `예측 시간: ${selectedDuration}시간`;
    });

    // E. Cancel Prediction button listener
    document.getElementById("cancelPredictionBtn").addEventListener("click", async () => {
        if (abortController) {
            abortController.abort(); // Abort the ongoing fetch request on the client side
        }
        document.getElementById("loadingOverlay").style.display = "none"; // Hide loading overlay immediately
        resetMapAndUI(map); // Reset UI

        // Send a request to the server to terminate the Python process
        if (currentPredictionData && currentPredictionData.requestId) { // Check if requestId exists
            try {
                const response = await fetch('/fire-predict-cancel', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: `requestId=${currentPredictionData.requestId}`
                });
                if (!response.ok) {
                    const errorText = await response.text();
                    console.error(`Server cancellation failed: ${response.status}, ${errorText}`);
                } else {
                    console.log("Server-side prediction process termination requested.");
                }
            } catch (error) {
                console.error("Error sending cancellation request to server:", error);
            }
        }
    });
}

/**
 * Resets all map elements and UI controls to their initial state.
 * @param {kakao.maps.Map} map The Kakao Map instance.
 */
function resetMapAndUI(map) {
    // Clear map elements
    if (clickMarker) clickMarker.setMap(null);
    if (currentFirePolygon) currentFirePolygon.setMap(null);
    if (currentInfoOverlay) currentInfoOverlay.setMap(null);
    if (currentWindArrowOverlay) currentWindArrowOverlay.setMap(null);
    
    // Reset global prediction data
    currentPredictionData = null;
    currentPredictionCenter = null;
    currentFirePolygon = null;
    currentInfoOverlay = null;
    currentWindArrowOverlay = null;

    // Hide duration controls
    document.querySelector(".prediction-controls").style.display = "none";
    document.getElementById("predictedDurationDisplay").innerText = "";

    // Reset charts
    createDistanceChart({ labels: [], datasets: [] });
    createSpeedLevelChart({ labels: [], datasets: [] });

    // Reset region selection dropdown
    document.getElementById("regionSelect").value = "";
    map.setCenter(new kakao.maps.LatLng(37.8228, 128.1555)); // Reset to default center
    map.setLevel(9); // Reset to default zoom
}

function displayWindDirectionArrow(map, position, wind_direction_deg) {
    // If wind direction is invalid, do not display arrow.
    if (wind_direction_deg <= -999.0) {
        console.warn("Invalid wind direction data. Not displaying wind arrow.");
        return null;
    }

    // Kakao Maps degrees are clockwise from North (0=N, 90=E, 180=S, 270=W)
    // CSS transform rotate is clockwise from top (0=up, 90=right, 180=down, 270=left)
    // So, the wind_direction_deg can be directly used for CSS rotation.
    const rotation = wind_direction_deg;

    const content = `
        <div class="wind-arrow-overlay" style="transform: rotate(${rotation}deg);">
            <svg width="30" height="30" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2L12 22M12 2L18 8M12 2L6 8" stroke="#333" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        </div>
    `;

    const customOverlay = new kakao.maps.CustomOverlay({
        map: map,
        position: position,
        content: content,
        yAnchor: 0.5, // Center vertically
        xAnchor: 0.5  // Center horizontally
    });

    return customOverlay;
}

function displayFirePrediction(map, centerLat, centerLon, predicted_distance_m, wind_direction_deg, predicted_speed_category) {
    // --- NEW: Color mapping based on speed category ---
    const speedColors = {
        0: { stroke: '#FFD700', fill: '#FFFFE0' }, // Low: Yellow
        1: { stroke: '#FFA500', fill: '#FFDAB9' }, // Medium: Orange
        2: { stroke: '#FF0000', fill: '#FFC0CB' }  // High: Red
    };
    const colors = speedColors[predicted_speed_category] || speedColors[0]; // Default to low speed color

    // If wind direction is invalid, draw a simple circle as a fallback.
    if (wind_direction_deg <= -999.0) {
        console.warn("Invalid wind direction data. Drawing a simple circle as a fallback.");
        const circle = new kakao.maps.Circle({
            map: map,
            center: new kakao.maps.LatLng(centerLat, centerLon),
            radius: predicted_distance_m,
            strokeWeight: 2,
            strokeColor: colors.stroke,
            strokeOpacity: 0.8,
            fillColor: colors.fill,
            fillOpacity: 0.5
        });
        map.setCenter(new kakao.maps.LatLng(centerLat, centerLon));
        map.setLevel(7);
        return circle;
    }

    const centerPoint = new kakao.maps.LatLng(centerLat, centerLon);
    const path = [];
    const numPoints = 64; // Use more points for a smoother shape

    for (let i = 0; i < numPoints; i++) {
        const angle = i * (360 / numPoints);

        // --- Wind Effect Logic ---
        let angleDifference = Math.abs(angle - wind_direction_deg);
        if (angleDifference > 180) angleDifference = 360 - angleDifference;
        const stretchFactor = 1.8;
        const sideFactor = 0.6;
        const radiusModifier = Math.cos(toRadians(angleDifference / 2));
        const interpolation = (stretchFactor - sideFactor) * Math.pow(radiusModifier, 4) + sideFactor;
        const effectiveRadius = predicted_distance_m * interpolation;

        const pointCoords = getEndpoint(centerLat, centerLon, angle, effectiveRadius);
        path.push(new kakao.maps.LatLng(pointCoords.lat, pointCoords.lng));
    }

    const polygon = new kakao.maps.Polygon({
        path: path,
        strokeWeight: 2,
        strokeColor: colors.stroke,
        strokeOpacity: 0.8,
        fillColor: colors.fill,
        fillOpacity: 0.5,
        map: map
    });

    const bounds = new kakao.maps.LatLngBounds();
    path.forEach(p => bounds.extend(p));
    map.setBounds(bounds);

    return polygon;
}

/**
 * --- NEW: Creates and displays a custom overlay with prediction info. ---
 */
function displayInfoOverlay(map, position, predicted_area_ha, predicted_distance_m, wind_direction_deg, predicted_speed_category) {
    const speedText = { 0: '느림 (1등급)', 1: '중간 (2등급)', 2: '빠름 (3등급)' };
    const windText = wind_direction_deg <= -999.0 ? 'N/A' : `${wind_direction_deg.toFixed(1)}°`;

    const content = `
        <div class="info-overlay">
            <h4>예측 정보</h4>
            <ul>
                <li><strong>예상 피해 면적:</strong> ${predicted_area_ha.toFixed(2)} ha</li>
                <li><strong>예상 확산 거리:</strong> ${predicted_distance_m.toFixed(1)} m</li>
                <li><strong>주요 확산 방향:</strong> ${windText}</li>
                <li><strong>예상 확산 속도:</strong> ${speedText[predicted_speed_category] || '알 수 없음'}</li>
            </ul>
        </div>
    `;

    const customOverlay = new kakao.maps.CustomOverlay({
        map: map,
        position: position,
        content: content,
        yAnchor: 1.1, // Position the overlay above the marker
        xAnchor: 0.5
    });

    return customOverlay;
}

/**
 * Calculates the coordinates of an endpoint given a starting point,
 * a bearing (direction in degrees), and a distance in meters.
 * This is a self-contained replacement for the geometry library's computeOffset.
 */
function getEndpoint(lat, lng, bearing, distance) {
    const R = 6378137; // Earth's radius in meters (WGS-84)
    const brng = toRadians(bearing);
    const lat1 = toRadians(lat);
    const lon1 = toRadians(lng);

    const lat2 = Math.asin(Math.sin(lat1) * Math.cos(distance / R) +
                      Math.cos(lat1) * Math.sin(distance / R) * Math.cos(brng));

    const lon2 = lon1 + Math.atan2(Math.sin(brng) * Math.sin(distance / R) * Math.cos(lat1),
                                 Math.cos(distance / R) - Math.sin(lat1) * Math.sin(lat2));

    return {
        lat: toDegrees(lat2),
        lng: toDegrees(lon2)
    };
}

function toRadians(degrees) {
    return degrees * Math.PI / 180;
}

function toDegrees(radians) {
    return radians * 180 / Math.PI;
}

function addRegionTag(region, selectedRegions, onRemoveCallback) {
  const container = document.getElementById("selectedRegions");
  if (selectedRegions.length > 4) {
    alert("최대 5개 지역까지만 선택할 수 있습니다.");
    selectedRegions.pop();
    return;
  }

  const tag = document.createElement("div");
  tag.className = "region-tag";
  tag.innerHTML = `<span class="region-name">${region}</span><span class="remove-btn">×</span>`;
  container.appendChild(tag);

  tag.querySelector(".remove-btn").addEventListener("click", () => {
    container.removeChild(tag);
    const index = selectedRegions.indexOf(region);
    if (index > -1) selectedRegions.splice(index, 1);
    onRemoveCallback();
  });
}

function setupHamburgerMenu() {
  const hamburger = document.getElementById("hamburgerBtn");
  const sideMenu = document.getElementById("sideMenu");
  hamburger.addEventListener("click", () => {
    sideMenu.classList.toggle("active");
    hamburger.classList.toggle("active");
  });
}

function setupHeaderScroll() {
    const header = document.querySelector("header");
    if (!header) return;
    let lastToggleY = window.scrollY;
    let ticking = false;
    const scrollThreshold = 120;
    const minScrollToHide = 150;

    function handleScroll() {
      const currentY = window.scrollY;
      const delta = currentY - lastToggleY;
      if (Math.abs(delta) >= scrollThreshold) {
        if (delta > 0 && currentY > minScrollToHide) {
          header.classList.add("hide");
        } else if (delta < 0) {
          header.classList.remove("hide");
        }
        lastToggleY = currentY;
      }
      ticking = false;
    }

    window.addEventListener("scroll", () => {
      if (!ticking) {
        window.requestAnimationFrame(handleScroll);
        ticking = true;
      }
    });
}

function formatDataForDistanceChart(predicted_area_ha, selectedDuration) {
    const final_radius_m_at_12h = Math.sqrt(predicted_area_ha * 10000 / Math.PI); // Convert ha to m^2, then to radius
    
    const labels = [];
    const data = [];
    for (let h = 3; h <= 12; h += 3) {
        labels.push(`${h}시간 후`);
        data.push((final_radius_m_at_12h / 12) * h / 1000); // Convert meters to kilometers
        if (h === selectedDuration) break; // Stop at the selected duration
    }

    return {
        labels: labels,
        datasets: [{
            label: `예상 확산 거리(km)`,
            data: data,
            borderColor: `hsl(15, 70%, 50%)`,
            fill: false,
        }]
    };
}

function formatDataForSpeedChart(predicted_speed_category) {
    const labels = ["1등급(느림)", "2등급(중간)", "3등급(빠름)"];
    const data = [0, 0, 0];
    if (predicted_speed_category >= 0 && predicted_speed_category < data.length) {
        data[predicted_speed_category] = 1;
    }

    return {
        labels,
        datasets: [{
            label: '예측된 확산 속도 등급',
            data: data,
            backgroundColor: `hsla(200, 70%, 50%, 0.7)`,
        }]
    };
}

// Mock data functions are no longer directly used for prediction charts,
// but kept for potential future use or other chart sections.
function generateMockLineData(region) {
  const data = {
    labels: ["3시간 후", "6시간 후", "9시간 후", "12시간 후"],
    datasets: [{
      label: `${region} 확산 거리(km)`,
      data: Array.from({ length: 4 }, () => Math.random() * 10),
      borderColor: `hsl(${Math.random() * 360}, 70%, 50%)`,
      fill: false,
    }, ],
  };
  return data;
}

function generateMockBarData(regions) {
  const labels = ["1등급(느림)", "2등급(중간)", "3등급(빠름)"];
  const datasets = regions.map((region, i) => {
    const hue = (360 / regions.length) * i;
    return {
      label: region,
      data: Array.from({ length: 3 }, () => Math.floor(Math.random() * 100)),
      backgroundColor: `hsla(${hue}, 70%, 50%, 0.7)`,
    };
  });
  return { labels, datasets };
}
