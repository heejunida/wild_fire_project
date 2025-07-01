let currentPage = 1;
let rowsPerPage = 12; // 기본값은 전체 보기
let fullData = [];
let marker = null;

kakao.maps.load(() => {
  const map = new kakao.maps.Map(document.getElementById("map"), {
    center: new kakao.maps.LatLng(37.8228, 128.1555),
    level: 9
  });

  const geocoder = new kakao.maps.services.Geocoder();
  const mapDiv = document.getElementById("map");
  mapDiv.style.cursor = "pointer";

  renderPaginatedTableRows([]);

  // ✅ 검색 버튼 클릭
  document.getElementById("searchBtn").addEventListener("click", async () => {
    const selected = document.getElementById("regionSelect").value;
    if (!selected) return alert("지역을 먼저 선택하세요!");

    try {
      const response = await fetch("../json/mock_forest_locations.json");
      const data = await response.json();
      const locations = data[selected];

      if (!locations || locations.length === 0) {
        renderPaginatedTableRows([]);
        alert("해당 지역의 산림 정보가 없습니다.");
        return;
      }

      const mockData = locations.map(loc => ({
        location: loc.location,
        area: "-",
        danger: "-"
      }));

      renderPaginatedTableRows(mockData);
    } catch (err) {
      console.error("데이터 로딩 실패", err);
      alert("산림 데이터를 불러오는 데 문제가 발생했습니다.");
    }
  });

  // ✅ 지도 클릭 시
  kakao.maps.event.addListener(map, 'click', mouseEvent => {
    const latlng = mouseEvent.latLng;

    if (marker) marker.setMap(null);
    marker = new kakao.maps.Marker({ position: latlng, map });

    geocoder.coord2Address(latlng.getLng(), latlng.getLat(), async (result, status) => {
      if (status === kakao.maps.services.Status.OK) {
        const fullAddr = result[0].address.address_name;
        const regionList = ["춘천시", "원주시", "강릉시", "동해시", "태백시", "속초시", "삼척시", "홍천군", "횡성군", "영월군", "평창군", "정선군", "철원군", "화천군", "양구군", "인제군", "고성군", "양양군"];
        const region = regionList.find(r => fullAddr.includes(r));

        if (region) {
          document.getElementById("regionSelect").value = region;

          try {
            const response = await fetch("../json/mock_forest_locations.json");
            const data = await response.json();
            const locations = data[region];

            if (!locations || locations.length === 0) {
              renderPaginatedTableRows([]);
              alert("해당 지역의 산림 정보가 없습니다.");
              return;
            }

            const mockData = locations.map(loc => ({
              location: loc.location,
              area: "-",
              danger: "-"
            }));

            renderPaginatedTableRows(mockData);
          } catch (err) {
            console.error("지도 클릭 후 fetch 실패", err);
            alert("산림 데이터를 불러오는 데 문제가 발생했습니다.");
          }
        }
      }
    });
  });

  // ✅ 출력 개수 변경
document.getElementById("resultCount").addEventListener("change", () => {
  const val = document.getElementById("resultCount").value;

  // ✅ 숫자가 아닌 경우 12로 기본 설정
  rowsPerPage = isNaN(parseInt(val)) ? 12 : parseInt(val);

  currentPage = 1;
  renderPaginatedTableRows(fullData, 1);
});
  // ✅ 초기화 버튼
  document.getElementById("resetBtn").addEventListener("click", () => {
    document.getElementById("regionSelect").value = "default";
    document.getElementById("resultCount").value = "default";
    rowsPerPage = Infinity;

    if (marker) {
      marker.setMap(null);
      marker = null;
    }

    renderPaginatedTableRows([]);
    document.querySelector(".pagination").innerHTML = "";
  });
});

// ✅ 테이블 출력
function renderPaginatedTableRows(data, page = 1) {
  fullData = data;
  currentPage = page;

  const tbody = document.getElementById("resultBody");
  tbody.innerHTML = "";

  const totalItems = data.length;

  // ✅ rowsPerPage가 12 이상인 경우만 페이지네이션, 나머지는 고정 출력
  if (document.getElementById("resultCount").value !== "default") {
    // 무조건 설정한 수만큼만 출력
    const limitedData = data.slice(0, rowsPerPage);
    limitedData.forEach(row => {
      const location = row.location.replace("강원도 ", "");
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${location}</td>
        <td>${row.area}</td>
        <td class="${row.danger === "높음" ? "danger" : ""}">${row.danger}</td>
      `;
      tbody.appendChild(tr);
    });

    // 테이블 줄 고정
    for (let i = limitedData.length; i < 12; i++) {
      const tr = document.createElement("tr");
      tr.innerHTML = `<td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td>`;
      tbody.appendChild(tr);
    }

    // ✅ 페이지네이션 제거
    document.querySelector(".pagination").innerHTML = "";
    return;
  }

  // 👉 디폴트 상태일 때만 페이지네이션
  const start = (page - 1) * 12;
  const end = start + 12;
  const currentData = data.slice(start, end);

  currentData.forEach(row => {
    const location = row.location.replace("강원도 ", "");
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${location}</td>
      <td>${row.area}</td>
      <td class="${row.danger === "높음" ? "danger" : ""}">${row.danger}</td>
    `;
    tbody.appendChild(tr);
  });

  for (let i = currentData.length; i < 12; i++) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td>`;
    tbody.appendChild(tr);
  }

  renderPagination(totalItems);
}

// ✅ 페이지네이션
function renderPagination(totalItems) {
  const pagination = document.querySelector(".pagination");
  pagination.innerHTML = "";

  // ❗ rowsPerPage가 Infinity일 경우 페이지네이션 없음
  if (rowsPerPage === Infinity || totalItems <= 12) return;

  const totalPages = Math.ceil(totalItems / rowsPerPage);
  if (totalPages <= 1) return;

  const prevBtn = document.createElement("button");
  prevBtn.textContent = "«";
  prevBtn.disabled = currentPage === 1;
  prevBtn.addEventListener("click", () => renderPaginatedTableRows(fullData, currentPage - 1));
  pagination.appendChild(prevBtn);

  for (let i = 1; i <= totalPages; i++) {
    const btn = document.createElement("button");
    btn.textContent = i;
    if (i === currentPage) btn.classList.add("active");
    btn.addEventListener("click", () => renderPaginatedTableRows(fullData, i));
    pagination.appendChild(btn);
  }

  const nextBtn = document.createElement("button");
  nextBtn.textContent = "»";
  nextBtn.disabled = currentPage === totalPages;
  nextBtn.addEventListener("click", () => renderPaginatedTableRows(fullData, currentPage + 1));
  pagination.appendChild(nextBtn);
}