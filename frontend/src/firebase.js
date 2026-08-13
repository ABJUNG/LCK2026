// frontend/src/firebase.js
import { initializeApp } from "firebase/app";
import { getFirestore } from "firebase/firestore";

// ⚠️ 여기에 아까 복사한 본인의 firebaseConfig 값을 덮어씌워 주세요!
const firebaseConfig = {
  apiKey: "AIzaSyB6GKMG5_uHKxMCUemVunArYt0Y_MyMXOs",
  authDomain: "l-sikhye.firebaseapp.com",
  projectId: "l-sikhye",
  storageBucket: "l-sikhye.firebasestorage.app",
  messagingSenderId: "355647701471",
  appId: "1:355647701471:web:6f980a1666b2896ca1c46a",
  measurementId: "G-2DXF35H8QB"
};

// Firebase 초기화 및 Firestore DB 객체 내보내기
const app = initializeApp(firebaseConfig);
export const db = getFirestore(app);