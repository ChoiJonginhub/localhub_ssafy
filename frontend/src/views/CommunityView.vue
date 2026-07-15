<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'

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
  <div class="community">
    <header>
      <h1>Community</h1>
      <p>서울 시민들의 실시간 커뮤니티</p>
      <button class="plus" @click="showWrite = true">+</button>
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

    <article v-for="post in posts" :key="post.id" class="post" :class="{ popular: isPopular(post) }">
      <div class="post-header">
        <div>
          <div class="post-meta">{{ post.region }} · {{ post.category }}</div>
          <h2>{{ post.title }}</h2>
        </div>
        <span v-if="isPopular(post)" class="hot-tag">인기</span>
      </div>

      <div class="summary-row">
        <span>좋아요 {{ post.like_count || 0 }}</span>
        <span>조회 {{ post.view_count || 0 }}</span>
        <span>댓글 {{ (post.comments || []).length }}</span>
      </div>

      <div class="buttons">
        <button class="secondary" @click="likePost(post.id)">좋아요</button>
        <button class="secondary" @click="togglePost(post)">{{ expandedPostIds.includes(post.id) ? '내용 접기' : '내용 보기' }}</button>
        <button @click="startEdit(post)">수정</button>
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
            <textarea v-model="commentDrafts[post.id]" rows="3" placeholder="댓글을 입력하세요" />
            <button class="secondary" @click="submitComment(post.id)">댓글 등록</button>
          </div>
        </div>
      </div>

      <div class="delete-box">
        <input v-model="deletePasswords[post.id]" type="password" placeholder="삭제 비밀번호" />
        <button class="delete" @click="deletePost(post.id)">삭제</button>
      </div>
    </article>
  </div>
</template>

<style scoped>
.community {
  min-height: 100vh;
  padding: 40px;
  background: linear-gradient(180deg, #050816, #111827);
  color: white;
}

header {
  margin-bottom: 40px;
  text-align: center;
  position: relative;
}

header h1 {
  font-size: 72px;
  font-weight: 900;
  margin: 0;
  background: linear-gradient(135deg, #fff, #ffd369, #93c5fd);
  -webkit-background-clip: text;
  color: transparent;
}

.plus {
  position: fixed;
  right: 40px;
  bottom: 80px;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  font-size: 28px;
  background: linear-gradient(135deg, #ffd369, #ff8a00);
  box-shadow: 0 20px 40px rgba(255, 180, 0, 0.35);
  z-index: 100;
}

.modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(12px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 999;
}

.modal-card {
  width: 700px;
  max-width: 92%;
  padding: 32px;
  border-radius: 24px;
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: 0 30px 80px rgba(0, 0, 0, 0.45);
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

.post {
  margin-top: 20px;
  padding: 20px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
}

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

.hot-tag {
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 0.8rem;
  background: rgba(250, 204, 21, 0.2);
  color: #fde68a;
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
</style>
