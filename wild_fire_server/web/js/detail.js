/**
 * This is the main entry point for all JavaScript on the page.
 * It waits for the HTML document to be fully loaded and parsed.
 */
document.addEventListener("DOMContentLoaded", () => {
    setupHamburgerMenu();
    setupHeaderScroll();
    kakao.maps.load(initMap);
});

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

    let clickMarker = null;
    let firePolygon = null;
    let infoOverlay = null;
    let searchMarkers = [];
    const selectedRegions = [];

    // A. Click listener for fire prediction
    kakao.maps.event.addListener(map, 'click', async (mouseEvent) => {
        const latlng = mouseEvent.latLng;
        if (clickMarker) clickMarker.setMap(null);
        if (firePolygon) firePolygon.setMap(null);
        if (infoOverlay) infoOverlay.setMap(null); // Clear previous overlay

        clickMarker = new kakao.maps.Marker({ position: latlng, map: map });

        try {
            // --- FIX: Use today's date minus 4 days to ensure data availability ---
            const now = new Date();
            now.setDate(now.getDate() - 4); // Go back 4 days
            const fireDate = now.toISOString().slice(0, 10); // Format as "YYYY-MM-DD"
            
            // The fireTime and duration are sent but not critical for the current prediction model
            const fireTime = "1200"; // Use a consistent midday time
            const duration = document.getElementById("durationSelect").value;

            const response = await fetch(`/fire-predict?lat=${latlng.getLat()}&lng=${latlng.getLng()}&fireDate=${fireDate}&fireTime=${fireTime}&duration=${duration}`);
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP error! status: ${response.status}, details: ${errorText}`);
            }
            const prediction = await response.json();
            
            console.log("✅ Prediction data received from servlet:", prediction);
            
            firePolygon = displayFirePrediction(map, latlng.getLat(), latlng.getLng(), prediction);
            infoOverlay = displayInfoOverlay(map, latlng, prediction); // Create and display the info overlay

            const distanceData = formatDataForDistanceChart(prediction, parseInt(duration));
            const speedData = formatDataForSpeedChart(prediction);
            createDistanceChart(distanceData);
            createSpeedLevelChart(speedData);

        } catch (error) {
            console.error("Error fetching fire prediction:", error);
            alert("산불 예측 데이터를 가져오는 데 실패했습니다.");
        }
    });

    // B. Search button listener
    document.getElementById("searchBtn").addEventListener("click", async () => {
        const selected = document.getElementById("regionSelect").value;
        if (!selected) {
            alert("지역을 선택해주세요.");
            return;
        }
        if (selectedRegions.includes(selected)) {
            alert("이미 선택된 지역입니다.");
            return;
        }

        try {
            const response = await fetch("json/mock_forest_locations_with_coords.json");
            const data = await response.json();
            const locations = data[selected];

            if (!locations || locations.length === 0) {
                alert("해당 지역의 산림 정보가 없습니다.");
                return;
            }

            searchMarkers.forEach(m => m.setMap(null));
            searchMarkers = [];

            const first = locations[0];
            map.setCenter(new kakao.maps.LatLng(first.lat, first.lng));

            locations.forEach(loc => {
                const marker = new kakao.maps.Marker({
                    map,
                    position: new kakao.maps.LatLng(loc.lat, loc.lng),
                    title: loc.location
                });
                searchMarkers.push(marker);
            });

            selectedRegions.push(selected);
            addRegionTag(selected, selectedRegions, () => {
                const mockBarData = generateMockBarData(selectedRegions);
                createSpeedLevelChart(mockBarData);
            });

            const mockLineData = generateMockLineData(selected);
            const mockBarData = generateMockBarData(selectedRegions);
            createDistanceChart(mockLineData);
            createSpeedLevelChart(mockBarData);

        } catch (err) {
            console.error("데이터 로딩 오류", err);
            alert("산림 데이터를 불러오는 데 실패했습니다.");
        }
    });

    // C. Reset button listener
    document.getElementById("resetBtn").addEventListener("click", () => {
        searchMarkers.forEach(m => m.setMap(null));
        searchMarkers = [];
        selectedRegions.length = 0;
        
        const regionTagsContainer = document.getElementById("selectedRegions");
        if (regionTagsContainer) {
            regionTagsContainer.innerHTML = "";
        }
        
        createSpeedLevelChart({});
    });
}

function displayFirePrediction(map, centerLat, centerLon, predictionData) {
    const { predicted_distance_m, wind_direction_deg, predicted_speed_category } = predictionData;

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
function displayInfoOverlay(map, position, predictionData) {
    const {
        predicted_area_ha,
        predicted_distance_m,
        wind_direction_deg,
        predicted_speed_category
    } = predictionData;

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

function formatDataForDistanceChart(prediction, duration) {
    const { predicted_area_ha } = prediction;
    const final_radius_km = Math.sqrt(predicted_area_ha / 100 / Math.PI);
    
    // --- CORRECTED LABELS AND DATA ---
    const labels = ["3시간 후", "6시간 후", "9시간 후", "12시간 후"];
    const data = [
        (final_radius_km / 12) * 3,
        (final_radius_km / 12) * 6,
        (final_radius_km / 12) * 9,
        (final_radius_km / 12) * 12
    ];

    // Only show the labels up to the selected duration
    const durationIndex = labels.findIndex(label => label.startsWith(duration));
    const visibleLabels = labels.slice(0, durationIndex + 1);
    const visibleData = data.slice(0, durationIndex + 1);

    return {
        labels: visibleLabels,
        datasets: [{
            label: `예상 확산 거리(km)`,
            data: visibleData,
            borderColor: `hsl(15, 70%, 50%)`,
            fill: false,
        }]
    };
}

function formatDataForSpeedChart(prediction) {
    const { predicted_speed_category } = prediction;
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
