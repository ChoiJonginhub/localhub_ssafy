<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import MapView from '../components/MapView.vue'

const category = 'seoul'

const sunsetProgress = ref(50)
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
const expandedPostIds = ref([])
const viewedPostIds = ref([])
const commentDrafts = ref({})
const options = ref({ regions: [], categories: [] })

const form = ref({
  title: '',
  content: '',
  password: ''
})

const communityMeta = ref({
  region: '강남구',
  category: '맛집'
})

const skyStyle = computed(() => {
  let c1 = '#1a1035'
  let c2 = '#9b3d70'
  let c3 = '#f97316'

  if (sunsetProgress.value <= 33) {
    c1 = '#1a1035'
    c2 = '#9b3d70'
    c3 = '#f97316'
  } else if (sunsetProgress.value <= 70) {
    c1 = '#1b153a'
    c2 = '#7c3aed'
    c3 = '#ec4899'
  } else {
    c1 = '#050816'
    c2 = '#111827'
    c3 = '#1e293b'
  }

  return {
    background: `linear-gradient(to bottom, ${c1}, ${c2}, ${c3})`
  }
})

function resetForm() {
  editingId.value = null
  form.value = {
    title: '',
    content: '',
    password: ''
  }
  communityMeta.value = {
    region: '강남구',
    category: '맛집'
  }
}

function startEdit(post) {
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

async function fetchOptions() {
  try {
    const res = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'https://localhub-ssafy-34ya.onrender.com'}/api/community/options`)
    if (!res.ok) {
      throw new Error('옵션 정보를 불러오지 못했습니다.')
    }
    options.value = await res.json()
  } catch (err) {
    errorMessage.value = err.message
  }
}

async function fetchPosts() {
  loading.value = true
  errorMessage.value = ''

  try {
    const res = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'https://localhub-ssafy-34ya.onrender.com'}/api/boards/${category}/posts`)
    if (!res.ok) {
      throw new Error('게시글을 불러오지 못했습니다.')
    }
    posts.value = await res.json()
  } catch (err) {
    errorMessage.value = err.message
  } finally {
    loading.value = false
  }
}

