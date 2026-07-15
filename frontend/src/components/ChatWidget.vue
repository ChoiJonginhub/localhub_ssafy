<template>
  <div class="chat-widget">
    <!-- 플로팅 버튼 -->
    <button
      class="chat-fab"
      :class="{ 'is-open': isOpen }"
      @click="toggleOpen"
      :aria-label="isOpen ? '챗봇 닫기' : '챗봇 열기'"
    >
      <svg v-if="!isOpen" viewBox="0 0 24 24" width="26" height="26" fill="none">
        <path
          d="M4 5.5C4 4.67 4.67 4 5.5 4h13c.83 0 1.5.67 1.5 1.5v10c0 .83-.67 1.5-1.5 1.5H9l-4 4v-4H5.5C4.67 17 4 16.33 4 15.5v-10Z"
          stroke="currentColor"
          stroke-width="1.6"
          stroke-linejoin="round"
        />
      </svg>
      <svg v-else viewBox="0 0 24 24" width="22" height="22" fill="none">
        <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
      </svg>
    </button>

    <!-- 챗 패널 -->
    <transition name="panel-fade">
      <div v-if="isOpen" class="chat-panel">
        <header class="chat-header">
          <div class="chat-header-text">
            <strong>지역 정보 챗봇</strong>
            <span>서울 관광·숙박·축제 정보를 물어보세요</span>
          </div>
        </header>

        <div class="chat-body" ref="bodyRef">
          <div v-if="messages.length === 0" class="chat-empty">
            "강남구 숙박 추천해줘" 처럼 물어보세요.
          </div>

          <div
            v-for="(msg, idx) in messages"
            :key="idx"
            class="chat-bubble-row"
            :class="msg.role"
          >
            <div class="chat-bubble">{{ msg.content }}</div>
          </div>

          <div v-if="isSending" class="chat-bubble-row assistant">
            <div class="chat-bubble chat-typing">
              <span></span><span></span><span></span>
            </div>
          </div>
        </div>

        <form class="chat-input-row" @submit.prevent="sendMessage">
          <input
            v-model="draft"
            type="text"
            placeholder="메시지를 입력하세요"
            :disabled="isSending"
            autocomplete="off"
          />
          <button type="submit" :disabled="isSending || !draft.trim()">전송</button>
        </form>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from "vue";

// 백엔드 주소. Vite 프로젝트라면 .env에 VITE_API_BASE_URL 설정 후 사용 권장
const API_BASE = (import.meta.env.VITE_API_BASE_URL || "https://localhub-ssafy-34ya.onrender.com").replace(/\/$/, "");

const isOpen = ref(false);
const messages = ref([]);
const draft = ref("");
const isSending = ref(false);
const bodyRef = ref(null);
const sessionId = getOrCreateSessionId();

function getOrCreateSessionId() {
  const key = "chat_session_id";
  let id = localStorage.getItem(key);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(key, id);
  }
  return id;
}

async function loadHistory() {
  try {
    const res = await fetch(`${API_BASE}/api/chat/history/${sessionId}`);
    if (!res.ok) return;
    messages.value = await res.json();
    scrollToBottom();
  } catch (e) {
    console.error("대화 기록을 불러오지 못했습니다.", e);
  }
}

function toggleOpen() {
  isOpen.value = !isOpen.value;
  if (isOpen.value && messages.value.length === 0) {
    loadHistory();
  }
}

async function sendMessage() {
  const text = draft.value.trim();
  if (!text || isSending.value) return;

  messages.value.push({ role: "user", content: text, created_at: new Date().toISOString() });
  draft.value = "";
  isSending.value = true;
  scrollToBottom();

  try {
    const res = await fetch(`${API_BASE}/api/chat/send`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, message: text }),
    });

    if (!res.ok) {
      throw new Error(`서버 오류 (${res.status})`);
    }

    const assistantMsg = await res.json();
    messages.value.push(assistantMsg);
  } catch (e) {
    messages.value.push({
      role: "assistant",
      content: "죄송해요, 응답을 받아오지 못했어요. 잠시 후 다시 시도해주세요.",
      created_at: new Date().toISOString(),
    });
    console.error(e);
  } finally {
    isSending.value = false;
    scrollToBottom();
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (bodyRef.value) {
      bodyRef.value.scrollTop = bodyRef.value.scrollHeight;
    }
  });
}

