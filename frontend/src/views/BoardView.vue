<script setup>
import { onMounted, ref } from 'vue'

const category = 'seoul'
const posts = ref([])
const loading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const editingId = ref(null)
const deletePasswords = ref({})

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
})
</script>

<template>
  <div class="page">
    <header>
      <h1>서울권역 익명 커뮤니티</h1>
      <p>회원가입 없이 익명으로 작성하고, 수정·삭제는 등록한 비밀번호로만 확인됩니다.</p>
    </header>

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
        <h2>게시글 목록</h2>
        <button type="button" class="secondary" @click="fetchPosts">새로고침</button>
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
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem 1rem 3rem;
  font-family: Arial, sans-serif;
}

header {
  margin-bottom: 1.5rem;
}

.panel {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1rem;
  margin-bottom: 1rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

form,
.card {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

label {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-weight: 600;
}

input,
textarea {
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 0.7rem;
  font-size: 1rem;
}

button {
  border: 0;
  border-radius: 8px;
  padding: 0.7rem 1rem;
  background: #2563eb;
  color: white;
  cursor: pointer;
}

button.secondary {
  background: #e5e7eb;
  color: #111827;
}

.actions,
.section-header,
.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.delete-box {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.delete-box input {
  min-width: 140px;
}

.card {
  border-top: 1px solid #f3f4f6;
  padding-top: 1rem;
  margin-top: 1rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
}

.error {
  color: #b91c1c;
}

.success {
  color: #047857;
}

.empty {
  color: #6b7280;
}
</style>
