<template>
  <div ref="mapRef" class="map"></div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const mapRef = ref(null)

onMounted(() => {
  const map = new naver.maps.Map(mapRef.value, {
    center: new naver.maps.LatLng(37.5666805, 126.9784147),
    zoom: 13
  })

  new naver.maps.Marker({
    position: new naver.maps.LatLng(37.5666805, 126.9784147),
    map
  })
})
</script>

<style scoped>
.map {
  width: 100%;
  height: 400px;
  border-radius: 12px;
}
</style>