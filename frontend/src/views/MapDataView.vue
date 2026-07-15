<script setup>
import { useSunsetTheme } from '@/composables/useSunsetTheme.js'
import MapView from '@/components/MapView.vue'
import Dashboard from '@/components/Dashboard.vue'

const { skyStyle, timeLabel, timeRangeLabel, currentTimeLabel } = useSunsetTheme()
</script>

<template>
  <div class="page" :style="skyStyle">
    <div class="panel">
      <p class="sub-title">SMART CITY DATA</p>
      <h1>지도 및 데이터 시각화</h1>
      <p class="desc">서울 지역 관광 데이터와 위치 정보를 한눈에 확인합니다.</p>
      <div class="theme-pill">
        <span>현재 {{ currentTimeLabel }}</span>
        <span>{{ timeLabel }} · {{ timeRangeLabel }}</span>
      </div>
      <MapView />
      <Dashboard />
    </div>
  </div>
</template>

<style scoped>
.page {
  min-height: 100vh;
  padding: 120px 24px 60px;
  transition: background 0.6s ease;
}

.panel {
  max-width: 1400px;
  margin: 0 auto;
  padding: 32px;
  border-radius: 32px;
  background: rgba(2, 6, 23, 0.45);
  border: 1px solid rgba(255,255,255,0.14);
  backdrop-filter: blur(24px);
  box-shadow: 0 24px 70px rgba(2, 6, 23, 0.3);
}

h1 {
  margin: 0;
  font-size: 42px;
  font-weight: 900;
  color: #fff;
}

.theme-pill {
  display: inline-flex;
  gap: 10px;
  align-items: center;
  padding: 10px 16px;
  margin: 12px 0 24px;
  border-radius: 999px;
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.12);
  color: #f8fafc;
  font-size: 13px;
  font-weight: 700;
}

.sub-title {
  margin: 0 0 8px;
  color: #ffd369;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 3px;
}

.desc {
  margin: 12px 0 24px;
  color: #e2e8f0;
  font-size: 16px;
}
</style>