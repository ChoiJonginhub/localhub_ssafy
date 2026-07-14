<script setup>
import { onMounted, onBeforeUnmount, ref } from 'vue'
import MapView from './MapView.vue'

const category = 'seoul'
const posts = ref([])
const loading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const notificationMessage = ref('')
const editingId = ref(null)
const deletePasswords = ref({})
const onlineCount = ref(0)
const socket = ref(null)
const reconnectTimer = ref(null)
const lastNotificationId = ref(null)

const form = ref({
  title: '',
  content: '',
  password: '',
})

async function fetchPosts() {
  loading.value = true
  errorMessage.value = ''
  try {
    const response = await fetch(`http://localhost:8000/api/boards/${category}/posts`)
    if (!response.ok) {
      throw new Error('게시글을 불러오지 못했습니다.')
    }
    posts.value = await response.json()
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}

function resetForm() {
  editingId.value = null
  form.value = { title: '', content: '', password: '' }
}

function connectSocket() {
  if (socket.value && (socket.value.readyState === WebSocket.OPEN || socket.value.readyState === WebSocket.CONNECTING)) {
    return
  }

  if (reconnectTimer.value) {
    clearTimeout(reconnectTimer.value)
    reconnectTimer.value = null
  }

  const clientId = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
  window.sessionStorage.setItem('board-client-id', clientId)
  const ws = new WebSocket(`ws://localhost:8000/ws/notifications?client_id=${encodeURIComponent(clientId)}`)
  socket.value = ws

  ws.addEventListener('open', () => {
    onlineCount.value = onlineCount.value
  })

  ws.addEventListener('message', (event) => {
    try {
      const payload = JSON.parse(event.data)
      if (payload.type === 'presence') {
        const nextCount = Number(payload.count) || 0
        onlineCount.value = Math.max(nextCount, 0)
        return
      }

      if (payload.type === 'new_post') {
        const incomingPost = payload.post
        if (lastNotificationId.value === incomingPost.id) {
          return
        }
        lastNotificationId.value = incomingPost.id
        const exists = posts.value.some((post) => post.id === incomingPost.id)
        if (!exists) {
          posts.value = [incomingPost, ...posts.value]
        }
        notificationMessage.value = `새 게시글이 등록되었습니다: ${incomingPost.title}`
        setTimeout(() => {
          if (lastNotificationId.value === incomingPost.id) {
            notificationMessage.value = ''
          }
        }, 4000)
      }
    } catch (error) {
      console.error('WebSocket message parse error', error)
    }
  })

  ws.addEventListener('close', () => {
    socket.value = null
    reconnectTimer.value = setTimeout(() => {
      connectSocket()
    }, 1000)
  })

  ws.addEventListener('error', () => {
    console.error('WebSocket connection error')
  })
}

function startEdit(post) {
  editingId.value = post.id
  form.value = {
    title: post.title,
    content: post.content,
    password: '',
  }
  successMessage.value = ''
  errorMessage.value = ''
}

async function submitForm() {
  if (!form.value.title || !form.value.content || !form.value.password) {
    errorMessage.value = '제목, 내용, 비밀번호를 모두 입력해주세요.'
    return
  }

  try {
    const url = `http://localhost:8000/api/boards/${category}/posts${editingId.value ? `/${editingId.value}` : ''}`
    const method = editingId.value ? 'PUT' : 'POST'
    const payload = {
      title: form.value.title,
      content: form.value.content,
      password: form.value.password,
    }

    const response = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    })

    if (!response.ok) {
      const data = await response.json().catch(() => ({ detail: '요청 처리에 실패했습니다.' }))
      throw new Error(data.detail || '요청 처리에 실패했습니다.')
    }

    successMessage.value = editingId.value ? '게시글이 수정되었습니다.' : '게시글이 등록되었습니다.'
    resetForm()
    await fetchPosts()
  } catch (error) {
    errorMessage.value = error.message
  }
}

