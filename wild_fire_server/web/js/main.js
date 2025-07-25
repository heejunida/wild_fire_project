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

// 슬라이더 자동 전환
const slides = document.querySelectorAll('.slider-slide');
let current = 0;
let intervalId;

function showSlide(index) {
  slides.forEach((slide, i) => {
    slide.classList.toggle('active', i === index);
  });
}

function startSlider() {
  intervalId = setInterval(() => {
    current = (current + 1) % slides.length;
    showSlide(current);
  }, 7000);
}

document.querySelector('.slider-image')?.addEventListener('click', (e) => {
  clearInterval(intervalId);
  const containerWidth = e.currentTarget.offsetWidth;
  const clickX = e.offsetX;

  if (clickX < containerWidth / 2) {
    current = (current - 1 + slides.length) % slides.length;
  } else {
    current = (current + 1) % slides.length;
  }

  showSlide(current);
  startSlider();
});

startSlider();

// 모달 열기
function openModal(id) {
  const modal = document.getElementById(id);
  if (!modal) return;
  modal.classList.remove("hidden");   // 모달을 보이게
  setTimeout(() => {
    modal.classList.add("show");      // opacity/transform 효과
  }, 10);
}
function closeModal(id) {
  const modal = document.getElementById(id);
  if (!modal) return;
  modal.classList.remove("show");
  setTimeout(() => {
    modal.classList.add("hidden");
  }, 320); // transition 시간보다 살짝 길게!
}
function switchForm(mode) {
  // 모든 폼 id 배열
  const formIds = ["loginForm", "signupForm", "findIdForm", "findPwForm", "pwResetForm"];
  // 폼 DOM 객체로 가져오기
  const forms = formIds.map(id => document.getElementById(id));

  // 모두 숨김 + 트랜지션 초기화
  forms.forEach(form => {
    if (form) {
      form.classList.add("hidden");
      form.style.opacity = "0";
      form.style.transform = "scale(0.95)";
      form.style.filter = "blur(4px)";
    }
  });

  // 보여줄 폼, 포커스 타겟 매핑
  let showForm = null, focusId = null;
  if (mode === "signup") {
    showForm = document.getElementById("signupForm");
    focusId = "signupName";
  } else if (mode === "login") {
    showForm = document.getElementById("loginForm");
    focusId = "loginId";
  } else if (mode === "findId") {
    showForm = document.getElementById("findIdForm");
    focusId = "findIdName";
  } else if (mode === "findPw") {
    showForm = document.getElementById("findPwForm");
    focusId = "findPwId";
  } else if (mode === "pwReset") {
    showForm = document.getElementById("pwResetForm");
    focusId = "resetPw1";
  }

  // 선택한 폼만 애니메이션 보여주기
  if (showForm) {
    showForm.classList.remove("hidden");
    setTimeout(() => {
      showForm.style.transition = "all 0.4s ease";
      showForm.style.opacity = "1";
      showForm.style.transform = "scale(1)";
      showForm.style.filter = "blur(0)";
    }, 10);
    if (focusId) document.getElementById(focusId)?.focus();
  }
}
// 회원가입
async function handleSignup() {
  const name = document.getElementById("signupName").value;
  const id = document.getElementById("signupId").value;
  const pw = document.getElementById("signupPw").value;

  const res = await fetch("/signup", {
    method: "POST",
    headers: {"Content-Type": "application/x-www-form-urlencoded"},
    body: `user_name=${encodeURIComponent(name)}&user_id=${encodeURIComponent(id)}&user_pw=${encodeURIComponent(pw)}`
  });
  const data = await res.json();
  if (data.result === "success") {
    alert("회원가입 성공!");
    switchForm("login");
  } else {
    alert("회원가입 실패(중복 또는 오류)");
  }
}

// 로그인
async function handleLogin() {
  const id = document.getElementById("loginId").value;
  const pw = document.getElementById("loginPw").value;

  const res = await fetch("/login", {
    method: "POST",
    headers: {"Content-Type": "application/x-www-form-urlencoded"},
    body: `user_id=${encodeURIComponent(id)}&user_pw=${encodeURIComponent(pw)}`
  });
  const data = await res.json();
  if (data.result === "success") {
    alert("로그인 성공!");
    closeModal("loginModal");
    location.reload();
  } else {
    alert("아이디 또는 비밀번호가 일치하지 않습니다.");
  }
}
const userMenuBtn = document.getElementById("userMenuBtn");
const userDropdown = document.getElementById("userDropdown");
if (userMenuBtn && userDropdown) {
  userMenuBtn.onclick = function(e) {
    e.stopPropagation();
    userDropdown.style.display = (userDropdown.style.display === "block") ? "none" : "block";
  };
  document.addEventListener("click", function() {
    userDropdown.style.display = "none";
  });
}
const mainDropdownBtn = document.getElementById("mainDropdownBtn");
const mainDropdownContent = document.getElementById("mainDropdownContent");