async function submitForm() {
  if (!form.value.title || !form.value.content || !form.value.password) {
    errorMessage.value = '제목, 내용, 비밀번호를 입력해주세요.'
    return
  }

  const url = `${import.meta.env.VITE_API_BASE_URL || 'https://localhub-ssafy-34ya.onrender.com'}/api/boards/${category}/posts${editingId.value ? `/${editingId.value}` : ''}`
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

    if (!res.ok) {
      throw new Error('처리에 실패했습니다.')
    }

    successMessage.value = editingId.value ? '게시글이 수정되었습니다.' : '게시글이 등록되었습니다.'
    resetForm()
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
    const res = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'https://localhub-ssafy-34ya.onrender.com'}/api/boards/${category}/posts/${id}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password })
    })

    if (!res.ok) {
      throw new Error('삭제 실패')
    }

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
    const res = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'https://localhub-ssafy-34ya.onrender.com'}/api/boards/${category}/posts/${postId}/view`, {
      method: 'POST'
    })
    if (!res.ok) {
      return
    }
    const updatedPost = await res.json()
    posts.value = posts.value.map((post) => (post.id === postId ? updatedPost : post))
  } catch (err) {
    console.error(err)
  }
}

async function likePost(postId) {
  try {
    const res = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'https://localhub-ssafy-34ya.onrender.com'}/api/boards/${category}/posts/${postId}/like`, {
      method: 'POST'
    })
    if (!res.ok) {
      throw new Error('좋아요 처리에 실패했습니다.')
    }
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
    const res = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'https://localhub-ssafy-34ya.onrender.com'}/api/boards/${category}/posts/${postId}/comments`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content })
    })

    if (!res.ok) {
      throw new Error('댓글 등록에 실패했습니다.')
    }

    const updatedPost = await res.json()
    posts.value = posts.value.map((post) => (post.id === postId ? updatedPost : post))
    commentDrafts.value = { ...commentDrafts.value, [postId]: '' }
    successMessage.value = '댓글이 등록되었습니다.'
  } catch (err) {
    errorMessage.value = err.message
  }
}

function connectSocket() {
  const clientId = Date.now()
  const wsBase = (import.meta.env.VITE_API_BASE_URL || 'https://localhub-ssafy-34ya.onrender.com').replace(/^https?:/, 'wss:')
  socket.value = new WebSocket(`${wsBase}/ws/notifications?client_id=${clientId}`)

  socket.value.onmessage = (event) => {
    const data = JSON.parse(event.data)

    if (data.type === 'presence') {
      onlineCount.value = data.count
    }

    if (data.type === 'new_post' && lastNotificationId.value !== data.post.id) {
      posts.value = [data.post, ...posts.value.filter((post) => post.id !== data.post.id)]
      notificationMessage.value = '새 게시글이 등록되었습니다.'
      lastNotificationId.value = data.post.id
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
  if (socket.value) {
    socket.value.close()
  }
  if (reconnectTimer.value) {
    clearTimeout(reconnectTimer.value)
  }
})
</script>
<template>
  <div class="page" :style="skyStyle">

    <section class="hero">
      <h1>서울 익명 커뮤니티</h1>
      <p>
        지역과 주제를 함께 선택해서 이야기를 나누고<br>
        좋아요·조회수·댓글로 더 활발한 소통을 경험해보세요.
      </p>

      <div class="sunset-controller">
        <div class="sunset-labels">
          <span :class="{ active: sunsetProgress <= 33 }">Golden</span>
          <span :class="{ active: sunsetProgress > 33 && sunsetProgress <= 70 }">Magenta</span>
          <span :class="{ active: sunsetProgress > 70 }">Twilight</span>
        </div>

        <input v-model="sunsetProgress" type="range" min="0" max="100" class="sunset-slider" />

        <div class="sunset-times">
          <span>17:20</span>
          <span>20:40</span>
        </div>
      </div>

      <div class="status">
        현재 접속자 <strong>{{ onlineCount }}</strong> 명
      </div>
    </section>

    <section class="section-title">
      <h2>Seoul Map</h2>
      <p>지역 기반 익명 커뮤니티</p>
    </section>

    <MapView />

    <section class="panel write-panel">
      <h2>{{ editingId ? '게시글 수정' : '새 게시글 작성' }}</h2>

      <form @submit.prevent="submitForm">
        <label>
          제목
          <input v-model="form.title" placeholder="제목을 입력하세요" />
        </label>

        <label>
          내용
          <textarea v-model="form.content" rows="6" placeholder="내용을 입력하세요" />
        </label>

        <div class="meta-grid">
          <label>
            지역 선택
            <select v-model="communityMeta.region">
              <option v-for="region in options.regions" :key="region" :value="region">
                {{ region }}
              </option>
            </select>
          </label>

          <label>
            카테고리 선택
            <select v-model="communityMeta.category">
              <option v-for="categoryOption in options.categories" :key="categoryOption" :value="categoryOption">
                {{ categoryOption }}
              </option>
            </select>
          </label>
        </div>

        <label>
          수정 / 삭제 비밀번호
          <input v-model="form.password" type="password" placeholder="비밀번호" />
        </label>

        <div class="actions">
          <button type="submit">{{ editingId ? '수정하기' : '등록하기' }}</button>
          <button v-if="editingId" type="button" class="secondary" @click="resetForm">취소</button>
        </div>
      </form>
    </section>

    <section class="panel community-panel">
      <div class="section-header">
        <div>
          <h2>Community <span>Board</span></h2>
          <p>서울 지역 사용자들의 실시간 이야기</p>
        </div>

        <button class="secondary" @click="fetchPosts">새로고침</button>
      </div>

      <div v-if="notificationMessage" class="notification">{{ notificationMessage }}</div>
      <p v-if="loading">불러오는 중...</p>
      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
      <p v-if="successMessage" class="success">{{ successMessage }}</p>

      <div v-if="posts.length === 0 && !loading" class="empty">
        아직 등록된 게시글이 없습니다.
      </div>

      <article v-for="post in posts" :key="post.id" class="card" :class="{ popular: isPopular(post) }">
        <div class="card-header">
          <div class="card-title-row">
            <span class="badge">{{ post.region }} · {{ post.category }}</span>
            <span v-if="isPopular(post)" class="hot-badge">인기</span>
          </div>
          <h3 @click="togglePost(post)">{{ post.title }}</h3>
          <time>{{ new Date(post.created_at).toLocaleString() }}</time>
        </div>

        <div class="summary-row">
          <span>좋아요 {{ post.like_count || 0 }}</span>
          <span>조회 {{ post.view_count || 0 }}</span>
          <span>댓글 {{ (post.comments || []).length }}</span>
        </div>

        <div class="card-actions">
          <button class="secondary" @click="likePost(post.id)">좋아요</button>
          <button class="secondary" @click="togglePost(post)">{{ expandedPostIds.includes(post.id) ? '내용 접기' : '내용 보기' }}</button>
          <button class="secondary" @click="startEdit(post)">수정</button>
        </div>

        <div v-if="expandedPostIds.includes(post.id)" class="content-panel">
          <div class="content">{{ post.content }}</div>

          <div class="comment-box">
            <h4>댓글</h4>
            <div v-if="(post.comments || []).length === 0" class="empty-comment">첫 댓글을 남겨보세요.</div>
            <div v-for="comment in post.comments || []" :key="comment.id" class="comment-item">
              <p>{{ comment.content }}</p>
              <span>{{ new Date(comment.created_at).toLocaleString() }}</span>
            </div>

            <div class="comment-form">
              <textarea v-model="commentDrafts[post.id]" rows="3" placeholder="댓글을 입력하세요" />
              <button type="button" class="secondary" @click="submitComment(post.id)">댓글 등록</button>
            </div>
          </div>
        </div>

        <div class="delete-box">
          <input v-model="deletePasswords[post.id]" type="password" placeholder="삭제 비밀번호" />
          <button class="delete" @click="deletePost(post.id)">삭제</button>
        </div>
      </article>
    </section>
  </div>
</template>

<style scoped>

*{
  box-sizing:border-box;
}


.page{

  max-width:1400px;

  margin:auto;

  padding:60px 40px;

  min-height:100vh;

  color:#f8fafc;

  transition:1s;

}



.page::before{

  content:"";

  position:fixed;

  inset:0;

  background:
  radial-gradient(circle,white 1px,transparent 1px);

  background-size:120px 120px;

  opacity:.12;

  pointer-events:none;

}





.hero{

  text-align:center;

  padding:80px 20px;

}



.hero h1{

  font-size:72px;

  font-weight:900;

  line-height:1.1;

  margin:0;


  background:
  linear-gradient(
    135deg,
    #fff,
    #ffd369,
    #818cf8
  );


  -webkit-background-clip:text;

  color:transparent;

}



.hero h1 span{

  display:block;

  font-size:28px;

  letter-spacing:8px;

  margin-top:15px;

}




.hero p{

  margin-top:25px;

  color:#cbd5e1;

  font-size:18px;

  line-height:1.8;

}





.sunset-controller{

  max-width:520px;

  margin:40px auto;

  padding:25px;

  border-radius:24px;

  background:
  rgba(255,255,255,.08);

  backdrop-filter:blur(20px);

}



.sunset-labels,
.sunset-times{

  display:flex;

  justify-content:space-between;

}



.sunset-labels span{

  color:#94a3b8;

}



.sunset-labels .active{

  color:white;

  font-weight:bold;

}



.sunset-slider{

  width:100%;

  margin:20px 0;

}



.status{

  font-size:18px;

}


.status strong{

  color:#ffd369;

}







.section-title{

  margin:40px 0 20px;

}


.section-title h2{

  font-size:36px;

}


.section-title p{

  color:#94a3b8;

}






.panel{

  margin-top:40px;

  padding:35px;


  border-radius:30px;


  background:
  rgba(15,23,42,.65);


  border:
  1px solid rgba(255,255,255,.1);


  backdrop-filter:blur(25px);


  box-shadow:
  0 20px 60px rgba(0,0,0,.35);

}






form{

 display:flex;

 flex-direction:column;

 gap:20px;

}



label{

 display:flex;

 flex-direction:column;

 gap:10px;

 font-weight:bold;

}



input,
textarea{

 padding:16px;

 border-radius:16px;


 border:
 1px solid rgba(255,255,255,.15);


 background:
 rgba(255,255,255,.06);


 color:white;


}





.actions,
.section-header,
.card-footer{

 display:flex;

 justify-content:space-between;

 align-items:center;

 gap:15px;

}





button{

 padding:12px 22px;

 border-radius:14px;

 border:none;

 cursor:pointer;


 background:
 linear-gradient(
 135deg,
 #ffd369,
 #ffb347
 );


 font-weight:bold;

}



button:hover{

 transform:translateY(-2px);

}



.secondary{

 background:
 rgba(255,255,255,.1);


 color:white;

}



.delete{

 background:
 linear-gradient(
 135deg,
 #fb7185,
 #ef4444
 );

 color:white;

}






.section-header h2{

 font-size:42px;

 margin:0;

}


.section-header h2 span{

 color:#ffd369;

}



.section-header p{

 color:#94a3b8;

}






.card{

 margin-top:25px;

 padding:30px;


 border-radius:25px;


 background:
 rgba(255,255,255,.06);


 border:
 1px solid rgba(255,255,255,.12);


 transition:.3s;

}




.card:hover{

 transform:translateY(-5px);

 border-color:#ffd369;

}




.card-header{

 display:flex;

 justify-content:space-between;

 align-items:center;

 padding-bottom:18px;

 border-bottom:
 1px solid rgba(255,255,255,.1);

}



.card-header h3{

 font-size:24px;

 margin:0;

}



.card-header time{

 color:#94a3b8;

 font-size:14px;

}



.content{

 padding:25px 0;

 color:#e2e8f0;

 line-height:1.8;

 white-space:pre-line;

}





.delete-box{

 display:flex;

 gap:10px;

}



.delete-box input{

 width:180px;

}




.notification{

 margin-top:20px;

 padding:15px;

 border-radius:15px;

 background:#064e3b;

}



.error{

 color:#fb7185;

}



.success{

 color:#4ade80;

}



.empty{

 padding:40px;

 text-align:center;

 color:#94a3b8;

}





@media(max-width:768px){


.page{

 padding:30px 20px;

}


.hero h1{

 font-size:45px;

}


.hero h1 span{

 font-size:18px;

}


.section-header h2{

 font-size:30px;

}


.card-header,
.card-footer{

 flex-direction:column;

 align-items:flex-start;

}


.delete-box{

 width:100%;

}


.delete-box input{

 width:100%;

}


}

</style>