async function deletePost(postId) {
  const password = deletePasswords.value[postId] || ''
  if (!password) {
    errorMessage.value = '삭제하려면 비밀번호를 입력해주세요.'
    return
  }

  try {
    const response = await fetch(`http://localhost:8000/api/boards/${category}/posts/${postId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ password }),
    })

    if (!response.ok) {
      const data = await response.json().catch(() => ({ detail: '삭제에 실패했습니다.' }))
      throw new Error(data.detail || '삭제에 실패했습니다.')
    }

    successMessage.value = '게시글이 삭제되었습니다.'
    deletePasswords.value[postId] = ''
    await fetchPosts()
  } catch (error) {
    errorMessage.value = error.message
  }
}

onMounted(() => {
  fetchPosts()
  connectSocket()
})

onBeforeUnmount(() => {
  if (reconnectTimer.value) {
    clearTimeout(reconnectTimer.value)
    reconnectTimer.value = null
  }
  if (socket.value) {
    socket.value.close()
    socket.value = null
  }
})
</script>

<template>
  <div class="page">
    <header class="hero">
  <div class="hero-text">
    <span class="badge">SEOUL COMMUNITY</span>
    <h1>서울권역<br>익명 커뮤니티</h1>
    <p>
      회원가입 없이 자유롭게 글을 작성하고<br>
      비밀번호로 수정과 삭제를 관리하세요.
    </p>

    <div class="status">
      현재 접속자 <strong>{{ onlineCount }}</strong> 명
    </div>

    <div v-if="notificationMessage" class="notification">
      {{ notificationMessage }}
    </div>
  </div>
</header>

    <section class="panel map-panel">
  <div class="section-title">
    <h2>Seoul Map</h2>
    <span>지역 기반 커뮤니티</span>
  </div>

  <MapView />
</section>

    <section class="panel">
      <h2>{{ editingId ? '게시글 수정' : '새 게시글 작성' }}</h2>
      <form @submit.prevent="submitForm">
        <label>
          제목
          <input v-model="form.title" placeholder="제목을 입력하세요" />
        </label>
        <label>
          내용
          <textarea v-model="form.content" rows="6" placeholder="내용을 입력하세요"></textarea>
        </label>
        <label>
          수정/삭제 비밀번호
          <input v-model="form.password" type="password" placeholder="비밀번호" />
        </label>
        <div class="actions">
          <button type="submit">{{ editingId ? '수정하기' : '등록하기' }}</button>
          <button v-if="editingId" type="button" class="secondary" @click="resetForm">취소</button>
        </div>
      </form>
    </section>

    <section class="panel">
      <div class="section-header">
  <div>
    <h2>Community Posts</h2>
    <p>서울 지역의 최신 소식을 확인하세요.</p>
  </div>

  <button type="button" class="secondary" @click="fetchPosts">
    새로고침
  </button>
</div>

      <p v-if="loading">불러오는 중...</p>
      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
      <p v-if="successMessage" class="success">{{ successMessage }}</p>

      <div v-if="posts.length === 0 && !loading" class="empty">
        아직 등록된 게시글이 없습니다.
      </div>

      <article v-for="post in posts" :key="post.id" class="card">
        <div class="card-header">
          <h3>{{ post.title }}</h3>
          <span>{{ new Date(post.created_at).toLocaleString() }}</span>
        </div>
        <p>{{ post.content }}</p>
        <div class="card-footer">
          <button type="button" class="secondary" @click="startEdit(post)">수정</button>
          <div class="delete-box">
            <input v-model="deletePasswords[post.id]" type="password" placeholder="삭제 비밀번호" />
            <button type="button" @click="deletePost(post.id)">삭제</button>
          </div>
        </div>
      </article>
    </section>
  </div>
</template>

<style scoped>
.page {
  max-width: 1400px;
  margin: auto;
  padding: 60px 40px;
  min-height: 100vh;

  background:
    radial-gradient(circle at top left,
      rgba(122,162,255,0.15),
      transparent 30%),
    radial-gradient(circle at top right,
      rgba(255,211,105,0.08),
      transparent 25%),
    linear-gradient(
      180deg,
      #050816 0%,
      #0b1126 40%,
      #111827 100%
    );

  color: #e8edf5;
  overflow-x: hidden;
}

.page::before {
  content: "";
  position: fixed;
  inset: 0;

  background-image:
    radial-gradient(circle, rgba(255,255,255,.9) 1px, transparent 1px),
    radial-gradient(circle, rgba(255,255,255,.6) 1px, transparent 1px);

  background-size:
    120px 120px,
    180px 180px;

  background-position:
    20px 40px,
    100px 120px;

  opacity: .25;
  pointer-events: none;
}

.hero {
  margin-bottom: 48px;
}

.badge {
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.12);

  color: #ffd369;

  backdrop-filter: blur(20px);

  border-radius: 999px;
  padding: 10px 20px;
}

.hero h1 {
  font-size: 82px;
  font-weight: 800;
  line-height: 1.05;

  background: linear-gradient(
      135deg,
      #ffffff,
      #ffd369,
      #7aa2ff
  );

  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;

  margin-bottom: 24px;
}

.hero p {
  color: #9aa4b5;
  line-height: 1.8;
  font-size: 20px;
}

.status {
  margin-top: 30px;
  font-size: 18px;
}

.status strong {
  color: #bf7b44;
}

.panel,
.card {
  background: rgba(20,27,46,0.65);

  backdrop-filter: blur(24px);

  border: 1px solid rgba(255,255,255,0.08);

  border-radius: 28px;

  box-shadow:
      0 20px 60px rgba(0,0,0,.35),
      0 0 40px rgba(122,162,255,.08);
}

.map-panel {
  position: relative;
  overflow: hidden;
}

.map-panel::after {
  content: "";
  position: absolute;

  inset: -100px;

  background:
      radial-gradient(
          circle,
          rgba(122,162,255,.15),
          transparent 70%
      );

  pointer-events: none;
}

.section-title {
  margin-bottom: 24px;
}

.section-title h2 {
  font-size: 32px;
  margin-bottom: 6px;
}

.section-title span {
  color: #9c8f81;
}

form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

label {
  display: flex;
  flex-direction: column;
  gap: 10px;
  font-weight: 600;
}

input,
textarea {
  background: rgba(255,255,255,0.05);

  border: 1px solid rgba(255,255,255,.08);

  color: white;

  border-radius: 18px;
}

input::placeholder,
textarea::placeholder {
  color: #7986a3;
}

input:focus,
textarea:focus {
  border-color: #7aa2ff;

  box-shadow:
      0 0 0 4px rgba(122,162,255,.18);
}

button {
  background:
      linear-gradient(
          135deg,
          #ffd369,
          #ffb347
      );

  color: #111827;

  font-weight: 700;

  box-shadow:
      0 10px 30px rgba(255,211,105,.25);
}

button:hover {
  transform: translateY(-3px);

  box-shadow:
      0 20px 40px rgba(255,211,105,.35);
}

.secondary {
  background:
      rgba(255,255,255,.08);

  color: #dbe3f0;

  border:
      1px solid rgba(255,255,255,.08);
}

.actions,
.section-header,
.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.section-header h2 {
  font-size: 36px;
}

.section-header p {
  color: #8d8278;
}

.card {
  background: white;
  border-radius: 24px;
  padding: 28px;
  margin-top: 24px;
  box-shadow:
      0 6px 24px rgba(0,0,0,.05);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  font-size: 24px;
}

.card-header span {
  color: #a39b93;
}

.card p {
  line-height: 1.8;
  color: #5d554e;
}

.delete-box {
  display: flex;
  gap: 12px;
  align-items: center;
}

.delete-box input {
  width: 180px;
}

.notification {
  margin-top: 20px;
  background: #eef8ee;
  color: #2e6b2e;
  border-radius: 18px;
  padding: 16px;
}

.error {
  color: #d14343;
}

.success {
  color: #1c8f4f;
}

.empty {
  color: #8d8278;
}

@media (max-width: 768px) {
  .page {
    padding: 30px 20px;
  }

  .hero h1 {
    font-size: 48px;
  }

  .panel {
    padding: 24px;
  }

  .section-header h2 {
    font-size: 28px;
  }
}
</style>