if (mainDropdownBtn && mainDropdownContent) {
  mainDropdownBtn.onclick = function(e) {
    e.stopPropagation();
    const isOpen = mainDropdownContent.style.display === "block";
    // 모든 드롭다운 닫기 (유저 메뉴와 충돌 방지)
    document.querySelectorAll(".dropdown-content").forEach(el => el.style.display = "none");
    mainDropdownContent.style.display = isOpen ? "none" : "block";
  };

  mainDropdownContent.onclick = function(e) {
    e.stopPropagation();
  };
  // 바깥 클릭시 닫기 (유저 메뉴도 같이 닫음)
  document.addEventListener("click", function() {
    mainDropdownContent.style.display = "none";
  });
}
async function handleFindId() {
  const name = document.getElementById("findIdName").value.trim();
  const resultBox = document.getElementById("findIdResult");
  resultBox.innerText = "";

  if (!name) {
    resultBox.innerText = "이름을 입력하세요.";
    return;
  }

  // 서버로 이름만 보내서 아이디 찾기 요청
  const res = await fetch("/findId", {
    method: "POST",
    headers: {"Content-Type": "application/x-www-form-urlencoded"},
    body: `user_name=${encodeURIComponent(name)}`
  });
  const data = await res.json();

  if (data.result === "success") {
    resultBox.innerText = `당신의 아이디는 [${data.user_id}] 입니다.`;
  } else {
    resultBox.innerText = "해당 이름으로 등록된 아이디가 없습니다.";
  }
}
async function handleFindPw() {
  const userId = document.getElementById("findPwId").value.trim();
  const name = document.getElementById("findPwName").value.trim();
  const resultBox = document.getElementById("findPwResult");
  resultBox.innerText = "";

  if (!userId || !name) {
    resultBox.innerText = "아이디와 이름을 모두 입력하세요.";
    return;
  }

  const res = await fetch("/findPw", {
    method: "POST",
    headers: {"Content-Type": "application/x-www-form-urlencoded"},
    body: `user_id=${encodeURIComponent(userId)}&user_name=${encodeURIComponent(name)}`
  });
  const data = await res.json();

  if (data.result === "success") {
    // 성공시: 비밀번호 재설정 폼(새 비번2개 입력)으로 전환
    PwResetForm(userId); // userId를 다음 스텝에 넘겨야 함!
  } else {
    resultBox.innerText = "일치하는 회원 정보가 없습니다.";
  }
}
function PwResetForm(userId) {
  // 비밀번호 재설정 전용 모달/폼 열고,
  // userId는 숨겨진 input이나 JS 변수에 저장
  document.getElementById("pwResetUserId").value = userId; // hidden input 사용 예시
  switchForm('pwReset'); // 전용 폼으로 전환
}

async function handleLogout() {
  const res = await fetch("/logout", { method: "GET" });
  const data = await res.json();

  if (data.result === "logout") {
    alert("로그아웃 되었습니다!");
    window.location.href = "/main.jsp";
    location.reload();
  } else {
    alert("로그아웃에 실패했습니다. 다시 시도해 주세요.");
  }
}

async function handleModalPwChange() {
  console.log("userId:", getLoginUserId());
  const oldPw = document.getElementById("modalOldPw").value;
  const newPw = document.getElementById("modalNewPw").value;
  const newPw2 = document.getElementById("modalNewPw2").value;
  const msgBox = document.getElementById("pwMsg");
  msgBox.innerText = "";

  if (!oldPw || !newPw || !newPw2) {
    msgBox.innerText = "모든 항목을 입력하세요.";
    return;
  }
  if (newPw !== newPw2) {
    msgBox.innerText = "새 비밀번호가 일치하지 않습니다.";
    return;
  }
  if (oldPw === newPw) {
    msgBox.innerText = "현재 비밀번호와 새 비밀번호가 동일합니다.";
    return;
  }

  // 로그인 유저 id 얻기
  const userId = getLoginUserId();

  // 서버에 비번 변경 요청
  const res = await fetch("/resetPw", {
    method: "POST",
    headers: {"Content-Type": "application/x-www-form-urlencoded"},
    body: `user_id=${encodeURIComponent(userId)}&old_pw=${encodeURIComponent(oldPw)}&new_pw=${encodeURIComponent(newPw)}`
  });
  const data = await res.json();
  if (data.result === "success") {
    alert("비밀번호가 변경되었습니다. 다시 로그인 해주세요.");
    closeModal('pwModal');
    window.location.href = "/main.jsp";
  } else if (data.result === "wrongpw") {
    msgBox.innerText = "현재 비밀번호가 올바르지 않습니다.";
  } else {
    msgBox.innerText = "비밀번호 변경에 실패했습니다. 다시 시도하세요.";
  }
}
async function handlePwResetWithoutOldPw() {
  const userId = document.getElementById("pwResetUserId").value;
  const pw1 = document.getElementById("resetPw1").value;
  const pw2 = document.getElementById("resetPw2").value;
  const msgBox = document.getElementById("pwResetMsg");
  msgBox.innerText = "";

  if (!pw1 || !pw2) {
    msgBox.innerText = "새 비밀번호를 모두 입력하세요.";
    return;
  }
  if (pw1 !== pw2) {
    msgBox.innerText = "새 비밀번호가 일치하지 않습니다.";
    return;
  }

  // 서버로 비밀번호 재설정 요청
  const res = await fetch("/resetPwWithoutOld", {
    method: "POST",
    headers: {"Content-Type": "application/x-www-form-urlencoded"},
    body: `user_id=${encodeURIComponent(userId)}&new_pw=${encodeURIComponent(pw1)}`
  });
  const data = await res.json();

  if (data.result === "success") {
    alert("비밀번호가 성공적으로 재설정되었습니다!");
    switchForm("login");
  } else {
    msgBox.innerText = "비밀번호 재설정에 실패했습니다. 다시 시도하세요.";
  }
}

// 로그인한 user_id를 얻는 함수 (예시, 실제 상황에 맞게 수정)
function getLoginUserId() {
  const el = document.getElementById("loginUserId");
  if (el) return el.innerText.trim();
  if (window.loginUserId) return window.loginUserId;
  return null;
}