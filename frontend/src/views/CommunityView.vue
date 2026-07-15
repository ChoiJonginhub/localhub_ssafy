<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useSunsetTheme } from '@/composables/useSunsetTheme.js'

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
const expandedPostIds = ref([])
const viewedPostIds = ref([])
const commentDrafts = ref({})
const options = ref({ regions: [], categories: [] })
const showWrite = ref(false)
const { skyStyle, timeLabel, timeRangeLabel, currentTimeLabel } = useSunsetTheme()

const form = ref({
  title: '',
  content: '',
  password: ''
})

const communityMeta = ref({
  region: '강남구',
  category: '맛집'
})

async function fetchOptions() {
  try {
    const res = await fetch('http://localhost:8000/api/community/options')
    if (!res.ok) throw new Error('옵션 정보를 불러오지 못했습니다.')
    options.value = await res.json()
  } catch (err) {
    errorMessage.value = err.message
  }
}

async function fetchPosts() {
  try {
    loading.value = true
    const res = await fetch(`http://localhost:8000/api/boards/${category}/posts`)
    if (!res.ok) throw new Error('게시글을 불러오지 못했습니다.')
    posts.value = await res.json()
  } catch (err) {
    errorMessage.value = err.message
  } finally {
    loading.value = false
  }
}

function resetForm() {
  editingId.value = null
  form.value = { title: '', content: '', password: '' }
  communityMeta.value = { region: '강남구', category: '맛집' }
}

function startEdit(post) {
  showWrite.value = true
  editingId.value = post.id
  form.value = {
    title: post.title,
    content: post.content,
    password: ''
  }
  communityMeta.value = {
    region: post.region || '강남구',
    category: post.category || '맛집'
  }
}

async function submitForm() {
  if (!form.value.title || !form.value.content || !form.value.password) {
    errorMessage.value = '제목, 내용, 비밀번호를 입력해주세요.'
    return
  }

  const url = `http://localhost:8000/api/boards/${category}/posts${editingId.value ? `/${editingId.value}` : ''}`
  const method = editingId.value ? 'PUT' : 'POST'

  try {
    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...form.value,
        region: communityMeta.value.region,
        category: communityMeta.value.category
      })
    })

    if (!res.ok) throw new Error('처리에 실패했습니다.')

    successMessage.value = editingId.value ? '게시글 수정 완료' : '게시글 등록 완료'
    resetForm()
    showWrite.value = false
    await fetchPosts()
  } catch (err) {
    errorMessage.value = err.message
  }
}

async function deletePost(id) {
  const password = deletePasswords.value[id]
  if (!password) {
    errorMessage.value = '삭제 비밀번호를 입력해주세요.'
    return
  }

  try {
    const res = await fetch(`http://localhost:8000/api/boards/${category}/posts/${id}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password })
    })

    if (!res.ok) throw new Error('삭제 실패')

    successMessage.value = '게시글이 삭제되었습니다.'
    await fetchPosts()
  } catch (err) {
    errorMessage.value = err.message
  }
}

function togglePost(post) {
  if (expandedPostIds.value.includes(post.id)) {
    expandedPostIds.value = expandedPostIds.value.filter((id) => id !== post.id)
    return
  }

  expandedPostIds.value = [...expandedPostIds.value, post.id]
  if (!viewedPostIds.value.includes(post.id)) {
    viewedPostIds.value = [...viewedPostIds.value, post.id]
    void viewPost(post.id)
  }
}

const sortedPosts = computed(() => {
  return [...posts.value].sort((a, b) => (b.view_count || 0) - (a.view_count || 0))
})

async function viewPost(postId) {
  try {
    const res = await fetch(`http://localhost:8000/api/boards/${category}/posts/${postId}/view`, { method: 'POST' })
    if (!res.ok) return
    const updatedPost = await res.json()
    posts.value = posts.value.map((post) => (post.id === postId ? updatedPost : post))
  } catch (err) {
    console.error(err)
  }
}

async function likePost(postId) {
  try {
    const res = await fetch(`http://localhost:8000/api/boards/${category}/posts/${postId}/like`, { method: 'POST' })
    if (!res.ok) throw new Error('좋아요 처리에 실패했습니다.')
    const updatedPost = await res.json()
    posts.value = posts.value.map((post) => (post.id === postId ? updatedPost : post))
  } catch (err) {
    errorMessage.value = err.message
  }
}

async function submitComment(postId) {
  const content = commentDrafts.value[postId]?.trim()
  if (!content) {
    errorMessage.value = '댓글 내용을 입력해주세요.'
    return
  }

  try {
    const res = await fetch(`http://localhost:8000/api/boards/${category}/posts/${postId}/comments`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content })
    })

    if (!res.ok) throw new Error('댓글 등록에 실패했습니다.')

    const updatedPost = await res.json()
    posts.value = posts.value.map((post) => (post.id === postId ? updatedPost : post))
    commentDrafts.value = { ...commentDrafts.value, [postId]: '' }
    successMessage.value = '댓글이 등록되었습니다.'
  } catch (err) {
    errorMessage.value = err.message
  }
}

