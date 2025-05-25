<template>
  <div class="metrics-chart">
    <h3>Performance History</h3>
    <div class="chart-controls">
      <select :value="selectedMetric" @change="$emit('metric-changed', $event.target.value)">
        <option value="cpu_usage_5m">CPU Usage (5m avg)</option>
        <option value="cpu_usage_1m">CPU Usage (1m avg)</option>
        <option value="cpu_usage_5s">CPU Usage (5s avg)</option>
        <option value="mem_used_percent">Memory Usage</option>
        <option value="storage_used_percent">Storage Usage</option>
      </select>
      <select :value="timeRange" @change="$emit('time-range-changed', $event.target.value)">
        <option value="1">Last 1 Hour</option>
        <option value="6">Last 6 Hours</option>
        <option value="24">Last 24 Hours</option>
        <option value="168">Last 7 Days</option>
      </select>
      <button @click="$emit('refresh')" class="refresh-btn">Refresh Data</button>
    </div>

    <div v-if="history.length" class="chart-container">
      <canvas ref="chartCanvas" width="1000" height="400"></canvas>
      <ChartLegend :stats="getChartStats()" />
    </div>
    <div v-else class="no-data">
      <p>No historical data available for the selected time range</p>
      <button @click="$emit('refresh')" class="retry-btn">Retry Loading</button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import ChartLegend from './ChartLegend.vue'

const props = defineProps({
  history: Array,
  selectedMetric: String,
  timeRange: String,
})

const emit = defineEmits(['metric-changed', 'time-range-changed', 'refresh'])

const chartCanvas = ref(null)

const getChartStats = () => {
  if (!props.history.length) return { min: 0, max: 0, avg: 0 }

  const values = props.history
    .map((point) => point[props.selectedMetric] || 0)
    .filter((val) => val !== null && val !== undefined)

  if (values.length === 0) return { min: 0, max: 0, avg: 0 }

  const min = Math.min(...values).toFixed(1)
  const max = Math.max(...values).toFixed(1)
  const avg = (values.reduce((a, b) => a + b, 0) / values.length).toFixed(1)

  return { min, max, avg }
}

