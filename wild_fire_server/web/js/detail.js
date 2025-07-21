let map;
let markers = [];
const selectedRegions = [];
let clickMarker = null; // 전역으로 선언

kakao.maps.load(() => {
  map = new kakao.maps.Map(document.getElementById("map"), {
    center: new kakao.maps.LatLng(37.8228, 128.1555),
    level: 9
  });

  kakao.maps.event.addListener(map, 'click', async mouseEvent => {
    const latlng = mouseEvent.latLng;
    const lat = latlng.getLat();
    const lon = latlng.getLng();

    // 이전에 표시된 마커와 폴리곤이 있다면 제거
    if (clickMarker) {
        clickMarker.setMap(null);
    }
    if (window.firePolygon) {
        window.firePolygon.setMap(null);
    }

    // 클릭한 위치에 마커 표시
    clickMarker = new kakao.maps.Marker({
        position: latlng,
        map: map
    });

    try {
        // FirePredictController 서블릿 호출
        const response = await fetch(`/fire-predict?lat=${lat}&lon=${lon}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const predictionData = await response.json();

        // GeoJSON 데이터를 Kakao Map 폴리곤으로 변환하여 지도에 표시
        displayFirePrediction(predictionData);

    } catch (error) {
        console.error("Error fetching fire prediction:", error);
        alert("산불 예측 데이터를 가져오는 데 실패했습니다.");
    }
});

// GeoJSON 데이터를 받아 지도에 폴리곤으로 표시하는 함수
function displayFirePrediction(geoJsonData) {
    if (window.firePolygon) {
        window.firePolygon.setMap(null);
    }

    // GeoJSON의 coordinates를 Kakao.maps.LatLng 객체 배열로 변환
    const path = geoJsonData.features[0].geometry.coordinates[0].map(coord => new kakao.maps.LatLng(coord[1], coord[0]));

    // 폴리곤 생성
    window.firePolygon = new kakao.maps.Polygon({
        path: path,
        strokeWeight: 3,
        strokeColor: '#FF0000',
        strokeOpacity: 0.8,
        fillColor: '#FF0000',
        fillOpacity: 0.35
    });

    // 지도에 폴리곤 표시
    window.firePolygon.setMap(map);

    // 폴리곤이 보이도록 지도 범위 조정
    const bounds = new kakao.maps.LatLngBounds();
    path.forEach(point => bounds.extend(point));
    map.setBounds(bounds);
}

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
      const response = await fetch("../json/mock_forest_locations_with_coords.json");
      const data = await response.json();
      const locations = data[selected];

      if (!locations || locations.length === 0) {
        alert("해당 지역의 산림 정보가 없습니다.");
        return;
      }

      // 마커 초기화
      markers.forEach(m => m.setMap(null));
      markers = [];

      // 중심 좌표 이동
      const first = locations[0];
      map.setCenter(new kakao.maps.LatLng(first.lat, first.lng));

      // 마커 추가
      locations.forEach(loc => {
        const marker = new kakao.maps.Marker({
          map,
          position: new kakao.maps.LatLng(loc.lat, loc.lng),
          title: loc.location
        });
        markers.push(marker);
      });

      // 지역 태그 추가
      selectedRegions.push(selected);
      addRegionTag(selected);

      // 📊 차트 업데이트용 mock 데이터 (차후 서버 연동 시 교체)
      const mockLineData = generateMockLineData(selected);
      const mockBarData = generateMockBarData(selectedRegions);
      createDistanceChart(mockLineData);
      createSpeedLevelChart(mockBarData);

    } catch (err) {
      console.error("데이터 로딩 오류", err);
      alert("산림 데이터를 불러오는 데 실패했습니다.");
    }
  });

  document.getElementById("resetBtn").addEventListener("click", () => {
    markers.forEach(m => m.setMap(null));
    markers = [];
    selectedRegions.length = 0;
    document.getElementById("regionTags").innerHTML = "";
    createSpeedLevelChart({}); // 초기화
  });
});

// 📌 지역 태그 생성
function addRegionTag(region) {
  const container = document.getElementById("selectedRegions");

  // 최대 5개 제한
  if (selectedRegions.length > 4) {
    alert("최대 5개 지역까지만 선택할 수 있습니다.");
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

    const mockBarData = generateMockBarData(selectedRegions);
    createSpeedLevelChart(mockBarData);
  });
}

// ✅ 햄버거 메뉴 동작
document.addEventListener("DOMContentLoaded", () => {
  const hamburger = document.getElementById("hamburgerBtn");
  const sideMenu = document.getElementById("sideMenu");
  const closeBtn = document.getElementById("closeMenu");

  hamburger.addEventListener("click", () => {
    sideMenu.classList.toggle("active");
    hamburger.classList.toggle("active");
  });

  if (closeBtn) {
    closeBtn.addEventListener("click", () => {
      sideMenu.classList.remove("active");
    });
  }
});

// ✅ 스크롤 시 헤더 숨김/표시
const header = document.querySelector("header");
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

document.getElementById("resetBtn").addEventListener("click", () => {
  document.getElementById("regionSelect").value = "default";
  document.getElementById("resultCount").value = "default";
  maxDataCount = Infinity;

  if (marker) {
    marker.setMap(null);
    marker = null;
  }

  renderPaginatedTableRows([]);
  document.querySelector(".pagination").innerHTML = "";
});
