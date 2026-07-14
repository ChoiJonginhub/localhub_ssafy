<template>
  <div class="map-toolbar">
  <select v-model="selectedCategory" @change="changeCategory">
    <option value="tourist">관광지</option>
    <option value="leports">레포츠</option>
    <option value="culture">문화시설</option>
    <option value="shop">쇼핑</option>
    <option value="lodge">숙박</option>
    <option value="course">여행코스</option>
    <option value="festival">축제</option>
  </select>

  <input
    v-model="searchKeyword"
    class="place-search"
    placeholder="장소명을 입력하세요"
    @keyup.enter="searchPlace"
  />
  <datalist id="place-list">
  <option
    v-for="place in currentPlaces"
    :key="place.id"
    :value="place.title"
  />
</datalist>

  <button class="search-button" @click="searchPlace">
    🔍
  </button>
</div>
  <div ref="mapRef" class="map"></div>
</template>

<script setup>
import { ref, onMounted } from "vue"

const mapRef = ref(null)
const selectedCategory = ref("tourist")
const searchKeyword = ref("")

const clusterColors = {
  tourist: {
    inner: "#7AA2FF",
    outer: "#4C6FFF"
  },
  leports: {
    inner: "#5EEAD4",
    outer: "#14B8A6"
  },
  culture: {
    inner: "#C084FC",
    outer: "#8B5CF6"
  },
  shop: {
    inner: "#FFD369",
    outer: "#F59E0B"
  },
  lodge: {
    inner: "#FF7A7A",
    outer: "#EF4444"
  },
  course: {
    inner: "#FB923C",
    outer: "#EA580C"
  },
  festival: {
    inner: "#FF9ED2",
    outer: "#EC4899"
  }
}

let currentPlaces = []
let map = null
let cluster = null
const markers = []

function createClusterIcon(category) {
  const color = clusterColors[category] || clusterColors.tourist

  return {
    content: `
      <div
        class="cluster-marker"
        style="
          background:
            radial-gradient(
              circle,
              ${color.inner} 0%,
              ${color.outer} 70%,
              rgba(0,0,0,0.2) 100%
            );

          box-shadow:
            0 0 12px ${color.inner},
            0 0 24px ${color.outer},
            0 0 48px ${color.outer};

          border: 3px solid rgba(255,255,255,.25);
        "
      >
        <span></span>
      </div>
    `,
    size: new naver.maps.Size(64, 64),
    anchor: new naver.maps.Point(32, 32)
  }
}

function clearMarkers() {
  markers.forEach(marker => marker.setMap(null))
  markers.length = 0
  if (cluster) {
    cluster.setMap(null)
    cluster = null
  }
}

function searchPlace() {
  const keyword = searchKeyword.value.trim().toLowerCase()

  const marker = markers.find(marker =>
    marker.getTitle().toLowerCase().includes(keyword)
  )

  if (!marker) {
    alert("검색 결과가 없습니다.")
    return
  }

  map.panTo(marker.getPosition())
  map.setZoom(16)

  naver.maps.Event.trigger(marker, "click")
}

async function loadMarkers(category = "tourist") {
  clearMarkers()

  const response = await fetch(
    `http://localhost:8000/api/${category}`
  )

  const places = await response.json()
  currentPlaces = places

  places.forEach(place => {

    const marker = new naver.maps.Marker({
      position: new naver.maps.LatLng(
        place.lat,
        place.lng
      ),
      title: place.title
    })

    marker.placeData = place
    markers.push(marker)

    const infoWindow = new naver.maps.InfoWindow({
      content: `
        <div style="
          width:260px;
          padding:12px;
          color:black;
        ">
          ${
            place.image
              ? `<img src="${place.image}"
                   style="
                     width:100%;
                     border-radius:10px;
                     margin-bottom:10px;
                   " />`
              : ""
          }

          <h3>${place.title}</h3>
          <p>${place.address}</p>
        </div>
      `
    })

    naver.maps.Event.addListener(
      marker,
      "click",
      () => {
        if (infoWindow.getMap()) {
          infoWindow.close()
        } else {
          infoWindow.open(map, marker)
        }
      }
    )
  })

  cluster = new MarkerClustering({
  map,
  markers,

  minClusterSize: 2,
  maxZoom: 14,

  icons: [
    createClusterIcon(selectedCategory.value)
  ],

  stylingFunction: function(clusterMarker, count) {
    const span =
      clusterMarker.getElement().querySelector("span")

    if (span) {
      span.innerText = count
    }
  }
})
}

async function changeCategory() {
  await loadMarkers(selectedCategory.value)
}

onMounted(async () => {

  map = new naver.maps.Map(
    mapRef.value,
    {
      center: new naver.maps.LatLng(
        37.5665,
        126.9780
      ),
      zoom: 11,
      zoomControl: true
    }
  )

  await loadMarkers(selectedCategory.value)
})
</script>

<style scoped>
.map {
  width: 100%;
  height: 550px;

  border-radius: 28px;

  overflow: hidden;

  box-shadow:
      0 0 50px rgba(122,162,255,.15);
}
.map-toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
}

.place-search {
  width: 250px;

  padding: 10px 16px;

  border: none;
  border-radius: 12px;

  background: rgba(20,20,30,0.85);

  color: white;

  outline: none;

  backdrop-filter: blur(12px);
}

.place-search::placeholder {
  color: #999;
}

.search-button {
  width: 42px;
  height: 42px;

  border: none;
  border-radius: 12px;

  background: rgba(122,162,255,0.8);

  color: white;

  cursor: pointer;

  transition: .2s;
}

.search-button:hover {
  transform: scale(1.05);
}

:deep(.cluster-marker) {
  width: 64px;
  height: 64px;

  border-radius: 50%;

  display: flex;
  justify-content: center;
  align-items: center;

  color: white;
  font-size: 18px;
  font-weight: 700;

  backdrop-filter: blur(12px);

  animation: clusterPulse 2.5s infinite ease-in-out;

  transition: all .3s ease;
}

:deep(.cluster-marker:hover) {
  transform: scale(1.1);
}

:deep(.cluster-marker span) {
  pointer-events: none;
}

@keyframes pulseCluster {
  0% {
    transform: scale(1);
  }

  50% {
    transform: scale(1.08);
  }

  100% {
    transform: scale(1);
  }
}
</style>