const drawChart = () => {
  if (!chartCanvas.value || !props.history.length) return

  const canvas = chartCanvas.value
  const ctx = canvas.getContext('2d')
  const width = canvas.width
  const height = canvas.height

  // Clear canvas
  ctx.clearRect(0, 0, width, height)

  // Get data points with proper time parsing
  const dataPoints = props.history
    .map((point) => ({
      value: point[props.selectedMetric] || 0,
      timestamp: new Date(point.timestamp),
    }))
    .filter((point) => !isNaN(point.timestamp.getTime()))

  if (dataPoints.length === 0) return

  // Set up chart area
  const padding = 70
  const chartWidth = width - 2 * padding
  const chartHeight = height - 2 * padding

  // Find min/max values and times
  const values = dataPoints.map((p) => p.value)
  const maxValue = Math.max(...values, 100)
  const minValue = Math.min(...values, 0)
  const valueRange = maxValue - minValue || 1

  const minTime = Math.min(...dataPoints.map((p) => p.timestamp.getTime()))
  const maxTime = Math.max(...dataPoints.map((p) => p.timestamp.getTime()))
  const timeRange = maxTime - minTime || 1

  // Draw background
  ctx.fillStyle = '#fafafa'
  ctx.fillRect(padding, padding, chartWidth, chartHeight)

  // Draw grid and labels
  ctx.strokeStyle = '#e0e0e0'
  ctx.lineWidth = 1
  ctx.fillStyle = '#666'
  ctx.font = '12px Arial'

  // Horizontal grid lines (Y-axis)
  for (let i = 0; i <= 5; i++) {
    const y = padding + (i * chartHeight) / 5
    ctx.beginPath()
    ctx.moveTo(padding, y)
    ctx.lineTo(width - padding, y)
    ctx.stroke()

    // Y-axis labels
    const value = maxValue - (i * valueRange) / 5
    ctx.fillText(value.toFixed(1) + '%', 5, y + 4)
  }

  // Vertical grid lines (X-axis) - show time labels
  const timeLabels = Math.min(8, dataPoints.length)
  for (let i = 0; i <= timeLabels; i++) {
    const x = padding + (i * chartWidth) / timeLabels
    ctx.beginPath()
    ctx.moveTo(x, padding)
    ctx.lineTo(x, height - padding)
    ctx.stroke()

    // Time labels
    if (i > 0 && i < timeLabels) {
      const timePoint = new Date(minTime + (i * timeRange) / timeLabels)
      const timeLabel = timePoint.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
      ctx.save()
      ctx.translate(x, height - padding + 15)
      ctx.rotate(-Math.PI / 4)
      ctx.fillText(timeLabel, 0, 0)
      ctx.restore()
    }
  }

  // Draw threshold lines based on metric type
  const drawThresholdLine = (threshold, color, label) => {
    const y = padding + chartHeight - ((threshold - minValue) / valueRange) * chartHeight
    if (y >= padding && y <= padding + chartHeight) {
      ctx.strokeStyle = color
      ctx.lineWidth = 1
      ctx.setLineDash([5, 5])
      ctx.beginPath()
      ctx.moveTo(padding, y)
      ctx.lineTo(width - padding, y)
      ctx.stroke()
      ctx.setLineDash([])

      // Label
      ctx.fillStyle = color
      ctx.font = '11px Arial'
      ctx.fillText(label, width - padding + 5, y + 4)
    }
  }

  if (props.selectedMetric.includes('cpu')) {
    drawThresholdLine(50, '#ffa500', 'Warning (50%)')
    drawThresholdLine(70, '#ff4444', 'Critical (70%)')
  } else if (props.selectedMetric.includes('mem') || props.selectedMetric.includes('storage')) {
    drawThresholdLine(60, '#ffa500', 'Warning (60%)')
    drawThresholdLine(80, '#ff4444', 'Critical (80%)')
  }

  // Draw area fill
  ctx.fillStyle = 'rgba(0, 123, 255, 0.1)'
  ctx.beginPath()
  dataPoints.forEach((point, index) => {
    const x = padding + ((point.timestamp.getTime() - minTime) / timeRange) * chartWidth
    const y = padding + chartHeight - ((point.value - minValue) / valueRange) * chartHeight

    if (index === 0) {
      ctx.moveTo(x, y)
    } else {
      ctx.lineTo(x, y)
    }
  })
  ctx.lineTo(padding + chartWidth, padding + chartHeight)
  ctx.lineTo(padding, padding + chartHeight)
  ctx.closePath()
  ctx.fill()

  // Draw main line
  ctx.strokeStyle = '#007bff'
  ctx.lineWidth = 3
  ctx.beginPath()
  dataPoints.forEach((point, index) => {
    const x = padding + ((point.timestamp.getTime() - minTime) / timeRange) * chartWidth
    const y = padding + chartHeight - ((point.value - minValue) / valueRange) * chartHeight

    if (index === 0) {
      ctx.moveTo(x, y)
    } else {
      ctx.lineTo(x, y)
    }
  })
  ctx.stroke()

  // Draw data points
  ctx.fillStyle = '#007bff'
  dataPoints.forEach((point) => {
    const x = padding + ((point.timestamp.getTime() - minTime) / timeRange) * chartWidth
    const y = padding + chartHeight - ((point.value - minValue) / valueRange) * chartHeight

    ctx.beginPath()
    ctx.arc(x, y, 4, 0, 2 * Math.PI)
    ctx.fill()
  })

  // Chart title and current value
  ctx.fillStyle = '#333'
  ctx.font = 'bold 16px Arial'
  const title = props.selectedMetric.replace(/_/g, ' ').toUpperCase()
  ctx.fillText(title, padding, 25)

  // Current value display
  const currentValue = dataPoints[dataPoints.length - 1]?.value || 0
  ctx.font = 'bold 14px Arial'
  ctx.fillStyle = currentValue >= 70 ? '#ff4444' : currentValue >= 50 ? '#ffa500' : '#28a745'
  ctx.fillText(`Current: ${currentValue.toFixed(1)}%`, width - 150, 25)

  // Data points count
  ctx.fillStyle = '#666'
  ctx.font = '12px Arial'
  ctx.fillText(`${dataPoints.length} data points`, width - 150, 45)
}

// Watch for changes and redraw chart
watch(
  () => [props.history, props.selectedMetric],
  async () => {
    await nextTick()
    drawChart()
  },
  { deep: true },
)
</script>

<style scoped>
.metrics-chart {
  margin-bottom: 30px;
}

.chart-controls {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
  align-items: center;
}

.chart-controls select,
.chart-controls button {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.refresh-btn,
.retry-btn {
  background: #007bff;
  color: white;
  border: none;
  cursor: pointer;
}

.refresh-btn:hover,
.retry-btn:hover {
  background: #0056b3;
}

.chart-container {
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.no-data {
  text-align: center;
  padding: 40px;
  background: #f8f9fa;
  border-radius: 8px;
  color: #6c757d;
}
</style>
