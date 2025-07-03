<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" %>
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8"/>
    <title>산불 확산 예측 상세 정보</title>
    <link rel="stylesheet" href="css/detail.css"/>
    <script defer src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script defer
            src="https://dapi.kakao.com/v2/maps/sdk.js?appkey=e474c3379b43247007872a8baf1b48ce&autoload=false"></script>
    <script defer src="js/detail.js"></script>
    <script defer src="js/chart.js"></script>
</head>
<body>
<div id="hamburgerBtn">☰</div>
<div id="sideMenu">
    <div class="side-menu">
        <ul>
            <li><a href="#map">🗺 확산 속도 및 범위</a></li>
            <li><a href="#lineChart">📈 시간별 거리 변화</a></li>
            <li><a href="#barChart">📊 확산 속도 등급 분포</a></li>
        </ul>
    </div>
</div>
<div class="wrapper">
    <header>
        <div class="logo" onclick="location.href='main.jsp'">SEED</div>
        <h1>산불 확산 예측 상세 정보</h1>
    </header>

    <!-- 🔍 지도 + 차트 나란히 배치 -->
    <div class="search-wrap">
        <!-- 왼쪽: 지역 선택 + 지도 -->
        <div class="search-left">
            <div class="search-bar">
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
                <button id="searchBtn">검색</button>
                <button id="resetBtn">초기화</button>
            </div>

            <div class="map-container">
                <h3>산불 확산 속도 및 범위</h3>
                <div id="map"></div>
            </div>
        </div>

        <!-- 오른쪽: 선형 차트 -->
        <div class="chart-area">
            <div class="chart-container">
                <h3>시간별 확산 거리 변화</h3>
                <canvas id="distanceChart" width="600" height="300"></canvas>
            </div>
        </div>
    </div>

    <!-- 하단: 비교 차트 -->
    <section class="compare-area">
        <h3>지역별 확산 속도 등급별 분포</h3>
        <div id="selectedRegions" class="selected-regions"></div>
        <canvas id="speedLevelChart" width="600" height="300"></canvas>
        <!-- 선택된 지역 태그 동적으로 삽입됨 -->
    </section>
</div>
<div class = "blank"></div>
    <footer id="siteFooter" class="site-footer">
        <div class="footer-content">
            <p>© 2025 SEED. All rights reserved.</p>
        </div>
    </footer>
</body>
</html>