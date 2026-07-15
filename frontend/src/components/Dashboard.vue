<script setup>
import { computed, onMounted, ref } from "vue"
import { Bar, Doughnut, Line } from "vue-chartjs"

import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  ArcElement,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement
} from "chart.js"

ChartJS.register(
  Title,
  Tooltip,
  Legend,
  BarElement,
  ArcElement,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement
)

const loading = ref(true)
const errorMessage = ref("")

const statistics = ref({
  total_posts: 0,
  region_count: 0,
  regions: [],
  popular_regions: [],
  categories: [],
  popular_categories: [],
  views: [],
  likes: [],
  category_daily_views: [],
  weekly_posts: [],
  hourly_posts: [],
  top_posts: []
})

const barChartData = computed(() => ({
  labels: statistics.value.regions.map(item => item.region),
  datasets: [
    {
      label: "게시글 수",
      data: statistics.value.regions.map(item => item.post_count),
      backgroundColor: "rgba(122, 162, 255, 0.75)",
      borderColor: "#7AA2FF",
      borderWidth: 1,
      borderRadius: 8,
      borderSkipped: false
    }
  ]
}))

const doughnutChartData = computed(() => ({
  labels: statistics.value.popular_regions.map(item => item.region),
  datasets: [
    {
      label: "게시글 수",
      data: statistics.value.popular_regions.map(item => item.post_count),
      backgroundColor: ["#7AA2FF", "#5EEAD4", "#C084FC", "#FFD369", "#FF7A7A"],
      borderWidth: 0,
      hoverOffset: 10
    }
  ]
}))

const categoryDistributionData = computed(() => ({
  labels: statistics.value.categories.map(item => item.category),
  datasets: [
    {
      label: "카테고리 게시글 수",
      data: statistics.value.categories.map(item => item.post_count),
      backgroundColor: ["#7AA2FF", "#5EEAD4", "#C084FC", "#FFD369", "#FF7A7A", "#F59E0B", "#FB923C", "#A78BFA"],
      borderWidth: 0,
      hoverOffset: 10
    }
  ]
}))

const weeklyPostBarData = computed(() => {
  const labels = statistics.value.weekly_posts.map(item => item.date.slice(5))
  return {
    labels,
    datasets: [
      {
        label: "최근 7일 게시글",
        data: statistics.value.weekly_posts.map(item => item.post_count),
        backgroundColor: "rgba(122, 162, 255, 0.8)",
        borderColor: "#7AA2FF",
        borderWidth: 1,
        borderRadius: 6,
        borderSkipped: false
      }
    ]
  }
})

const hourlyPostLineData = computed(() => ({
  labels: statistics.value.hourly_posts.map(item => `${item.hour}시`),
  datasets: [
    {
      label: "시간대별 방문객 추이",
      data: statistics.value.hourly_posts.map(item => item.visitor_count),
      borderColor: "#5EEAD4",
      backgroundColor: "rgba(94, 234, 212, 0.18)",
      fill: true,
      tension: 0.3,
      pointBackgroundColor: "#5EEAD4",
      pointBorderColor: "#fff"
    }
  ]
}))

const barChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false
    },
    tooltip: {
      callbacks: {
        label(context) {
          return `게시글 ${context.raw}개`
        }
      }
    }
  },
  scales: {
    x: {
      ticks: { color: "#CBD5E1" },
      grid: { display: false }
    },
    y: {
      beginAtZero: true,
      ticks: { color: "#CBD5E1", precision: 0, stepSize: 1 },
      grid: { color: "rgba(148, 163, 184, 0.15)" }
    }
  }
}

const doughnutChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  cutout: "65%",
  plugins: {
    legend: {
      position: "bottom",
      labels: {
        color: "#CBD5E1",
        padding: 20,
        usePointStyle: true
      }
    },
    tooltip: {
      callbacks: {
        label(context) {
          return `${context.label}: ${context.raw}개`
        }
      }
    }
  }
}

const weeklyBarOptions = {
  responsive: true,
  maintainAspectRatio: false,
  indexAxis: "y",
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label(context) {
          return `${context.raw}개`
        }
      }
    }
  },
  scales: {
    x: {
      beginAtZero: true,
      ticks: { color: "#CBD5E1", precision: 0, stepSize: 1 },
      grid: { color: "rgba(148, 163, 184, 0.15)" }
    },
    y: {
      ticks: { color: "#CBD5E1" },
      grid: { display: false }
    }
  }
}

const lineChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label(context) {
          return `${context.raw}개`
        }
      }
    }
  },
  scales: {
    x: {
      ticks: { color: "#CBD5E1" },
      grid: { display: false }
    },
    y: {
      beginAtZero: true,
      ticks: { color: "#CBD5E1", precision: 0, stepSize: 1 },
      grid: { color: "rgba(148, 163, 184, 0.15)" }
    }
  }
}

async function loadStatistics() {
  loading.value = true
  errorMessage.value = ""

  try {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || "https://localhub-ssafy-34ya.onrender.com"}/api/statistics/regions`)

    if (!response.ok) {
      throw new Error(`통계 데이터 요청 실패: ${response.status}`)
    }

    statistics.value = await response.json()
  } catch (error) {
    console.error(error)
    errorMessage.value = "통계 데이터를 불러오지 못했습니다."
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadStatistics()
})
</script>

<template>
  <section class="dashboard">
    <div class="dashboard-header">
      <div>
        <p class="sub-title">
          COMMUNITY STATISTICS
        </p>

        <h2>
          지역 커뮤니티 통계
        </h2>

        <p class="dashboard-desc">
          권역별 게시글 현황과 인기 지역을 확인합니다.
        </p>
      </div>

      <button
        class="refresh-button"
        @click="loadStatistics"
      >
        새로고침
      </button>
    </div>

    <div
      v-if="loading"
      class="message-box"
    >
      통계 데이터를 불러오는 중입니다.
    </div>

    <div
      v-else-if="errorMessage"
      class="message-box error-message"
    >
      {{ errorMessage }}
    </div>

    <template v-else>
      <div class="summary-grid">
        <article class="summary-card">
          <p>전체 게시글</p>

          <strong>
            {{ statistics.total_posts }}
          </strong>

          <span>
            등록된 게시글 수
          </span>
        </article>

        <article class="summary-card">
          <p>활성 권역</p>

          <strong>
            {{ statistics.region_count }}
          </strong>

          <span>
            게시글이 등록된 지역
          </span>
        </article>

        <article class="summary-card popular-card">
          <p>가장 인기 있는 지역</p>

          <strong>
            {{
              statistics.popular_regions[0]?.region
              || "-"
            }}
          </strong>

          <span>
            게시글
            {{
              statistics.popular_regions[0]?.post_count
              || 0
            }}개
          </span>
        </article>
      </div>

      <div
        v-if="statistics.regions.length === 0"
        class="message-box"
      >
        아직 등록된 게시글이 없습니다.
      </div>

      <template v-else>
        <div class="chart-grid">
          <article class="chart-card">
            <div class="chart-header">
              <p>REGION POSTS</p>
              <h3>권역별 게시글 현황</h3>
            </div>
            <div class="bar-chart">
              <Bar :data="barChartData" :options="barChartOptions" />
            </div>
          </article>

          <article class="chart-card">
            <div class="chart-header">
              <p>CATEGORY DISTRIBUTION</p>
              <h3>카테고리 분포</h3>
            </div>
            <div class="doughnut-chart">
              <Doughnut :data="categoryDistributionData" :options="doughnutChartOptions" />
            </div>
          </article>
        </div>

        <div class="chart-grid second-grid">
          <article class="chart-card">
            <div class="chart-header">
              <p>WEEKLY POSTS</p>
              <h3>최근 7일 게시글 추이</h3>
            </div>
            <div class="bar-chart horizontal-bar-chart">
              <Bar :data="weeklyPostBarData" :options="weeklyBarOptions" />
            </div>
          </article>

          <article class="ranking-card">
            <div class="chart-header">
              <p>TOP POSTS</p>
              <h3>인기 게시글 TOP 5</h3>
            </div>

            <div class="ranking-list">
              <div
                v-for="(item, index) in statistics.top_posts"
                :key="item.id"
                class="ranking-item"
              >
                <div class="ranking-left">
                  <span class="ranking-number">
                    {{ index + 1 }}
                  </span>

                  <div class="ranking-text">
                    <strong>{{ item.title }}</strong>
                    <span>{{ item.writer }} · {{ item.category }} · {{ item.region }}</span>
                  </div>
                </div>

                <span class="ranking-count">
                  조회 {{ item.views }} · 좋아요 {{ item.likes }}
                </span>
              </div>
            </div>
          </article>
        </div>

        <article class="chart-card line-card">
          <div class="chart-header">
            <p>VISITOR TREND</p>
            <h3>시간대별 방문객 추이</h3>
          </div>
          <div class="line-chart">
            <Line :data="hourlyPostLineData" :options="lineChartOptions" />
          </div>
        </article>
      </template>
    </template>
  </section>
</template>

<style scoped>
.dashboard {
  margin-top: 80px;
  padding-bottom: 60px;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: end;

  gap: 20px;

  margin-bottom: 30px;
}

.sub-title {
  margin: 0;

  color: #7aa2ff;

  font-size: 13px;
  font-weight: 800;
  letter-spacing: 3px;
}

h2 {
  margin: 10px 0 0;

  color: white;

  font-size: 36px;
  font-weight: 900;
}

.dashboard-desc {
  margin: 10px 0 0;

  color: #94a3b8;
}

.refresh-button {
  padding: 11px 18px;

  border: 1px solid rgba(122, 162, 255, 0.5);
  border-radius: 12px;

  background: rgba(122, 162, 255, 0.15);

  color: #a9c0ff;

  font-size: 14px;
  font-weight: 700;

  cursor: pointer;

  transition: 0.2s;
}

.refresh-button:hover {
  background: rgba(122, 162, 255, 0.28);

  transform: translateY(-2px);
}

.summary-grid {
  display: grid;

  grid-template-columns: repeat(3, 1fr);

  gap: 20px;

  margin-bottom: 20px;
}

.summary-card,
.chart-card,
.ranking-card {
  border: 1px solid rgba(148, 163, 184, 0.15);
  border-radius: 22px;

  background: rgba(15, 23, 42, 0.8);

  box-shadow:
    0 0 40px rgba(122, 162, 255, 0.08);

  backdrop-filter: blur(12px);
}

.summary-card {
  padding: 25px;
}

.summary-card p {
  margin: 0;

  color: #94a3b8;

  font-size: 14px;
}

.summary-card strong {
  display: block;

  margin-top: 12px;

  color: white;

  font-size: 34px;
  font-weight: 900;
}

.summary-card span {
  display: block;

  margin-top: 6px;

  color: #64748b;

  font-size: 13px;
}

.popular-card strong {
  color: #7aa2ff;
}

.chart-grid {
  display: grid;

  grid-template-columns: 2fr 1fr;

  gap: 20px;
}

.second-grid {
  margin-top: 20px;
}

.chart-card {
  padding: 25px;
}

.chart-header p {
  margin: 0;

  color: #7aa2ff;

  font-size: 11px;
  font-weight: 800;
  letter-spacing: 2px;
}

.chart-header h3 {
  margin: 7px 0 0;

  color: white;

  font-size: 21px;
}

.bar-chart {
  height: 340px;

  margin-top: 25px;
}

.doughnut-chart {
  height: 340px;

  margin-top: 25px;
}

.line-chart {
  height: 320px;

  margin-top: 25px;
}

.horizontal-bar-chart {
  height: 280px;
}

.ranking-card {
  margin-top: 20px;

  padding: 25px;
}

.ranking-list {
  display: grid;

  gap: 12px;

  margin-top: 22px;
}

.ranking-item {
  display: flex;
  justify-content: space-between;
  align-items: center;

  padding: 14px 18px;

  border-radius: 14px;

  background: rgba(30, 41, 59, 0.7);
}

.ranking-left {
  display: flex;
  align-items: center;

  gap: 14px;
}

.ranking-number {
  display: flex;
  justify-content: center;
  align-items: center;

  width: 32px;
  height: 32px;

  border-radius: 50%;

  background: rgba(122, 162, 255, 0.18);

  color: #7aa2ff;

  font-weight: 800;
}

.ranking-left strong {
  color: #e2e8f0;
}

.ranking-count {
  color: #94a3b8;
}

.message-box {
  padding: 50px;

  border: 1px solid rgba(148, 163, 184, 0.15);
  border-radius: 20px;

  background: rgba(15, 23, 42, 0.75);

  color: #94a3b8;

  text-align: center;
}

.error-message {
  color: #ff7a7a;
}

.category-list {
  display: grid;
  gap: 12px;
  margin-top: 24px;
}

.category-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border-radius: 14px;
  background: rgba(30, 41, 59, 0.7);
}

.category-name {
  color: #e2e8f0;
  font-weight: 700;
}

.category-count {
  color: #7aa2ff;
  font-weight: 700;
}

.ranking-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ranking-text span {
  color: #94a3b8;
  font-size: 12px;
}

.ranking-count {
  color: #94a3b8;
  font-size: 13px;
  text-align: right;
}

@media (max-width: 900px) {
  .summary-grid,
  .chart-grid {
    grid-template-columns: 1fr;
  }

  .dashboard-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .ranking-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .ranking-count {
    text-align: left;
  }

  h2 {
    font-size: 30px;
  }
}
</style>