function connectSocket() {
  socket.value = new WebSocket(`ws://localhost:8000/ws/notifications?client_id=${Date.now()}`)

  socket.value.onmessage = (event) => {
    const data = JSON.parse(event.data)
    if (data.type === 'presence') {
      onlineCount.value = data.count
    }
    if (data.type === 'new_post') {
      posts.value = [data.post, ...posts.value.filter((post) => post.id !== data.post.id)]
      notificationMessage.value = '새 게시글이 등록되었습니다.'
    }
  }

  socket.value.onclose = () => {
    reconnectTimer.value = setTimeout(connectSocket, 1000)
  }
}

function isPopular(post) {
  return (post.like_count || 0) >= 3
}

onMounted(async () => {
  await fetchOptions()
  await fetchPosts()
  connectSocket()
})

onBeforeUnmount(() => {
  if (socket.value) socket.value.close()
  if (reconnectTimer.value) clearTimeout(reconnectTimer.value)
})
</script>

<template>
  <div class="community" :style="skyStyle">
    <header class="hero">
  <div class="hero-bg"></div>

  <div class="hero-content">
    <span class="hero-badge">
      🌆 Seoul Community
    </span>

    <h1>
      서울 실시간 커뮤니티
    </h1>

    <p>
      오늘 서울에서 일어나는 이야기를
      실시간으로 공유해보세요.
    </p>

    <div class="hero-info">

      <div class="info-card">
        <span>🕒</span>
        <div>
          <small>현재 시간</small>
          <b>{{ currentTimeLabel }}</b>
        </div>
      </div>

      <div class="info-card">
        <span>👥</span>
        <div>
          <small>접속자</small>
          <b>{{ onlineCount }}명</b>
        </div>
      </div>

      <div class="info-card">
        <span>🌅</span>
        <div>
          <small>테마</small>
          <b>{{ timeLabel }}</b>
        </div>
      </div>

    </div>

  </div>

  <button class="write-btn" @click="showWrite=true">
    ✏ 새 글 작성
  </button>

</header>

    <div v-if="showWrite" class="modal">
      <div class="modal-card">
        <button class="close-btn" @click="showWrite = false">✕</button>
        <h2>{{ editingId ? '게시글 수정' : '게시글 작성' }}</h2>

        <input v-model="form.title" placeholder="제목" />
        <textarea v-model="form.content" rows="8" placeholder="내용" />

        <div class="meta-grid">
          <label>
            지역 선택
            <select v-model="communityMeta.region">
              <option v-for="region in options.regions" :key="region" :value="region">{{ region }}</option>
            </select>
          </label>
          <label>
            카테고리 선택
            <select v-model="communityMeta.category">
              <option v-for="categoryOption in options.categories" :key="categoryOption" :value="categoryOption">{{ categoryOption }}</option>
            </select>
          </label>
        </div>

        <input v-model="form.password" type="password" placeholder="수정 / 삭제 비밀번호" />

        <div class="modal-buttons">
          <button class="cancel" @click="showWrite = false">취소</button>
          <button class="submit" @click="submitForm">등록하기</button>
        </div>
      </div>
    </div>

    <div class="status">
      현재 접속자 <b>{{ onlineCount }}</b> 명
    </div>

    <p v-if="loading">불러오는 중...</p>
    <p class="error">{{ errorMessage }}</p>
    <p class="success">{{ successMessage }}</p>
    <div class="notice">{{ notificationMessage }}</div>

    <div class="post-grid">
    <article v-for="post in sortedPosts" :key="post.id" class="post" :class="{ popular: isPopular(post) }">

    <div class="card-top">

  <div class="left">

    <div class="avatar">
      {{ post.region[0] }}
    </div>

    <div>

      <div class="chips">

        <span class="chip location">
          📍 {{ post.region }}
        </span>

        <span class="chip category">
          {{ post.category }}
        </span>

        <span
          v-if="isPopular(post)"
          class="chip hot"
        >
          🔥 인기
        </span>

      </div>

      <h2>{{ post.title }}</h2>

    </div>

  </div>

</div>

<p
class="preview"
v-if="!expandedPostIds.includes(post.id)"
>
{{ post.content.slice(0,120) }}
<span v-if="post.content.length>120">...</span>
</p>

<div class="summary-row">

    <div class="summary-item">
        ❤️
        <span>{{ post.like_count || 0 }}</span>
    </div>

    <div class="summary-item">
        💬
        <span>{{ (post.comments || []).length }}</span>
    </div>

    <div class="summary-item">
        👁
        <span>{{ post.view_count || 0 }}</span>
    </div>