onMounted(() => {
  // 배지 없이 조용히 대기, 열 때 히스토리 로드
});
</script>

<style scoped>
.chat-widget {
  position: fixed;
  right: 20px;
  bottom: 20px;
  z-index: 1000;
  font-family: -apple-system, BlinkMacSystemFont, "Pretendard", "Malgun Gothic", sans-serif;
}

.chat-fab {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  border: none;
  background: #1f2933;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 6px 20px rgba(31, 41, 51, 0.35);
  transition: transform 0.15s ease, background 0.15s ease;
}

.chat-fab:hover {
  transform: translateY(-2px);
  background: #2b3742;
}

.chat-fab.is-open {
  background: #3a4750;
}

.chat-panel {
  position: absolute;
  right: 0;
  bottom: 72px;
  width: 340px;
  max-width: calc(100vw - 32px);
  height: 480px;
  max-height: calc(100vh - 140px);
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 12px 40px rgba(20, 25, 30, 0.18);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-header {
  padding: 14px 16px;
  background: #1f2933;
  color: #fff;
}

.chat-header-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.chat-header-text strong {
  font-size: 15px;
}

.chat-header-text span {
  font-size: 12px;
  color: #b8c2c9;
}

.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: #f6f7f8;
}

.chat-empty {
  margin: auto;
  color: #8a949c;
  font-size: 13px;
  text-align: center;
  padding: 0 20px;
}

.chat-bubble-row {
  display: flex;
}

.chat-bubble-row.user {
  justify-content: flex-end;
}

.chat-bubble-row.assistant {
  justify-content: flex-start;
}

.chat-bubble {
  max-width: 78%;
  padding: 9px 13px;
  border-radius: 14px;
  font-size: 13.5px;
  line-height: 1.45;
  white-space: pre-wrap;
  word-break: break-word;
}

.chat-bubble-row.user .chat-bubble {
  background: #1f2933;
  color: #fff;
  border-bottom-right-radius: 4px;
}

.chat-bubble-row.assistant .chat-bubble {
  background: #ffffff;
  color: #1f2933;
  border: 1px solid #e4e7ea;
  border-bottom-left-radius: 4px;
}

.chat-typing {
  display: flex;
  gap: 4px;
  padding: 12px 14px;
}

.chat-typing span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #a8b0b6;
  animation: blink 1.2s infinite ease-in-out;
}

.chat-typing span:nth-child(2) {
  animation-delay: 0.15s;
}
.chat-typing span:nth-child(3) {
  animation-delay: 0.3s;
}

@keyframes blink {
  0%, 80%, 100% { opacity: 0.25; }
  40% { opacity: 1; }
}

.chat-input-row {
  display: flex;
  gap: 8px;
  padding: 10px;
  border-top: 1px solid #e4e7ea;
  background: #fff;
}

.chat-input-row input {
  flex: 1;
  border: 1px solid #dfe3e6;
  border-radius: 20px;
  padding: 9px 14px;
  font-size: 13.5px;
  outline: none;
}

.chat-input-row input:focus {
  border-color: #1f2933;
}

.chat-input-row button {
  border: none;
  background: #1f2933;
  color: #fff;
  padding: 0 16px;
  border-radius: 20px;
  font-size: 13.5px;
  cursor: pointer;
}

.chat-input-row button:disabled {
  background: #c3c9cd;
  cursor: not-allowed;
}

/* 모바일: 전체 화면 */
@media (max-width: 480px) {
  .chat-panel {
    position: fixed;
    right: 0;
    bottom: 0;
    left: 0;
    top: 0;
    width: 100%;
    max-width: 100%;
    height: 100%;
    max-height: 100%;
    border-radius: 0;
  }

  .chat-widget {
    right: 16px;
    bottom: 16px;
  }
}

.panel-fade-enter-active,
.panel-fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.panel-fade-enter-from,
.panel-fade-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>