import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.5/firebase-app.js";

import {
  getAuth,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut,
  onAuthStateChanged
} from "https://www.gstatic.com/firebasejs/10.12.5/firebase-auth.js";

// Firebase에서 받은 설정값으로 바꿔야 하는 부분
const firebaseConfig = {
  apiKey: "AIzaSyDPGi_MBLGkap_VTdo07j_fXw6Sy4TTPeo",
  authDomain: "kksarchive.firebaseapp.com",
  projectId: "kksarchive",
  storageBucket: "kksarchive.firebasestorage.app",
  messagingSenderId: "322477795788",
  appId: "1:322477795788:web:9f6a9c2c8d26c1a76d5569",
  measurementId: "G-9RG0YXC

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

const emailInput = document.getElementById("email");
const passwordInput = document.getElementById("password");
const privacyAgree = document.getElementById("privacyAgree");

const signupBtn = document.getElementById("signupBtn");
const loginBtn = document.getElementById("loginBtn");
const logoutBtn = document.getElementById("logoutBtn");

const userStatus = document.getElementById("userStatus");
const archiveMenu = document.getElementById("archive-menu");

signupBtn.addEventListener("click", async () => {
  const email = emailInput.value;
  const password = passwordInput.value;

  if (!privacyAgree.checked) {
    alert("개인정보 수집·이용에 동의해야 회원가입할 수 있습니다.");
    return;
  }

  try {
    await createUserWithEmailAndPassword(auth, email, password);
    alert("회원가입이 완료되었습니다.");
  } catch (error) {
    alert("회원가입 오류: " + error.message);
  }
});

loginBtn.addEventListener("click", async () => {
  const email = emailInput.value;
  const password = passwordInput.value;

  try {
    await signInWithEmailAndPassword(auth, email, password);
    alert("로그인되었습니다.");
  } catch (error) {
    alert("로그인 오류: " + error.message);
  }
});

logoutBtn.addEventListener("click", async () => {
  await signOut(auth);
});

onAuthStateChanged(auth, (user) => {
  if (user) {
    userStatus.textContent = `${user.email} 님이 로그인 중입니다.`;
    archiveMenu.style.display = "block";
    logoutBtn.style.display = "inline-block";
    loginBtn.style.display = "none";
    signupBtn.style.display = "none";
  } else {
    userStatus.textContent = "로그인 전입니다.";
    archiveMenu.style.display = "none";
    logoutBtn.style.display = "none";
    loginBtn.style.display = "inline-block";
    signupBtn.style.display = "inline-block";
  }
});
