import { computed, ref } from 'vue'

const sunsetProgress = ref(50)

function getTimeFromProgress(progress) {
  const totalMinutes = 24 * 60
  const current = Math.round((progress / 100) * totalMinutes)
  const hours = Math.floor(current / 60) % 24
  const minutes = current % 60
  return { hours, minutes }
}

function formatTime(hours, minutes) {
  const h = String(hours).padStart(2, '0')
  const m = String(minutes).padStart(2, '0')
  return `${h}:${m}`
}

function getSkyStyle(progress) {
  const p = Number(progress) / 100
  const hour = Math.round(p * 24)
  const isNight = hour >= 20 || hour <= 5

  let c1 = '#07111f'
  let c2 = '#3b82f6'
  let c3 = '#67e8f9'

  if (hour >= 6 && hour < 12) {
    c1 = '#0f172a'
    c2 = '#6366f1'
    c3 = '#f59e0b'
  } else if (hour >= 12 && hour < 18) {
    c1 = '#1e1b4b'
    c2 = '#ec4899'
    c3 = '#fb923c'
  } else if (hour >= 18 && hour < 20) {
    c1 = '#111827'
    c2 = '#f43f5e'
    c3 = '#fb923c'
  } else if (isNight) {
    c1 = '#020617'
    c2 = '#111827'
    c3 = '#334155'
  }

  return {
    background: `linear-gradient(135deg, ${c1}, ${c2}, ${c3})`,
    boxShadow: `inset 0 -120px 180px rgba(15, 23, 42, ${0.2 + p * 0.25})`
  }
}

export function useSunsetTheme() {
  const currentTimeLabel = computed(() => {
    const now = new Date()
    const hours = now.getHours()
    const minutes = now.getMinutes()
    return formatTime(hours, minutes)
  })

  const currentTimeValue = computed(() => {
    const now = new Date()
    const totalMinutes = now.getHours() * 60 + now.getMinutes()
    return Math.round((totalMinutes / (24 * 60)) * 100)
  })

  const themeProgress = computed({
    get: () => sunsetProgress.value,
    set: (value) => {
      sunsetProgress.value = Number(value)
    }
  })

  const skyStyle = computed(() => getSkyStyle(sunsetProgress.value))
  const timeLabel = computed(() => {
    const { hours, minutes } = getTimeFromProgress(sunsetProgress.value)
    return formatTime(hours, minutes)
  })

  const timeRangeLabel = computed(() => {
    const { hours, minutes } = getTimeFromProgress(sunsetProgress.value)
    return `${formatTime(hours, minutes)} • ${formatTime((hours + 6) % 24, minutes)}`
  })

  function initializeFromNow() {
    sunsetProgress.value = currentTimeValue.value
  }

  return {
    sunsetProgress: themeProgress,
    skyStyle,
    timeLabel,
    timeRangeLabel,
    currentTimeLabel,
    initializeFromNow
  }
}
