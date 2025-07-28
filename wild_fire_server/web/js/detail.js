/**
 * Main entry point for all JavaScript on the page.
 */
document.addEventListener("DOMContentLoaded", () => {
    setupHamburgerMenu();
    setupHeaderScroll();
    window.addEventListener('load', initMap);
});

// Global variables
let mapInstance = null;
let currentPredictionData = null;
let currentPredictionCenter = null;
let currentFirePolygon = null;
let currentInfoOverlay = null;
let currentWindArrowOverlay = null;
let abortController = null;
let clickMarker = null;
let pollingTimerId = null;

const regionCoordinates = {
    "춘천시": {lat: 37.8813, lng: 127.7298}, "원주시": {lat: 37.3422, lng: 127.9200},
    "강릉시": {lat: 37.7519, lng: 128.8762}, "동해시": {lat: 37.5236, lng: 129.1167},
    "태백시": {lat: 37.1636, lng: 128.9850}, "속초시": {lat: 38.2000, lng: 128.5917},
    "삼척시": {lat: 37.4486, lng: 129.1642}, "홍천군": {lat: 37.8850, lng: 127.8900},
    "횡성군": {lat: 37.4922, lng: 128.1950}, "영월군": {lat: 37.1850, lng: 128.4680},
    "평창군": {lat: 37.3722, lng: 128.3950}, "정선군": {lat: 37.3800, lng: 128.6600},
    "철원군": {lat: 38.1467, lng: 127.3100}, "화천군": {lat: 38.1000, lng: 127.7000},
    "양구군": {lat: 38.0800, lng: 127.9000}, "인제군": {lat: 38.0700, lng: 128.1700},
    "고성군": {lat: 38.3700, lng: 128.4000}, "양양군": {lat: 38.0700, lng: 128.6200}
};