</div>
      <div class="buttons">

<button class="icon-btn like"
@click="likePost(post.id)">
❤️ 좋아요
</button>

<button
class="icon-btn view"
@click="togglePost(post)"
>
{{ expandedPostIds.includes(post.id) ? '📖 접기' : '📖 내용 보기' }}
</button>

<button
class="icon-btn edit"
@click="startEdit(post)"
>
✏ 수정
</button>

</div>

      <div v-if="expandedPostIds.includes(post.id)" class="content-panel">
        <p class="content">{{ post.content }}</p>

        <div class="comment-box">
          <h3>댓글</h3>
          <div v-if="(post.comments || []).length === 0" class="empty-comment">첫 댓글을 남겨보세요.</div>
          <div v-for="comment in post.comments || []" :key="comment.id" class="comment-item">
            <p>{{ comment.content }}</p>
            <span>{{ new Date(comment.created_at).toLocaleString() }}</span>
          </div>

          <div class="comment-form">
  <textarea
    v-model="commentDrafts[post.id]"
    rows="3"
    placeholder="💬 댓글을 입력해보세요..."
  />

  <button
    class="comment-submit"
    @click="submitComment(post.id)"
  >
    등록하기 →
  </button>
</div>
        </div>
      </div>

      <div class="delete-box">

  <input
    v-model="deletePasswords[post.id]"
    type="password"
    placeholder="🔒 삭제 비밀번호"
  />

  <button
    class="delete"
    @click="deletePost(post.id)"
  >
    🗑 삭제
  </button>

</div>
    </article>
    </div>
  </div>
</template>

<style scoped>
.community {
  min-height: 100vh;
  padding: 120px 24px 60px;
  transition: background 0.6s ease;
  color: #f8fafc;
}

.hero{
    position:relative;
    overflow:hidden;
    padding:90px 60px;
    margin-bottom:45px;

    border-radius:35px;

    background:
    linear-gradient(135deg,
    rgba(29,78,216,.55),
    rgba(15,23,42,.75),
    rgba(88,28,135,.65));

    border:1px solid rgba(255,255,255,.08);

    box-shadow:
    0 20px 60px rgba(0,0,0,.35);
}

.hero-bg{

    position:absolute;

    inset:0;

    background:

    radial-gradient(circle at 20% 20%,
    rgba(59,130,246,.45),
    transparent 35%),

    radial-gradient(circle at 80% 30%,
    rgba(168,85,247,.35),
    transparent 30%),

    radial-gradient(circle at 50% 100%,
    rgba(255,170,0,.18),
    transparent 45%);

    filter:blur(20px);
}

.hero-content{

    position:relative;

    z-index:2;
}

.hero-badge{

    display:inline-block;

    padding:10px 18px;

    border-radius:999px;

    background:rgba(255,255,255,.12);

    border:1px solid rgba(255,255,255,.12);

    font-weight:700;

    margin-bottom:20px;
}

