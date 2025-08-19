<template>
  <div class="chart-legend">
    <div class="legend-item"><span class="legend-color normal"></span> Normal (< 50%)</div>
    <div class="legend-item"><span class="legend-color warning"></span> Warning (50-70%)</div>
    <div class="legend-item"><span class="legend-color alert"></span> Critical (> 70%)</div>
    <div class="chart-stats">
      Min: {{ stats.min }}% | Max: {{ stats.max }}% | Avg: {{ stats.avg }}%
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  stats: Object,
})
</script>

<style scoped>
.chart-legend {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #dee2e6;
  font-size: 14px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 2px;
}

.legend-color.normal {
  background: #28a745;
}

.legend-color.warning {
  background: #ffc107;
}

.legend-color.alert {
  background: #dc3545;
}

.chart-stats {
  font-weight: 600;
  color: #495057;
}
</style>
