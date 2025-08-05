<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" %>
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8"/>
    <title>산불 확산 예측 상세 정보</title>
    <link rel="stylesheet" href="css/detail.css"/>
</head>
<script>
    window.loginUserId = "<%= session.getAttribute("user") != null ? session.getAttribute("user") : "" %>";
</script>
<body>
    <div id="hamburgerBtn">☰</div>
    <div id="sideMenu">
        <div class="side-menu">
            <ul>
                <li><a href="#map">🗺 확산 속도 및 범위</a></li>
                <li><a href="#distanceChart">📈 시간별 확산 변화</a></li>
                <li><a href="#modelConfidence">📊 모델 예측 신뢰도</a></li>
            </ul>
        </div>
    </div>
    <div class="wrapper">
        <header>
            <div class="logo" onclick="location.href='main.jsp'">SEED</div>
            <h1>산불 확산 예측 상세 정보</h1>
        </header>

        <div class="search-wrap">
            <div class="search-left">
                <div class="search-bar">
                    <div class="region-selection">
                        <label for="regionSelect">지역</label>
                        <select id="regionSelect">
                            <option value="">시/군/구 선택</option>
                            <option value="춘천시">춘천시</option>
                            <option value="원주시">원주시</option>
                            <option value="강릉시">강릉시</option>
                            <option value="동해시">동해시</option>
                            <option value="태백시">태백시</option>
                            <option value="속초시">속초시</option>
                            <option value="삼척시">삼척시</option>
                            <option value="홍천군">홍천군</option>
                            <option value="횡성군">횡성군</option>
                            <option value="영월군">영월군</option>
                            <option value="평창군">평창군</option>
                            <option value="정선군">정선군</option>
                            <option value="철원군">철원군</option>
                            <option value="화천군">화천군</option>
                            <option value="양구군">양구군</option>
                            <option value="인제군">인제군</option>
                            <option value="고성군">고성군</option>
                            <option value="양양군">양양군</option>
                        </select>
                        <button id="selectRegionBtn">지역으로 이동</button>
                        <button id="resetBtn">초기화</button>
                    </div>
                    
                    <div class="prediction-controls" style="display: none;">
                        <label for="durationSelect">예측 기간</label>
                        <select id="durationSelect">
                            <option value="3">3시간</option>
                            <option value="6">6시간</option>
                            <option value="9">9시간</option>
                            <option value="12" selected>12시간</option>
                        </select>
                        <span id="predictedDurationDisplay" style="margin-left: 10px; font-weight: bold;"></span>
                    </div>
                </div>
                <div class="map-container">
                    <h3>산불 확산 속도 및 범위</h3>
                    <div id="map"></div>
                </div>
            </div>
            <div class="chart-area">
                <div class="chart-container">
                    <h3>시간별 확산 변화</h3>
                    <canvas id="distanceChart" width="600" height="300"></canvas>
                </div>
            </div>
        </div>

        <section id="modelConfidence" class="confidence-section">
            <h3>모델 예측 신뢰도</h3>
            <div id="confidenceMetrics" class="metrics-container">
                <!-- Populated by detail.js -->
            </div>
        </section>

    </div>
    <div class = "blank"></div>
    <footer id="siteFooter" class="site-footer">
        <div class="footer-content">
            <p>© 2025 SEED. All rights reserved.</p>
        </div>
    </footer>

    <!-- Loading Overlay -->
    <div id="loadingOverlay" class="loading-overlay">
        <div class="loading-spinner"></div>
        <p>예측 데이터를 불러오는 중...</p>
        <button id="cancelPredictionBtn" class="cancel-button">예측 중지</button>
    </div>

    <script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey=e474c3379b43247007872a8baf1b48ce"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="js/chart.js"></script>
    <script src="js/detail.js"></script>
</body>
</html>