.hero h1{

    font-size:72px;

    line-height:1.05;

    margin:0;

    font-weight:900;

    background:
    linear-gradient(135deg,#fff,#ffe082,#60a5fa);

    -webkit-background-clip:text;

    color:transparent;
}

.hero p{

    font-size:20px;

    margin-top:22px;

    color:#dbeafe;

    line-height:1.7;
}

.hero-info{

    display:flex;

    gap:18px;

    margin-top:45px;

    flex-wrap:wrap;
}

.info-card{

    display:flex;

    align-items:center;

    gap:15px;

    padding:18px 22px;

    min-width:190px;

    border-radius:20px;

    backdrop-filter:blur(18px);

    background:rgba(255,255,255,.08);

    border:1px solid rgba(255,255,255,.08);
}

.info-card span{

    font-size:32px;
}

.info-card small{

    color:#cbd5e1;

    display:block;
}

.info-card b{

    font-size:18px;
}

.write-btn{

    position:absolute;

    right:45px;

    bottom:45px;

    padding:18px 28px;

    border-radius:18px;

    font-size:16px;

    background:linear-gradient(135deg,#ffcf5c,#ff8c42);

    box-shadow:0 12px 35px rgba(255,170,0,.35);

    transition:.3s;
}

.write-btn:hover{

    transform:translateY(-4px) scale(1.03);
}

.modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(12px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 999;
}

.modal-card{

    width:600px;

    padding:28px;

    border-radius:24px;
}

.modal-card h2{

    font-size:26px;

    margin-bottom:24px;

    text-align:center;
}

.modal-card input,
.modal-card textarea,
.modal-card select{

    margin-bottom:16px;

    background:rgba(255,255,255,.09);

    transition:.25s;
}

.modal-card input:focus,
.modal-card textarea:focus,
.modal-card select:focus{

    border-color:#60a5fa;

    box-shadow:0 0 0 3px rgba(96,165,250,.2);
}

.close-btn {
  float: right;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
  color: white;
}

.modal-card h2 {
  margin: 0 0 20px;
}

.modal-card input,
.modal-card textarea,
.modal-card select {
  width: 100%;
  margin-bottom: 12px;
  padding: 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: white;
}

.meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.modal-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 12px;
}

button {
  border: none;
  padding: 10px 16px;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 600;
  color: white;
  background: linear-gradient(135deg, #ffd369, #ff8a00);
}

button.secondary {
  background: rgba(255, 255, 255, 0.12);
}

button.delete {
  background: linear-gradient(135deg, #fb7185, #ef4444);
}

.status, .notice, .error, .success {
  margin: 12px 0;
}

.error { color: #fb7185; }
.success { color: #4ade80; }



.post.popular {
  border-color: rgba(250, 204, 21, 0.7);
}

.post-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: start;
}

.post-meta {
  color: #93c5fd;
  font-size: 0.9rem;
  margin-bottom: 4px;
}

.post{


    padding:28px;

    border-radius:26px;

    background:rgba(255,255,255, 0.2);

    backdrop-filter:blur(18px);

    border:1px solid rgba(255,255,255,.08);

    transition:.35s;

    overflow:hidden;
}

.post:hover{

    transform:translateY(-8px);

    border-color:#60a5fa;

    box-shadow:
    0 20px 60px rgba(0,0,0,.28);
}
.modal-card select{
    appearance:none;

    background:rgba(255,255,255,.08);

    color:#fff;

    border:1px solid rgba(255,255,255,.15);

    padding:14px 18px;

    border-radius:14px;
}

.modal-card option{

    background:#1e293b;

    color:white;
}
.card-top{

    display:flex;

    justify-content:space-between;

    align-items:flex-start;
}

.left{

    display:flex;

    gap:18px;
}

.avatar{

    width:58px;

    height:58px;

    border-radius:50%;

    background:linear-gradient(
    135deg,
    #3b82f6,
    #8b5cf6);

    display:flex;

    justify-content:center;

    align-items:center;

    font-size:24px;

    font-weight:bold;

    color:white;

    box-shadow:
    0 10px 30px rgba(59,130,246,.4);
}

.chips{

    display:flex;

    gap:8px;

    flex-wrap:wrap;

    margin-bottom:10px;
}

.chip{

    padding:6px 12px;

    border-radius:999px;

    font-size:12px;

    font-weight:700;
}

.location{

background:rgba(37,99,235,.18);

color:#93c5fd;

}

.category{

background:rgba(255,255,255,.08);

color:#e5e7eb;

}

.hot{

background:rgba(245,158,11,.15);

color:#ffd166;

}

.post h2{

    margin:0;

    font-size:30px;

    font-weight:800;
}

.preview{

    margin-top:20px;

    color:#d1d5db;

    line-height:1.8;

    font-size:15px;
}

.summary-row{

    display:flex;

    gap:26px;

    margin-top:24px;

    padding-top:20px;

    border-top:1px solid rgba(255,255,255,.08);
}

.summary-item{

    display:flex;

    align-items:center;

    gap:8px;

    font-weight:700;

    color:#e5e7eb;

    font-size:15px;
}

.summary-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin: 12px 0 16px;
  color: #cbd5e1;
}

.buttons {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.content-panel {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.12);
}

.content {
  white-space: pre-line;
  line-height: 1.7;
}

.comment-box {
  margin-top: 12px;
}

.comment-item {
  padding: 10px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.comment-item p {
  margin: 0 0 4px;
}

.comment-item span {
  color: #94a3b8;
  font-size: 0.82rem;
}

.comment-form {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 10px;
}

.delete-box {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.delete-box input {
  width: 180px;
}

@media (max-width: 768px) {
  .community { padding: 20px; }
  .meta-grid { grid-template-columns: 1fr; }
  .delete-box { flex-direction: column; }
  .delete-box input { width: 100%; }
}

.buttons{

display:flex;

gap:12px;

margin-top:22px;

}

.icon-btn{

padding:12px 20px;

border:none;

border-radius:14px;

font-weight:700;

transition:.25s;
}

.post-grid{

display:grid;

grid-template-columns:
repeat(2,minmax(0,1fr));

gap:24px;

align-items:start;

}

.like{

background:#ec4899;
}

.view{

background:#334155;
}

.edit{

background:#f59e0b;
}

.icon-btn:hover{

transform:translateY(-3px);

filter:brightness(1.08);

box-shadow:0 10px 25px rgba(0,0,0,.25);
}

.like{

background:#2563eb;

}

.view{

background:rgba(255,255,255,.08);

}

.edit{

background:rgba(255,255,255,.08);

}

.delete{

background:#ef4444;
}
</style>
