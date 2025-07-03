<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <title>실시간 산불 확산 예측 정보</title>
  <link rel="stylesheet" href="css/search.css" />
  <script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey=e474c3379b43247007872a8baf1b48ce&libraries=services&autoload=false"></script>
</head>
<body>
<div class="wrapper">
  <header>
    <div class="logo" onclick="location.href='main.jsp'">SEED</div>
    <h1>실시간 산불 확산 예측 정보</h1>
  </header>
  <div class="search-wrap">
    <!-- 왼쪽: 검색 및 결과 표 -->
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

        <select id="resultCount">
          <option value="default">-</option>
          <option value="5">5</option>
          <option value="10">10</option>
          <option value="15">15</option>
        </select>
      </div>

      <div class="result-table">
        <div class="result-header">
          <span>검색 결과</span>
          <span id="tooltip">?</span>
        </div>
        <table>
          <thead>
            <tr>
              <th>발생지점</th>
              <th>예상 피해면적</th>
              <th>위험 등급</th>
            </tr>
          </thead>
          <tbody id="resultBody">
            
          </tbody>
        </table>
      </div>
      <div class="pagination"></div>
    </div>

    <!-- 오른쪽: 지도 -->
    <div class="search-map">
      <div id="map"></div>
    </div>
  </div>
</div>
  <footer id="siteFooter" class="site-footer">
    <div class="footer-content">
      <p>© 2025 SEED. All rights reserved.</p>
    </div>
  </footer>
<script src="js/search.js"></script>
</body>
</html>