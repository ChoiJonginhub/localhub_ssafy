<script setup>
import { computed, onMounted, ref, watch } from 'vue'

const meetups = ref([])
const loading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const showWrite = ref(false)
const joinDrafts = ref({})
const joinedNicknames = ref({})
const form = ref({
  title: '',
  host_nickname: '',
  recruitment_count: 4,
  recruitment_period: '',
  activity_content: '',
  location: '',
  latitude: 37.5665,
  longitude: 126.9780,
})

const currentPosition = ref({ lat: 37.5665, lng: 126.9780 })
const mapError = ref('')
const mainMapRef = ref(null)
const writeMapRef = ref(null)
const selectedMeetupId = ref(null)
const chatDrafts = ref({})
const chatMessages = ref({})
let map = null
let meetupMarker = null
let userMarker = null

async function fetchMeetups() {
  loading.value = true
  errorMessage.value = ''
  try {
    const res = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'https://localhub-ssafy-34ya.onrender.com'}/api/meetups`)
    if (!res.ok) throw new Error('모임 정보를 불러오지 못했습니다.')
    meetups.value = await res.json()
    for (const meetup of meetups.value) {
      await fetchMeetupChat(meetup.id)
    }
    if (map) {
      renderMarkers()
    }
  } catch (err) {
    errorMessage.value = err.message
  } finally {
    loading.value = false
  }
}

async function fetchMeetupChat(meetupId) {
  try {
    const res = await fetch(`http://localhost:8000/api/meetups/${meetupId}/chat`)
    if (!res.ok) throw new Error('채팅 내역을 불러오지 못했습니다.')
    const messages = await res.json()
    chatMessages.value = { ...chatMessages.value, [meetupId]: messages }
  } catch (err) {
    chatMessages.value = { ...chatMessages.value, [meetupId]: [] }
  }
}

async function sendMeetupChat(meetup) {
  const nickname = (joinedNicknames.value[meetup.id] || joinDrafts.value[meetup.id] || '').trim()
  const content = (chatDrafts.value[meetup.id] || '').trim()

  if (!nickname) {
    errorMessage.value = '참가 후에만 채팅을 보낼 수 있습니다.'
    return
  }

  if (!content) {
    errorMessage.value = '채팅 내용을 입력해주세요.'
    return
  }

  try {
    const res = await fetch(`http://localhost:8000/api/meetups/${meetup.id}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nickname, content })
    })

    if (!res.ok) throw new Error('채팅 전송에 실패했습니다.')

    chatDrafts.value = { ...chatDrafts.value, [meetup.id]: '' }
    await fetchMeetupChat(meetup.id)
    successMessage.value = '메시지를 전송했습니다.'
  } catch (err) {
    errorMessage.value = err.message
  }
}

async function submitForm() {
  if (!form.value.title || !form.value.host_nickname || !form.value.recruitment_period || !form.value.activity_content || !form.value.location) {
    errorMessage.value = '모든 항목을 입력해주세요.'
    return
  }

  try {
    const res = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'https://localhub-ssafy-34ya.onrender.com'}/api/meetups`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form.value)
    })

    if (!res.ok) throw new Error('모임 등록에 실패했습니다.')

    successMessage.value = '모임이 등록되었습니다. 참가자 닉네임으로 바로 참여해보세요.'
    showWrite.value = false
    form.value = {
      title: '',
      host_nickname: '',
      recruitment_count: 4,
      recruitment_period: '',
      activity_content: '',
      location: '',
      latitude: currentPosition.value.lat,
      longitude: currentPosition.value.lng,
    }
    await fetchMeetups()
  } catch (err) {
    errorMessage.value = err.message
  }
}

