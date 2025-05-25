<template>
  <div class="details-section">
    <h2>{{ router.hostname }} - Performance Dashboard</h2>

    <StatusCards :router="router" />

    <PerformanceChart
      :history="history"
      :selected-metric="selectedMetric"
      :time-range="timeRange"
      @metric-changed="$emit('metric-changed', $event)"
      @time-range-changed="$emit('time-range-changed', $event)"
      @refresh="$emit('refresh-history')"
    />

    <InterfacesList :interfaces="interfaces" />
  </div>
</template>

<script setup>
import StatusCards from './StatusCards.vue'
import PerformanceChart from './PerformanceChart.vue'
import InterfacesList from './InterfacesList.vue'

const props = defineProps({
  router: Object,
  history: Array,
  interfaces: Array,
  selectedMetric: String,
  timeRange: String,
})

defineEmits(['metric-changed', 'time-range-changed', 'refresh-history'])
</script>

<style scoped>
.details-section {
  margin-top: 30px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
</style>
