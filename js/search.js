// 예시 위치 좌표 (시군구명: 위도, 경도)
const regionCoordinates = {
  '강릉시': { lat: 37.7519, lng: 128.8761 },
  '삼척시': { lat: 37.4458, lng: 129.1651 },
  '동해시': { lat: 37.5245, lng: 129.114 },
};

let marker;

const container = document.getElementById('map');
const options = {
  center: new kakao.maps.LatLng(37.5, 128), // 강원도 중심
  level: 9
};

const map = new kakao.maps.Map(container, options);

// 지도 초기화
function initMap() {
  map = new kakao.maps.Map(document.getElementById('map'), {
    center: new kakao.maps.LatLng(37.7, 128.3), // 강원도 중심
    level: 9
  });
}

// 지도 위치 이동 및 마커 표시
function moveToRegion(region) {
  const coord = regionCoordinates[region];
  if (!coord) return;

  const moveLatLng = new kakao.maps.LatLng(coord.lat, coord.lng);
  map.setCenter(moveLatLng);
  map.setLevel(6);

  if (marker) marker.setMap(null);
  marker = new kakao.maps.Marker({
    position: moveLatLng,
    map: map
  });
}

// 검색 버튼 클릭 시 결과 표시
document.getElementById('searchBtn').addEventListener('click', () => {
  const region = document.getElementById('regionSelect').value;
  if (!region) {
    alert("지역을 먼저 선택해 주세요");
    return;
  }

  moveToRegion(region);

  // 예시 데이터 삽입
  const tbody = document.querySelector('#resultTable tbody');
  tbody.innerHTML = `
    <tr>
      <td>${region} 토성면</td>
      <td>14.3</td>
      <td class="danger">높음</td>
    </tr>
  `;

  document.querySelector('.pagination').style.display = 'block';
});

// 초기화
document.getElementById('resetBtn').addEventListener('click', () => {
  document.getElementById('regionSelect').value = "";
  const tbody = document.querySelector('#resultTable tbody');
  tbody.innerHTML = "";
  map.setCenter(new kakao.maps.LatLng(37.7, 128.3));
  map.setLevel(9);
  if (marker) marker.setMap(null);
  document.querySelector('.pagination').style.display = 'none';
});

// 도움말 아이콘
document.getElementById('helpIcon').addEventListener('click', () => {
  alert("각 항목은 예측된 산불 발생 위치, 예상 피해면적, 위험 등급을 나타냅니다.");
});

// 페이지 로드시 지도 초기화
window.onload = initMap;