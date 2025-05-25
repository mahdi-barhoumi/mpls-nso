<template>
  <div class="current-status">
    <div class="status-card">
      <h4>CPU Usage</h4>
      <div class="metric-display">
        <span
          class="metric-value large"
          :class="{
            alert: router.cpu_usage_5m >= 70,
            warning: router.cpu_usage_5m >= 50,
          }"
        >
          {{ formatPercentage(router.cpu_usage_5m) }}
        </span>
        <div class="metric-breakdown">
          <div>5 seconds: {{ formatPercentage(router.cpu_usage_5s) }}</div>
          <div>1 minute: {{ formatPercentage(router.cpu_usage_1m) }}</div>
          <div>5 minutes: {{ formatPercentage(router.cpu_usage_5m) }}</div>
        </div>
      </div>
    </div>

    <div class="status-card">
      <h4>Memory Usage</h4>
      <div class="metric-display">
        <span
          class="metric-value large"
          :class="{
            alert: router.mem_used_percent >= 80,
            warning: router.mem_used_percent >= 60,
          }"
        >
          {{ formatPercentage(router.mem_used_percent) }}
        </span>
        <div class="metric-breakdown" v-if="router.mem_total">
          <div>Used: {{ formatBytes(router.mem_used || 0) }}</div>
          <div>Free: {{ formatBytes(router.mem_free || 0) }}</div>
          <div>Total: {{ formatBytes(router.mem_total) }}</div>
        </div>
      </div>
    </div>

    <div class="status-card">
      <h4>Storage Usage</h4>
      <div class="metric-display">
        <span
          class="metric-value large"
          :class="{
            alert: router.storage_used_percent >= 80,
            warning: router.storage_used_percent >= 60,
          }"
        >
          {{ formatPercentage(router.storage_used_percent) }}
        </span>
        <div class="metric-breakdown" v-if="router.storage_total">
          <div>Used: {{ formatBytes(router.storage_used || 0) }}</div>
          <div>Free: {{ formatBytes(router.storage_free || 0) }}</div>
          <div>Total: {{ formatBytes(router.storage_total) }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { formatUtils } from './utils/formatUtils'

const props = defineProps({
  router: Object,
})

const { formatPercentage, formatBytes } = formatUtils
</script>

<style scoped>
.current-status {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.status-card {
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.status-card h4 {
  margin: 0 0 15px 0;
  color: #495057;
  font-size: 16px;
}

.metric-display {
  text-align: center;
}

.metric-value.large {
  display: block;
  font-size: 36px;
  font-weight: bold;
  margin-bottom: 15px;
  color: #28a745;
}

.metric-value.warning {
  color: #ffc107;
}

.metric-value.alert {
  color: #dc3545;
}

.metric-breakdown {
  text-align: left;
  font-size: 14px;
  color: #6c757d;
}

.metric-breakdown div {
  margin-bottom: 4px;
}
</style>
