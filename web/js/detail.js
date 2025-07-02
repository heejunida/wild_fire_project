document.addEventListener("DOMContentLoaded", () => {
  const sido = document.getElementById("sido");
  const sigungu = document.getElementById("sigungu");
  const searchBtn = document.getElementById("searchBtn");
  const resetBtn = document.getElementById("resetBtn");

  const mapContainer = document.getElementById("map");
  const lineChartCanvas = document.getElementById("lineChart");
  const barChartCanvas = document.getElementById("barChart");
  const compareList = document.getElementById("compareList");

  // 지역 선택 → 하위 군/구 연동 (샘플)
  sido.addEventListener("change", () => {
    sigungu.innerHTML = "<option>군/구 선택</option>";
    if (sido.value === "춘천시") {
      sigungu.innerHTML += "<option>동면</option><option>신북읍</option>";
    }
    // 실제는 서버나 지역 DB 기반으로 동적 구성
  });

  // 검색 버튼 클릭
  searchBtn.addEventListener("click", () => {
    const region = `${sido.value} ${sigungu.value}`;
    if (!sido.value || !sigungu.value) {
      alert("지역을 선택해주세요.");
      return;
    }

    // 1. 지도에 마커/폴리곤 + 등급 표시
    // 2. 차트 업데이트
    // 3. compare 리스트에 지역 추가
    addRegionToCompare(region);
    updateLineChart(region);
    updateBarChart(); // compare 리스트 기준
  });

  // 초기화 버튼
  resetBtn.addEventListener("click", () => {
    compareList.innerHTML = "";
    lineChartCanvas.getContext('2d').clearRect(0, 0, lineChartCanvas.width, lineChartCanvas.height);
    barChartCanvas.getContext('2d').clearRect(0, 0, barChartCanvas.width, barChartCanvas.height);
  });

  // 지역 태그 추가
  function addRegionToCompare(region) {
    if (compareList.children.length >= 5) {
      alert("비교 지역은 최대 5개까지 가능합니다.");
      return;
    }

    const tag = document.createElement("div");
    tag.className = "tag";
    tag.innerHTML = `${region}<span class="remove">✕</span>`;
    tag.querySelector(".remove").addEventListener("click", () => {
      tag.remove();
      updateBarChart();
    });

    compareList.appendChild(tag);
  }

  // 차트 업데이트 함수 (샘플)
  function updateLineChart(region) {
    // 실제 예측 거리 데이터를 fetch → 차트에 반영
  }

  function updateBarChart() {
    // compareList.children 기준으로 지역별 속도 등급 분포 계산 후 Chart.js로 시각화
  }

});