function initMap() {
    const mapContainer = document.getElementById("map");
    const mapOption = { center: new kakao.maps.LatLng(37.8228, 128.1555), level: 9 };
    mapInstance = new kakao.maps.Map(mapContainer, mapOption);

    mapInstance.relayout();

    let lastStatusMessage = '';

    kakao.maps.event.addListener(mapInstance, 'click', async (mouseEvent) => {
        if (!window.loginUserId) {
            return alert("로그인이 필요합니다.");
        }
        const latlng = mouseEvent.latLng;

        // --- DEBUGGING STEP 1: Log the coordinates ---
        console.log("Clicked coordinates:", latlng.getLat(), latlng.getLng());

        resetMapAndUI(mapInstance, false);
        clickMarker = new kakao.maps.Marker({ position: latlng, map: mapInstance });
        currentPredictionCenter = latlng;

        mapInstance.setCenter(latlng);
        mapInstance.setLevel(4);

        document.getElementById("loadingOverlay").style.display = "flex";
        const loadingText = document.querySelector("#loadingOverlay p");
        if (loadingText) loadingText.textContent = "예측 데이터를 불러오는 중...";

        abortController = new AbortController();
        const requestId = `req-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
        currentPredictionData = { requestId };

        try {
            const now = new Date();
            const fireDate = now.toISOString().slice(0, 10);
            const fireTime = now.toTimeString().slice(0, 5);

            const response = await fetch(`/fire-predict?lat=${latlng.getLat()}&lng=${latlng.getLng()}&fireDate=${fireDate}&fireTime=${fireTime}&requestId=${requestId}&userId=${window.loginUserId}`, { signal: abortController.signal });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            await response.json();
            pollPredictionResult(requestId, latlng);
        } catch (error) {
            if (error.name !== 'AbortError') console.error("Error fetching fire prediction:", error);
            resetMapAndUI(mapInstance);
        }
    });

    function pollPredictionResult(requestId, latlng, tryCount = 0) {
        if (abortController?.signal.aborted) return;
        if (pollingTimerId) clearTimeout(pollingTimerId);

        fetch(`/fire-predict-result?requestId=${requestId}`)
            .then(res => res.json())
            .then(prediction => {
                if (abortController?.signal.aborted) return;

                if (prediction.status === "processing") {
                    if (prediction.message && prediction.message !== lastStatusMessage) {
                        lastStatusMessage = prediction.message;
                        const loadingText = document.querySelector("#loadingOverlay p");
                        if (loadingText) loadingText.textContent = lastStatusMessage;
                    }
                    pollingTimerId = setTimeout(() => pollPredictionResult(requestId, latlng, tryCount + 1), 500);
                } else if (prediction.status === "success") {
                    currentPredictionData = { ...prediction, requestId };
                    displayFullPrediction(mapInstance, latlng, prediction);
                } else {
                    console.error("Server-side prediction error:", prediction.error);
                    resetMapAndUI(mapInstance);
                }
            })
            .catch(err => {
                if (abortController?.signal.aborted) return;
                if (tryCount < 40) {
                    pollingTimerId = setTimeout(() => pollPredictionResult(requestId, latlng, tryCount + 1), 500);
                } else {
                    resetMapAndUI(mapInstance);
                }
            });
    }

    document.getElementById("cancelPredictionBtn").addEventListener("click", () => handleCancel(mapInstance));
    document.getElementById("selectRegionBtn").addEventListener("click", () => handleRegionSelect(mapInstance));
    document.getElementById("resetBtn").addEventListener("click", () => resetMapAndUI(mapInstance, true));
    document.getElementById("durationSelect").addEventListener("change", () => handleDurationChange(mapInstance));
}

let resizeTimer;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => { if (mapInstance) mapInstance.relayout(); }, 250);
});

function displayFullPrediction(map, latlng, prediction) {
    const finalAreaHa = prediction.area_pred_median;
    const speedCategory = fwiToSpeedCategory(prediction.fwi_pred);
    const windDirection = prediction.dir_pred * 45;

    const areaAt12h = calculateGrowthWithSCurve(12, finalAreaHa);
    const distanceAt12h = Math.sqrt(areaAt12h * 10000 / Math.PI);

    currentFirePolygon = displayFirePrediction(map, latlng.getLat(), latlng.getLng(), distanceAt12h, windDirection, speedCategory);
    currentInfoOverlay = displayInfoOverlay(map, latlng, prediction);
    currentWindArrowOverlay = displayWindDirectionArrow(map, latlng, windDirection);

    document.querySelector(".prediction-controls").style.display = "flex";
    document.getElementById("durationSelect").value = "12";
    document.getElementById("predictedDurationDisplay").innerText = `예측 시간: 12시간`;

    createDistanceChart(formatDataForDistanceChart(finalAreaHa));
    displayConfidenceMetrics(prediction);

    document.getElementById("loadingOverlay").style.display = "none";
    abortController = null;
    pollingTimerId = null;
}

async function handleCancel(map) {
    if (abortController) abortController.abort();
    if (pollingTimerId) clearTimeout(pollingTimerId);
    if (currentPredictionData?.requestId) {
        try {
            await fetch('/fire-predict-cancel', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `requestId=${currentPredictionData.requestId}`
            });
        } catch (error) {
            console.error("Error sending cancellation request:", error);
        }
    }
    resetMapAndUI(map);
}

function handleRegionSelect(map) {
    const selectedRegion = document.getElementById("regionSelect").value;
    if (!selectedRegion) return alert("지역을 선택해주세요.");
    const coords = regionCoordinates[selectedRegion];
    if (coords) {
        map.setCenter(new kakao.maps.LatLng(coords.lat, coords.lng));
        map.setLevel(7);
        resetMapAndUI(map, false);
    }
}

function handleDurationChange(map) {
    if (!currentPredictionData || !currentPredictionCenter) return;
    const selectedDuration = parseInt(document.getElementById("durationSelect").value);
    const finalAreaHa = currentPredictionData.area_pred_median;
    const windDirection = currentPredictionData.dir_pred * 45;
    const speedCategory = fwiToSpeedCategory(currentPredictionData.fwi_pred);

    const newPredictedAreaHa = calculateGrowthWithSCurve(selectedDuration, finalAreaHa);
    const newPredictedDistance = Math.sqrt(newPredictedAreaHa * 10000 / Math.PI);

    if (currentFirePolygon) currentFirePolygon.setMap(null);
    currentFirePolygon = displayFirePrediction(map, currentPredictionCenter.getLat(), currentPredictionCenter.getLng(), newPredictedDistance, windDirection, speedCategory);
    
    if (currentInfoOverlay) currentInfoOverlay.setMap(null);
    currentInfoOverlay = displayInfoOverlay(map, currentPredictionCenter, currentPredictionData, newPredictedAreaHa, newPredictedDistance);

    document.getElementById("predictedDurationDisplay").innerText = `예측 시간: ${selectedDuration}시간`;
}

function fwiToSpeedCategory(fwi) {
    if (fwi < 10) return 0; if (fwi < 25) return 1; return 2;
}

function calculateGrowthWithSCurve(time, maxArea) {
    const L = maxArea, k = 0.8, x0 = 6;
    return L / (1 + Math.exp(-k * (time - x0)));
}

function resetMapAndUI(map, resetPosition = true) {
    document.getElementById("loadingOverlay").style.display = "none";
    if (clickMarker) clickMarker.setMap(null);
    if (currentFirePolygon) currentFirePolygon.setMap(null);
    if (currentInfoOverlay) currentInfoOverlay.setMap(null);
    if (currentWindArrowOverlay) currentWindArrowOverlay.setMap(null);
    if (pollingTimerId) clearTimeout(pollingTimerId);
    
    currentPredictionData = currentPredictionCenter = currentFirePolygon = currentInfoOverlay = currentWindArrowOverlay = null;
    
    document.querySelector(".prediction-controls").style.display = "none";
    document.getElementById("predictedDurationDisplay").innerText = "";
    document.getElementById("confidenceMetrics").innerHTML = "";

    if (typeof distanceChartInstance !== 'undefined' && distanceChartInstance) {
        distanceChartInstance.destroy();
    }

    if (resetPosition) {
        document.getElementById("regionSelect").value = "";
        map.setCenter(new kakao.maps.LatLng(37.8228, 128.1555));
        map.setLevel(9);
    }
}

function displayWindDirectionArrow(map, position, wind_direction_deg) {
    if (wind_direction_deg <= -999.0) return null;
    const content = `<div class="wind-arrow-overlay" style="transform: rotate(${wind_direction_deg}deg);"><svg width="30" height="30" viewBox="0 0 24 24"><path d="M12 2L12 22M12 2L18 8M12 2L6 8" stroke="#333" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></div>`;
    return new kakao.maps.CustomOverlay({ map, position, content, yAnchor: 0.5, xAnchor: 0.5 });
}

function displayFirePrediction(map, centerLat, centerLon, predicted_distance_m, wind_direction_deg, speedCategory) {
    const speedColors = { 0: {stroke: '#FFD700', fill: '#FFFFE0'}, 1: {stroke: '#FFA500', fill: '#FFDAB9'}, 2: {stroke: '#FF0000', fill: '#FFC0CB'} };
    const colors = speedColors[speedCategory] || speedColors[0];
    if (wind_direction_deg <= -999.0) {
        return new kakao.maps.Circle({ map, center: new kakao.maps.LatLng(centerLat, centerLon), radius: predicted_distance_m, strokeWeight: 2, strokeColor: colors.stroke, strokeOpacity: 0.8, fillColor: colors.fill, fillOpacity: 0.5 });
    }
    const path = [];
    for (let i = 0; i < 64; i++) {
        const angle = i * (360 / 64);
        let diff = Math.abs(angle - wind_direction_deg);
        if (diff > 180) diff = 360 - diff;
        const interp = (1.8 - 0.6) * Math.pow(Math.cos(toRadians(diff / 2)), 4) + 0.6;
        const radius = predicted_distance_m * interp;
        const point = getEndpoint(centerLat, centerLon, angle, radius);
        path.push(new kakao.maps.LatLng(point.lat, point.lng));
    }
    return new kakao.maps.Polygon({ path, strokeWeight: 2, strokeColor: colors.stroke, strokeOpacity: 0.8, fillColor: colors.fill, fillOpacity: 0.5, map: map });
}

function displayInfoOverlay(map, position, prediction, area_ha_override = null, distance_m_override = null) {
    const area_ha = area_ha_override ?? prediction.area_pred_median;
    const distance_m = distance_m_override ?? Math.sqrt(area_ha * 10000 / Math.PI);
    const speedCategory = fwiToSpeedCategory(prediction.fwi_pred);
    const windDirection = prediction.dir_pred * 45;
    const speedText = {0: '낮음', 1: '중간', 2: '높음'};
    const windText = windDirection <= -999.0 ? 'N/A' : `${windDirection.toFixed(1)}°`;

    const content = `<div class="info-overlay"><h4>예측 정보</h4><ul>` +
        `<li><strong>예상 피해 면적:</strong> ${area_ha.toFixed(2)} ha <span class="confidence-range">(범위: ${prediction.area_pred_low.toFixed(2)} - ${prediction.area_pred_high.toFixed(2)} ha)</span></li>` +
        `<li><strong>예상 확산 거리:</strong> ${distance_m.toFixed(1)} m</li>` +
        `<li><strong>주요 확산 방향:</strong> ${windText}</li>` +
        `<li><strong>예상 확산 속도:</strong> ${speedText[speedCategory] || '알 수 없음'} (FWI: ${prediction.fwi_pred.toFixed(2)})</li>` +
        `</ul></div>`;
    return new kakao.maps.CustomOverlay({ map, position, content, yAnchor: 1.1, xAnchor: 0.5 });
}

function displayConfidenceMetrics(prediction) {
    const container = document.getElementById("confidenceMetrics");
    if (!container) return;

    const metricsHTML = `
        <div class="metric-item">
            <h4>면적 예측 (Area Prediction)</h4>
            <p><strong>가장 가능성 높은 예측 (Median):</strong> ${prediction.area_pred_median.toFixed(2)} ha</p>
            <p><strong>예측 신뢰 구간 (Confidence Range):</strong> ${prediction.area_pred_low.toFixed(2)} - ${prediction.area_pred_high.toFixed(2)} ha</p>
            <small>모델은 80% 확률로 실제 피해 면적이 이 범위 내에 있을 것으로 예측합니다.</small>
        </div>
        <div class="metric-item">
            <h4>산불위험지수 (FWI)</h4>
            <p><strong>예측된 위험 지수:</strong> ${prediction.fwi_pred.toFixed(2)}</p>
            <small>날씨가 화재에 얼마나 유리한지를 나타내는 종합 점수입니다.</small>
        </div>
        <div class="metric-item">
            <h4>주요 확산 방향 (Direction)</h4>
            <p><strong>예측 방향:</strong> ${prediction.dir_pred * 45}°</p>
            <small>8방위 중 가장 가능성이 높은 바람의 방향입니다.</small>
        </div>
        <div class="metric-item">
            <h4>예상 확산 거리 (Distance)</h4>
            <p><strong>예측 반경:</strong> ${prediction.distance_pred.toFixed(2)} m</p>
            <small>화재 중심으로부터의 평균 최종 확산 반경에 대한 독립적인 예측입니다.</small>
        </div>
    `;
    container.innerHTML = metricsHTML;
}

function getEndpoint(lat, lng, bearing, distance) {
    const R = 6378137;
    const brng = toRadians(bearing);
    const lat1 = toRadians(lat);
    const lon1 = toRadians(lng);
    const lat2 = Math.asin(Math.sin(lat1) * Math.cos(distance / R) + Math.cos(lat1) * Math.sin(distance / R) * Math.cos(brng));
    const lon2 = lon1 + Math.atan2(Math.sin(brng) * Math.sin(distance / R) * Math.cos(lat1), Math.cos(distance / R) - Math.sin(lat1) * Math.sin(lat2));
    return { lat: toDegrees(lat2), lng: toDegrees(lon2) };
}

function toRadians(degrees) { return degrees * Math.PI / 180; }
function toDegrees(radians) { return radians * 180 / Math.PI; }

function formatDataForDistanceChart(predicted_area_ha) {
    const labels = [], data = [];
    for (let h = 3; h <= 12; h += 3) {
        labels.push(`${h}시간 후`);
        const areaAtH = calculateGrowthWithSCurve(h, predicted_area_ha);
        const radiusAtH = Math.sqrt(areaAtH * 10000 / Math.PI);
        data.push(radiusAtH / 1000);
    }
    return { labels, datasets: [{ label: `예상 확산 거리(km)`, data, borderColor: `hsl(15, 70%, 50%)`, fill: false }] };
}

function setupHamburgerMenu() {
    const hamburger = document.getElementById("hamburgerBtn");
    const sideMenu = document.getElementById("sideMenu");
    hamburger.addEventListener("click", () => {
        sideMenu.classList.toggle("active");
        hamburger.classList.toggle("active");
        if (mapInstance) {
            setTimeout(() => mapInstance.relayout(), 350); 
        }
    });
}

function setupHeaderScroll() {
    const header = document.querySelector("header");
    if (!header) return;
    let lastToggleY = window.scrollY;
    let ticking = false;
    window.addEventListener("scroll", () => {
        if (!ticking) {
            window.requestAnimationFrame(() => {
                if (Math.abs(window.scrollY - lastToggleY) >= 120) {
                    if (window.scrollY > lastToggleY && window.scrollY > 150) {
                        header.classList.add("hide");
                    } else {
                        header.classList.remove("hide");
                    }
                    lastToggleY = window.scrollY;
                }
                ticking = false;
            });
            ticking = true;
        }
    });
}