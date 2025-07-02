<%@ page language="java" contentType="text/html; charset=UTF-8" %>
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <title>산불 확산 예측 상세 페이지</title>
  <link rel="stylesheet" href="css/detail.css">
  <script defer src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <script defer src="predictDetail.js" type="module"></script>
</head>
<body>
  <main class="container">

    <!-- 지역 선택 -->
    <section class="region-select">
      <label for="sido">지역</label>
      <select id="sido">
        <option value="">시 선택</option>
        <option value="강릉시">강릉시</option>
        <option value="춘천시">춘천시</option>
        <!-- ... -->
      </select>
      <select id="sigungu">
        <option value="">군/구 선택</option>
      </select>
      <button id="searchBtn">검색</button>
      <button id="resetBtn">초기화</button>
    </section>

    <!-- 지도 + 시간별 차트 -->
    <section class="content-area">
      <div class="map-container">
        <h3>산불 확산 속도 및 범위</h3>
        <div id="map" class="map-box"></div>
      </div>

      <div class="chart-container">
        <h3>시간별 거리 변화</h3>
        <canvas id="lineChart"></canvas>
      </div>
    </section>

    <!-- 하단 비교 지역 바 + 그룹 막대 차트 -->
    <section class="compare-area">
      <div id="compareList" class="compare-tags">
        <!-- 지역 태그가 여기에 동적으로 들어감 -->
      </div>
      <canvas id="barChart"></canvas>
    </section>

  </main>
</body>
</html>