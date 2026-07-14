<template>
  <div ref="mapRef" class="map"></div>
</template>

<script setup>
import { ref, onMounted } from "vue"

const mapRef = ref(null)

let map = null
const markers = []

async function loadTouristMarkers() {
  const response = await fetch(
    "http://localhost:8000/api/tourist"
  )

  const places = await response.json()

  places.forEach(place => {

    const marker = new naver.maps.Marker({
      position: new naver.maps.LatLng(
        place.lat,
        place.lng
      ),
      title: place.title
    })

    markers.push(marker)

    const infoWindow =
      new naver.maps.InfoWindow({
        content: `
          <div style="
            width:260px;
            padding:12px;
            color:black;
          ">
            ${
              place.image
              ? `
                <img
                  src="${place.image}"
                  style="
                    width:100%;
                    border-radius:10px;
                    margin-bottom:10px;
                  "
                />
              `
              : ''
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

  new MarkerClustering({
  minClusterSize: 2,
  maxZoom: 14,
  map,
  markers,

  icons: [{
    content: `
      <div style="
        width:56px;
        height:56px;
        border-radius:50%;
        background:
          radial-gradient(
            circle,
            rgba(122,162,255,0.95) 0%,
            rgba(76,111,255,0.85) 60%,
            rgba(76,111,255,0.4) 100%
          );

        border: 2px solid rgba(255,255,255,0.2);

        display:flex;
        justify-content:center;
        align-items:center;

        color:white;
        font-size:18px;
        font-weight:700;

        backdrop-filter: blur(10px);

        box-shadow:
          0 0 10px rgba(122,162,255,.8),
          0 0 30px rgba(122,162,255,.5),
          0 0 60px rgba(122,162,255,.3);
      ">
      </div>
    `,
    size: new naver.maps.Size(56,56),
    anchor: new naver.maps.Point(28,28)
  }]
})
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

  await loadTouristMarkers()
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
</style>