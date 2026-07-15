<script setup>
import Navbar from "@/components/Navbar.vue";
import ChatWidget from "@/components/ChatWidget.vue";
import { useSunsetTheme } from "@/composables/useSunsetTheme.js";

const { skyStyle, initializeFromNow } = useSunsetTheme();
initializeFromNow();
</script>

<template>
  <div class="app" :style="skyStyle">
    <div class="aurora aurora1"></div>
    <div class="aurora aurora2"></div>
    <div class="aurora aurora3"></div>

    <Navbar />
    <router-view />
    <ChatWidget />
  </div>
</template>

<style>
html,
body,
#app {
  margin: 0;
  padding: 0;
  min-height: 100%;
  background: #050816;
  font-family: 'Pretendard', sans-serif;
  color: #f8fafc;
}

.app {
  position: relative;
  min-height: 100vh;
  overflow-x: hidden;
  transition: background 0.6s ease;
}

.app > * {
  position: relative;
  z-index: 2;
}

.aurora {
  position: fixed;
  border-radius: 50%;
  filter: blur(140px);
  opacity: 0.35;
  pointer-events: none;
  animation: move 20s ease-in-out infinite;
  z-index: 0;
}

.aurora1 {
  width: 600px;
  height: 600px;
  background: #7c3aed;
  top: -200px;
  left: -200px;
}

.aurora2 {
  width: 700px;
  height: 700px;
  background: #ec4899;
  right: -250px;
  top: 150px;
  animation-delay: 5s;
}

.aurora3 {
  width: 550px;
  height: 550px;
  background: #3b82f6;
  bottom: -150px;
  left: 35%;
  animation-delay: 10s;
}

@keyframes move {
  0% { transform: translate(0,0) scale(1); }
  50% { transform: translate(120px,-80px) scale(1.2); }
  100% { transform: translate(0,0) scale(1); }
}
</style>