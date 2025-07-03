let map;
let markers = [];

kakao.maps.load(() => {
  map = new kakao.maps.Map(document.getElementById("map"), {
    center: new kakao.maps.LatLng(37.8228, 128.1555),
    level: 9
  });

  document.getElementById("searchBtn").addEventListener("click", async () => {
    const selected = document.getElementById("regionSelect").value;
    if (!selected) {
      alert("지역을 선택해주세요.");
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

      // 기존 마커 제거
      markers.forEach(m => m.setMap(null));
      markers = [];

      // 중심 좌표 재설정 (첫 번째 위치 기준)
      const first = locations[0];
      map.setCenter(new kakao.maps.LatLng(first.lat, first.lng));

      // 마커 생성
      locations.forEach(loc => {
        const marker = new kakao.maps.Marker({
          map,
          position: new kakao.maps.LatLng(loc.lat, loc.lng),
          title: loc.location
        });
        markers.push(marker);
      });

    } catch (err) {
      console.error("데이터 로딩 오류", err);
      alert("산림 데이터를 불러오는 데 실패했습니다.");
    }
  });
});
document.addEventListener("DOMContentLoaded", () => {
  const hamburger = document.getElementById("hamburgerBtn");
  const sideMenu = document.getElementById("sideMenu");
  const closeBtn = document.getElementById("closeMenu");

  // 햄버거 버튼 클릭 시 토글
  hamburger.addEventListener("click", () => {
    sideMenu.classList.toggle("active");
    hamburger.classList.toggle("active");
  });

  // 닫기 버튼은 그대로
  closeBtn.addEventListener("click", () => {
    sideMenu.classList.remove("active");
  });
});

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