let map;
let markers = [];
const selectedRegions = [];

function saveNasaDataToCSV(data, lat, lng) {
  const parameters = Object.keys(data); // T2M, RH2M, ...
  const timeKeys = Object.keys(data[parameters[0]]); // 날짜 시간 키들 (예: 2025070400, 2025070401...)

  let csv = "datetime,latitude,longitude," + parameters.join(",") + "\n";

  timeKeys.forEach(datetime => {
    const row = [datetime, lat, lng];
    parameters.forEach(param => {
      const value = data[param][datetime] ?? "";
      row.push(value);
    });
    csv += row.join(",") + "\n";
  });

  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);

  const link = document.createElement("a");
  link.href = url;
  link.download = `nasa_power_${lat.toFixed(3)}_${lng.toFixed(3)}.csv`;
  link.style.display = "none";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

kakao.maps.load(() => {

  let clickMarker = null;
  map = new kakao.maps.Map(document.getElementById("map"), {
    center: new kakao.maps.LatLng(37.8228, 128.1555),
    level: 9
  });

  // ✅ 지도 클릭 시 위도/경도 출력
  kakao.maps.event.addListener(map, 'click', mouseEvent => {
    const latlng = mouseEvent.latLng;
    const lat = latlng.getLat();
    const lng = latlng.getLng();

    console.log("🛰️ 지도 클릭 위치 위도:", lat, "경도:", lng);

    fetchNasaData(lat, lng);

    if (clickMarker) {
      clickMarker.setMap(null);
    }
    // 새 마커 생성
    clickMarker = new kakao.maps.Marker({
      map,
      position: latlng
    });
  });

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

async function fetchNasaData(lat, lng) {
  const today = new Date();
  today.setDate(today.getDate() - 3);  // 3일 전
  const yyyymmdd = today.toISOString().slice(0, 10).replace(/-/g, "");
  const url = `https://power.larc.nasa.gov/api/temporal/hourly/point?parameters=T2M,RH2M,WS2M,WD2M,PRECTOTCORR,PS,ALLSKY_SFC_SW_DWN&community=RE&longitude=${lng}&latitude=${lat}&start=${yyyymmdd}&end=${yyyymmdd}&format=CSV`;

  try {
    const res = await fetch(url);
    const json = await res.json();
    const hourData = json.properties.parameter;

    console.log("🌤️ NASA POWER 시간별 데이터 (hourly):", hourData);

    // 📁 CSV 저장
    saveNasaDataToCSV(hourData, lat, lng);
  } catch (err) {
    console.error("❌ NASA POWER API 호출 실패:", err);
  }
}