async function joinMeetup(meetup) {
  const nickname = joinDrafts.value[meetup.id]?.trim()
  if (!nickname) {
    errorMessage.value = '참가자 닉네임을 입력해주세요.'
    return
  }

  try {
    const res = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'https://localhub-ssafy-34ya.onrender.com'}/api/meetups/${meetup.id}/join`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ participant_nickname: nickname })
    })

    if (!res.ok) throw new Error('참가 신청에 실패했습니다.')

    successMessage.value = `${nickname}님이 모임 참가 신청을 완료했습니다.`
    errorMessage.value = ''
    joinedNicknames.value = { ...joinedNicknames.value, [meetup.id]: nickname }
    joinDrafts.value = { ...joinDrafts.value, [meetup.id]: '' }
    await fetchMeetups()
  } catch (err) {
    errorMessage.value = err.message
  }
}

function initMap() {
  if (!window.naver?.maps || !mainMapRef.value) return

  map = new naver.maps.Map(mainMapRef.value, {
    center: new naver.maps.LatLng(currentPosition.value.lat, currentPosition.value.lng),
    zoom: 12,
    zoomControl: true,
    mapTypeControl: true
  })

  renderMarkers()
}

function renderMarkers() {
  if (!map || !window.naver?.maps) return

  const userPosition = new naver.maps.LatLng(currentPosition.value.lat, currentPosition.value.lng)
  if (userMarker) {
    userMarker.setPosition(userPosition)
    userMarker.setMap(map)
  } else {
    userMarker = new naver.maps.Marker({
      position: userPosition,
      map,
      title: '내 위치',
      icon: {
        content: '<div style="width:14px;height:14px;border-radius:50%;background:#7AA2FF;border:2px solid white;box-shadow:0 0 0 4px rgba(122,162,255,.2);"></div>',
        anchor: new naver.maps.Point(7, 7)
      }
    })
  }

  const selected = selectedMeetup.value
  if (selected && selected.latitude !== undefined && selected.longitude !== undefined) {
    const meetupPosition = new naver.maps.LatLng(selected.latitude, selected.longitude)
    if (meetupMarker) {
      meetupMarker.setPosition(meetupPosition)
      meetupMarker.setMap(map)
    } else {
      meetupMarker = new naver.maps.Marker({
        position: meetupPosition,
        map,
        title: selected.title,
        icon: {
          content: '<div style="width:18px;height:18px;border-radius:50%;background:#F59E0B;border:2px solid white;box-shadow:0 0 0 4px rgba(245,158,11,.25);"></div>',
          anchor: new naver.maps.Point(9, 9)
        }
      })
    }

    const bounds = new naver.maps.LatLngBounds()
    bounds.extend(userPosition)
    bounds.extend(meetupPosition)
    map.fitBounds(bounds, { top: 30, right: 30, bottom: 30, left: 30 })
  } else {
    map.setCenter(userPosition)
    map.setZoom(12)
  }
}

function updateMap(meetup) {
  if (!map || !window.naver?.maps || !meetup) return
  selectedMeetupId.value = meetup.id
  renderMarkers()
}

function selectMeetup(meetup) {
  selectedMeetupId.value = meetup.id
  updateMap(meetup)
}

function requestLocation() {
  if (!navigator.geolocation) {
    mapError.value = '브라우저에서 위치 권한을 지원하지 않습니다.'
    return
  }

  navigator.geolocation.getCurrentPosition((position) => {
    currentPosition.value = {
      lat: position.coords.latitude,
      lng: position.coords.longitude
    }
    if (map) {
      const nextPos = new naver.maps.LatLng(currentPosition.value.lat, currentPosition.value.lng)
      map.setCenter(nextPos)
      renderMarkers()
    }
  }, () => {
    mapError.value = '위치 권한을 허용해주세요.'
  })
}

const selectedMeetup = computed(() => {
  if (selectedMeetupId.value) {
    return meetups.value.find((meetup) => meetup.id === selectedMeetupId.value) || meetups.value[0] || null
  }
  return meetups.value[0] || null
})

watch([selectedMeetup, currentPosition], () => {
  if (map) {
    renderMarkers()
  }
}, { deep: true })

onMounted(async () => {
  try {
    if (!window.naver?.maps) {
      throw new Error('네이버 지도 SDK를 불러오지 못했습니다.')
    }
    initMap()
    requestLocation()
    await fetchMeetups()
    if (selectedMeetup.value) {
      updateMap(selectedMeetup.value)
    }
  } catch (err) {
    mapError.value = err.message || '지도를 초기화하지 못했습니다.'
  }
})
</script>

<template>
  <section class="meetup-page">
    <div class="hero">
      <div>
        <p class="eyebrow">MEETUP</p>
        <h1>모임을 만들고, 참여하고, 함께 만나요</h1>
        <p class="hero-text">모집자와 참가자 닉네임을 입력해 모임을 시작하고, 지도에서 위치까지 확인하세요.</p>
      </div>
      <button class="write-btn" @click="showWrite = true">+ 모임 만들기</button>
    </div>

    <div v-if="showWrite" class="modal">
      <div class="modal-card">
        <button class="close-btn" @click="showWrite = false">✕</button>
        <h2>모임 등록</h2>

        <input v-model="form.title" placeholder="모임 제목" />
        <input v-model="form.host_nickname" placeholder="모집자 닉네임" />
        <input v-model="form.recruitment_period" placeholder="모집 기간 (예: 2026-07-20까지)" />
        <input v-model="form.recruitment_count" type="number" min="1" placeholder="모집 인원" />
        <textarea v-model="form.activity_content" rows="4" placeholder="활동 내용" />
        <input v-model="form.location" placeholder="모임 위치" />

        <div class="map-preview" ref="writeMapRef"></div>
        <p v-if="mapError" class="error">{{ mapError }}</p>

        <div class="modal-buttons">
          <button class="secondary" @click="showWrite = false">취소</button>
          <button @click="submitForm">등록하기</button>
        </div>
      </div>
    </div>

    <div class="status-row">
      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
      <p v-if="successMessage" class="success">{{ successMessage }}</p>
    </div>

    <div class="layout-grid">
      <div class="card">
        <div class="card-title">모임 목록</div>
        <div v-if="loading">불러오는 중...</div>
        <div v-else-if="meetups.length === 0">등록된 모임이 없습니다.</div>
        <div v-else class="meetup-list">
          <article v-for="meetup in meetups" :key="meetup.id" class="meetup-item" @click="selectMeetup(meetup)">
            <div class="meetup-head">
              <div>
                <h3>{{ meetup.title }}</h3>
                <p class="meta">모집자: {{ meetup.host_nickname }} · 위치: {{ meetup.location }}</p>
              </div>
              <span class="badge">{{ meetup.current_participants }}/{{ meetup.recruitment_count }}명</span>
            </div>
            <p class="content">{{ meetup.activity_content }}</p>
            <p class="meta">모집 기간: {{ meetup.recruitment_period }}</p>
            <div class="participants">
              <strong>참가자</strong>
              <div class="chips">
                <span v-for="participant in meetup.participants" :key="participant" class="chip">{{ participant }}</span>
              </div>
            </div>

            <div class="join-box">
              <input v-model="joinDrafts[meetup.id]" placeholder="참가자 닉네임" />
              <button @click="joinMeetup(meetup)">모임 참가</button>
            </div>

            <div class="chat-box">
              <div class="chat-title">모임 채팅</div>
              <div class="chat-list">
                <div v-if="!(chatMessages[meetup.id] || []).length" class="chat-empty">첫 인사를 남겨보세요.</div>
                <div v-for="message in (chatMessages[meetup.id] || [])" :key="message.id" class="chat-message">
                  <div class="chat-message-head">
                    <strong>{{ message.nickname }}</strong>
                    <span>{{ new Date(message.created_at).toLocaleString('ko-KR', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' }) }}</span>
                  </div>
                  <div class="chat-message-body">{{ message.content }}</div>
                </div>
              </div>
              <div class="chat-inputs">
                <input v-model="chatDrafts[meetup.id]" :disabled="!(joinedNicknames[meetup.id] || joinDrafts[meetup.id])" placeholder="메시지를 입력하세요" @keyup.enter="sendMeetupChat(meetup)" />
                <button :disabled="!(joinedNicknames[meetup.id] || joinDrafts[meetup.id])" @click="sendMeetupChat(meetup)">전송</button>
              </div>
              <p v-if="!(joinedNicknames[meetup.id] || joinDrafts[meetup.id])" class="chat-help">참가 후에만 채팅을 보낼 수 있습니다.</p>
            </div>
          </article>
        </div>
      </div>

      <div class="card">
        <div class="card-title">모임 위치 / 내 위치</div>
        <div class="map-preview" ref="mainMapRef"></div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.meetup-page {
  margin-top: 80px;
  padding: 24px 24px 80px;
  color: #f8fafc;
}
.hero {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  padding: 28px 32px;
  border-radius: 24px;
  background: linear-gradient(135deg, rgba(122,162,255,.35), rgba(15,23,42,.95));
  margin-bottom: 24px;
}
.eyebrow {
  margin: 0 0 8px;
  color: #7AA2FF;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 2px;
}
.hero h1 { margin: 0; font-size: 28px; }
.hero-text { margin: 8px 0 0; color: #cbd5e1; }
.write-btn { background: linear-gradient(135deg, #ffd369, #f59e0b); color: #111827; }
.layout-grid { display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 20px; }
.card { background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(255,255,255,.12); border-radius: 24px; padding: 20px; }
.card-title { font-size: 18px; font-weight: 800; margin-bottom: 16px; }
.meetup-list { display: grid; gap: 14px; }
.meetup-item { padding: 16px; border-radius: 16px; background: rgba(30,41,59,.7); }
.meetup-head { display: flex; justify-content: space-between; gap: 12px; align-items: start; }
.badge { padding: 4px 10px; border-radius: 999px; background: rgba(122,162,255,.18); color: #7AA2FF; font-weight: 700; }
.meta { color: #94a3b8; font-size: 13px; margin: 4px 0 0; }
.content { color: #e2e8f0; margin-top: 10px; }
.participants { margin-top: 10px; }
.chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
.chip { padding: 6px 10px; border-radius: 999px; background: rgba(94,234,212,.12); color: #5EEAD4; font-size: 12px; }
.join-box { display: flex; gap: 10px; margin-top: 12px; }
.join-box input { flex: 1; padding: 10px 12px; border-radius: 12px; border: 1px solid rgba(255,255,255,.12); background: rgba(255,255,255,.06); color: white; }
.chat-box { margin-top: 14px; padding: 12px; border-radius: 14px; background: rgba(15,23,42,.55); border: 1px solid rgba(255,255,255,.08); }
.chat-title { font-size: 13px; font-weight: 700; color: #7AA2FF; margin-bottom: 8px; }
.chat-list { display: grid; gap: 8px; max-height: 220px; overflow: auto; margin-bottom: 10px; }
.chat-empty { color: #94a3b8; font-size: 13px; }
.chat-message { padding: 8px 10px; border-radius: 10px; background: rgba(255,255,255,.05); }
.chat-message-head { display: flex; justify-content: space-between; gap: 10px; color: #e2e8f0; font-size: 12px; margin-bottom: 4px; }
.chat-message-body { color: #f8fafc; font-size: 14px; line-height: 1.4; }
.chat-inputs { display: flex; gap: 8px; }
.chat-inputs input { flex: 1; padding: 9px 10px; border-radius: 10px; border: 1px solid rgba(255,255,255,.12); background: rgba(255,255,255,.06); color: white; }
.chat-inputs button { padding: 0 12px; border-radius: 10px; }
.modal { position: fixed; inset: 0; background: rgba(0,0,0,.75); display: flex; justify-content: center; align-items: center; z-index: 1000; }
.modal-card { width: min(620px, 92vw); background: rgba(15,23,42,.98); border-radius: 24px; padding: 24px; }
.modal-card input, .modal-card textarea { width: 100%; margin-bottom: 12px; padding: 12px 14px; border-radius: 12px; border: 1px solid rgba(255,255,255,.12); background: rgba(255,255,255,.06); color: white; }
.modal-buttons { display: flex; justify-content: flex-end; gap: 10px; margin-top: 8px; }
.close-btn { float: right; background: transparent; color: white; padding: 0; }
.map-preview { width: 100%; height: 320px; border-radius: 18px; overflow: hidden; margin-top: 10px; border: 1px solid rgba(255,255,255,.12); }
.error { color: #fb7185; }
.success { color: #4ade80; }
@media (max-width: 900px) { .layout-grid { grid-template-columns: 1fr; } .hero { flex-direction: column; align-items: flex-start; } }
</style>
