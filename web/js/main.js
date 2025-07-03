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
  if (modal) {
    modal.classList.remove("hidden");

    modal.style.opacity = "0";
    modal.style.transform = "scale(0.95)";

    setTimeout(() => {
      modal.style.transition = "opacity 0.3s ease, transform 0.3s ease";
      modal.style.opacity = "1";
      modal.style.transform = "scale(1)";
    }, 10);
  }
}

// 모달 닫기
function closeModal(id) {
  const modal = document.getElementById(id);
  if (!modal) return;

  modal.style.transition = "opacity 0.3s ease, transform 0.3s ease";
  modal.style.opacity = "0";
  modal.style.transform = "scale(0.95)";

  setTimeout(() => {
    modal.classList.add("hidden");
    modal.style.opacity = "";
    modal.style.transform = "";
    modal.style.transition = "";
  }, 300);
}

function switchForm(mode) {
  const loginForm = document.getElementById("loginForm");
  const signupForm = document.getElementById("signupForm");

  if (mode === "signup") {
    loginForm.classList.add("hidden");
    signupForm.classList.remove("hidden");

    signupForm.style.opacity = "0";
    signupForm.style.transform = "scale(0.95)";
    signupForm.style.filter = "blur(4px)";
    setTimeout(() => {
      signupForm.style.transition = "all 0.4s ease";
      signupForm.style.opacity = "1";
      signupForm.style.transform = "scale(1)";
      signupForm.style.filter = "blur(0)";
    }, 10);
    document.getElementById("signupName")?.focus();
  } else {
    signupForm.classList.add("hidden");
    loginForm.classList.remove("hidden");

    loginForm.style.opacity = "0";
    loginForm.style.transform = "scale(0.95)";
    loginForm.style.filter = "blur(4px)";
    setTimeout(() => {
      loginForm.style.transition = "all 0.4s ease";
      loginForm.style.opacity = "1";
      loginForm.style.transform = "scale(1)";
      loginForm.style.filter = "blur(0)";
    }, 10);
    document.getElementById("loginId")?.focus();
  }
}

function handleLogin() {
  const id = document.getElementById("loginId").value;
  const pw = document.getElementById("loginPw").value;

  if (id === "testuser" && pw === "1234") {
    alert("로그인 성공!");
    closeModal("loginModal");
  } else {
    alert("아이디 또는 비밀번호가 일치하지 않습니다.");
  }
}

function handleSignup() {
  const name = document.getElementById("signupName").value;
  const id = document.getElementById("signupId").value;
  const pw = document.getElementById("signupPw").value;

  if (!name || !id || !pw) {
    alert("모든 항목을 입력해주세요.");
    return;
  }

  alert("회원가입에 성공하였습니다!");
  switchForm("login");
}