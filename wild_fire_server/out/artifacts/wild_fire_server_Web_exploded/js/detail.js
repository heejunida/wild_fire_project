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
    let searchMarkers = [];
    const selectedRegions = [];

    // A. Click listener for fire prediction
    kakao.maps.event.addListener(map, 'click', async (mouseEvent) => {
        const latlng = mouseEvent.latLng;
        if (clickMarker) clickMarker.setMap(null);
        if (firePolygon) firePolygon.setMap(null);

        clickMarker = new kakao.maps.Marker({ position: latlng, map: map });

        try {
            // --- DURATION LOGIC ---
            const duration = document.getElementById("durationSelect").value;
            const now = new Date();
            const fireDate = now.toISOString().slice(0, 10); // "YYYY-MM-DD"
            const fireTime = now.toTimeString().slice(0, 5).replace(':', ''); // "HHMM"

            const response = await fetch(`/fire-predict?lat=${latlng.getLat()}&lng=${latlng.getLng()}&fireDate=${fireDate}&fireTime=${fireTime}&duration=${duration}`);
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP error! status: ${response.status}, details: ${errorText}`);
            }
            const prediction = await response.json();
            
            console.log("✅ Prediction data received from servlet:", prediction);
            
            firePolygon = displayFirePrediction(map, latlng.getLat(), latlng.getLng(), prediction);

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
    const { predicted_area_ha, wind_direction_deg } = predictionData;
    const radius_m = Math.sqrt(predicted_area_ha * 10000 / Math.PI);
    const centerPoint = new kakao.maps.LatLng(centerLat, centerLon);
    const numPoints = 32;
    const path = [];

    for (let i = 0; i < numPoints; i++) {
        const angle = i * (360 / numPoints);
        let effectiveRadius = radius_m;
        if (Math.abs(angle - wind_direction_deg) < 45 || Math.abs(angle - wind_direction_deg) > 315) {
            effectiveRadius *= 1.5;
        } else {
            effectiveRadius *= 0.7;
        }
        const point = kakao.maps.geometry.spherical.computeOffset(centerPoint, effectiveRadius, angle);
        path.push(point);
    }
    
    const polygon = new kakao.maps.Polygon({
        path: path,
        strokeWeight: 3,
        strokeColor: '#FF0000',
        strokeOpacity: 0.8,
        fillColor: '#FF0000',
        fillOpacity: 0.35,
        map: map
    });

    const bounds = new kakao.maps.LatLngBounds();
    path.forEach(p => bounds.extend(p));
    map.setBounds(bounds);

    return polygon;
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
