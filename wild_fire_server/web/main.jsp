<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" %>
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <title>산불 확산속도 예측 서비스</title>
    <link rel="stylesheet" href="css/main.css"/>
</head>
<body>
<div class="wrapper">
    <header>
        <div class="logo" onclick="location.href='main.jsp'">SEED</div>
        <div class="nav">
            <div class="dropdown">
                <button id="mainDropdownBtn" class="dropdown-btn">산불 확산 예측 ▼</button>
                <div id="mainDropdownContent" class="dropdown-content">
                    <a href="aboutUs.html">이슈 인사이트</a>
                    <a href="detail.jsp">예측 결과 분석</a>
                </div>
            </div>
        </div>
        <div class="login-icon" style="position:relative;">
            <%
                if (session.getAttribute("user") != null) {
            %>
            <!-- 로그인 된 경우: 아이콘 + 드롭다운 메뉴 -->
            <img src="https://cdn-icons-png.flaticon.com/512/847/847969.png" id="userMenuBtn" alt="user"
                 style="cursor:pointer;">
            <div id="userDropdown" class="user-dropdown"
                 style="display:none; position:absolute; right:0; top:40px; background:#fff; border:1px solid #eee; border-radius:12px; box-shadow:0 4px 16px rgba(0,0,0,0.10); min-width:140px; z-index:1000;">
                <button class="dropdown-item" onclick="openModal('pwModal')"
                        style="width:100%; background:none; border:none; text-align:left; padding:12px 16px; font-size:15px;">
                    비밀번호 변경
                </button>
                <button class="dropdown-item" onclick="handleLogout()"
                        style="width:100%; background:none; border:none; text-align:left; padding:12px 16px; font-size:15px;">
                    로그아웃
                </button>
            </div>
            <%
            } else {
            %>
            <!-- 로그인 안 된 경우: 클릭시 로그인 모달 열기 -->
            <img src="https://cdn-icons-png.flaticon.com/512/847/847969.png" onclick="openModal('loginModal')"
                 alt="login" style="cursor:pointer;">
            <%
                }
            %>
        </div>

        <!-- 이 부분은 body 제일 아래쪽, 혹은 어디든 한 번만! -->
        <div id="pwModal" class="modal hidden">
            <div class="modal-content">
                <span class="close" onclick="closeModal('pwModal')">&times;</span>
                <h2>비밀번호 변경</h2>
                <div class="msg" id="pwMsg"></div>
                <input type="password" id="modalOldPw" placeholder="현재 비밀번호">
                <input type="password" id="modalNewPw" placeholder="새 비밀번호" style="margin-top:10px;">
                <input type="password" id="modalNewPw2" placeholder="새 비밀번호 확인" style="margin-top:10px;">
                <button onclick="handleModalPwChange()">변경하기</button>
                <span id="loginUserId" style="display:none;"><%= session.getAttribute("user") %></span>
                <button onclick="closeModal('pwModal')"
                        style="position:absolute; top:12px; right:12px; background:none; border:none; font-size:18px;">
                    &times;
                </button>
            </div>
        </div>
    </header>

    <main>
        <section class="slider-section">
            <div class="slider-container">
                <div class="slider-overlay center-style">
                    <h2>산불의 확산, 이제는 예측할 수 있습니다.</h2>
                    <p>강원도를 중심으로 산불 확산 규모와 속도를 미리 감지합니다.</p>
                    <button onclick="location.href='detail.jsp'">산불 예측하러 가기</button>
                </div>

                <div class="slider-image">
                    <img class="slider-slide active" src="img/forest1.jpg" alt="Forest 1">
                    <img class="slider-slide" src="img/forest2.jpg" alt="Forest 2">
                    <img class="slider-slide" src="img/forest3.jpg" alt="Forest 3">
                    <img class="slider-slide" src="img/forest4.jpg" alt="Forest 4">
                </div>
            </div>
        </section>

        <section class="hot-zones">
            <h2>🔥 현재 위험도가 높은 지역</h2>
            <div class="zone-cards">
                <div class="zone-card danger">
                    <h3>강릉시</h3>
                    <p>위험도: <span>높음</span></p>
                    <p>예상 피해 면적: 0.6 ha</p>
                </div>
                <div class="zone-card warning">
                    <h3>삼척시</h3>
                    <p>위험도: <span>보통</span></p>
                    <p>예상 피해 면적: 0.2 ha</p>
                </div>
                <div class="zone-card danger">
                    <h3>동해시</h3>
                    <p>위험도: <span>높음</span></p>
                    <p>예상 피해 면적: 0.4 ha</p>
                </div>
            </div>
        </section>
    </main>
</div>

<footer id="siteFooter" class="site-footer">
    <div class="footer-content">
        <p>© 2025 SEED. All rights reserved.</p>
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
                    <input type="text" id="loginId" required/>
                    <label for="loginId">아이디</label>
                </div>
                <div class="floating-input">
                    <input type="password" id="loginPw" required/>
                    <label for="loginPw">비밀번호</label>
                </div>
                <button onclick="handleLogin()">로그인</button>
                <p class="switch-msg">계정이 없으신가요? <span onclick="switchForm('signup')">회원가입 하기</span></p>
                <p class="find-msg">
                    <span class="find" onclick="switchForm('findId')">아이디 찾기</span> /
                    <span class="find" onclick="switchForm('findPw')">비밀번호 찾기</span>
                </p>
            </div>
        </div>
            <div id="findIdForm" class="form-section hidden">
                <h2>아이디 찾기</h2>
                <input id="findIdName" type="text" placeholder="이름">
                <button onclick="handleFindId()">아이디 찾기</button>
                <div id="findIdResult" class="msg"></div>
                <div class="switch-msg">
                    <span onclick="switchForm('login')">로그인 화면으로 돌아가기</span>
                </div>
            </div>

            <!-- 비밀번호 찾기 폼 -->
            <div id="findPwForm" class="form-section hidden">
                <h2>비밀번호 찾기</h2>
                <input id="findPwId" type="text" placeholder="아이디">
                <input id="findPwName" type="text" placeholder="이름">
                <button onclick="handleFindPw()">본인 인증</button>
                <div id="findPwResult" class="msg"></div>
                <div class="switch-msg">
                    <span onclick="switchForm('login')">로그인 화면으로 돌아가기</span>
                </div>
            </div>
            <div id="pwResetForm" class="form-section hidden">
                <h2>새 비밀번호 설정</h2>
                <input id="pwResetUserId" type="hidden">
                <input id="resetPw1" type="password" placeholder="새 비밀번호">
                <input id="resetPw2" type="password" placeholder="새 비밀번호 확인">
                <button onclick="handlePwResetWithoutOldPw()">비밀번호 재설정</button>
                <div id="pwResetMsg" class="msg"></div>
                <div class="switch-msg">
                    <span onclick="switchForm('login')">로그인 화면으로 돌아가기</span>
                </div>
            </div>

        <!-- 회원가입 폼 -->
        <div id="signupForm" class="form-section hidden">
            <h2>회원가입</h2>
            <div class="modal-form">
                <div class="floating-input">
                    <input type="text" id="signupName" required/>
                    <label for="signupName">이름</label>
                </div>
                <div class="floating-input">
                    <input type="text" id="signupId" required/>
                    <label for="signupId">아이디</label>
                </div>
                <div class="floating-input">
                    <input type="password" id="signupPw" required/>
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