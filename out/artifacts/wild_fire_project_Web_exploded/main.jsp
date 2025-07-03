<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>산불 확산속도 예측 서비스</title>
  <link rel="stylesheet" href="css/main.css" />
</head>
<body>
  <header>
    <div class="logo" onclick="location.href='main.jsp'">SEED</div>
    <div class="nav">
      <div class="dropdown">
        <button class="dropdown-btn">산불 확산 예측 ▼</button>
        <div class="dropdown-content">
          <a href="search.jsp">예측할 지역 검색</a>
          <a href="detail.html">예측 결과 분석</a>
        </div>
      </div>
    </div>
<div class="login-icon">
<img src="https://cdn-icons-png.flaticon.com/512/847/847969.png" onclick="openModal('loginModal')" alt="login" />
  </div>
  </header>

  <main>
    <section class="slider-section">
     <div class="slider-container">
  <div class="slider-overlay center-style">
    <h2>산불의 확산, 이제는 예측할 수 있습니다.</h2>
    <p>강원도를 중심으로 산불 확산 규모와 속도를 미리 감지합니다.</p>
    <button>About US</button>
  </div>

  <div class="slider-image">
    <img class="slider-slide active" src="img/forest1.jpg" alt="Forest 1">
    <img class="slider-slide" src="img/forest2.jpg" alt="Forest 2">
    <img class="slider-slide" src="img/forest3.jpg" alt="Forest 3">
    <img class="slider-slide" src="img/forest4.jpg" alt="Forest 4">
  </div>
</div>
      </div>
      <div class="button-row">
        <button onclick="location.href='search.jsp'">예측 검색하기</button>
        <button onclick="location.href='detail.jsp'">상세 분석 보러가기</button>
      </div>
    </section>

    <section class="hot-zones">
      <h2>🔥 현재 위험도가 높은 지역</h2>
      <div class="zone-cards">
        <div class="zone-card danger">
          <h3>강릉시</h3>
          <p>위험도: <span>높음</span></p>
          <p>예상 피해 면적: 120 ha</p>
        </div>
        <div class="zone-card warning">
          <h3>삼척시</h3>
          <p>위험도: <span>보통</span></p>
          <p>예상 피해 면적: 85 ha</p>
        </div>
        <div class="zone-card danger">
          <h3>동해시</h3>
          <p>위험도: <span>높음</span></p>
          <p>예상 피해 면적: 103 ha</p>
        </div>
      </div>
    </section>
  </main>

  <footer class="site-footer">
    <div class="footer-content">
      <p><strong>SEED</strong> – 산불 예측 시각화 시스템</p>
      <p class="copyright">© 2025 SEED. All rights reserved.</p>
    </div>
  </footer>
<!-- ✅ 모달 구조: 로그인과 회원가입을 하나의 modal-content 안에서 switch -->
<div id="loginModal" class="modal hidden">
  <div class="modal-content fade-scale">
    <span class="close" onclick="closeModal('loginModal')">&times;</span>

    <!-- 로그인 폼 -->
    <div id="loginForm" class="form-section">
      <h2>로그인</h2>
      <div class="modal-form">
        <div class="floating-input">
          <input type="text" id="loginId" required />
          <label for="loginId">아이디</label>
        </div>
        <div class="floating-input">
          <input type="password" id="loginPw" required />
          <label for="loginPw">비밀번호</label>
        </div>
        <button onclick="handleLogin()">로그인</button>
        <p class="switch-msg">계정이 없으신가요? <span onclick="switchForm('signup')">회원가입 하기</span></p>
      </div>
    </div>

    <!-- 회원가입 폼 -->
    <div id="signupForm" class="form-section hidden">
      <h2>회원가입</h2>
      <div class="modal-form">
        <div class="floating-input">
          <input type="text" id="signupName" required />
          <label for="signupName">이름</label>
        </div>
        <div class="floating-input">
          <input type="text" id="signupId" required />
          <label for="signupId">아이디</label>
        </div>
        <div class="floating-input">
          <input type="password" id="signupPw" required />
          <label for="signupPw">비밀번호</label>
        </div>
        <button onclick="handleSignup()">회원가입</button>
        <p class="switch-msg">이미 계정이 있으신가요? <span onclick="switchForm('login')">로그인 하기</span></p>
      </div>
    </div>
  </div>
</div>
<script src="js/main.js"></script>
</body>
</html>