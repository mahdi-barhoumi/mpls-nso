<template>
  <div class="interface-card">
    <div class="interface-header">
      <h4>{{ interface.name }}</h4>
      <span :class="interface.operational_status === 'up' ? 'status-up' : 'status-down'">
        {{ interface.operational_status }}
      </span>
    </div>
    <div class="interface-metrics">
      <div class="traffic-metrics">
        <div class="traffic-item">
          <label>In Traffic:</label>
          <span>{{ formatBandwidth(interface.bps_in) }}</span>
        </div>
        <div class="traffic-item">
          <label>Out Traffic:</label>
          <span>{{ formatBandwidth(interface.bps_out) }}</span>
        </div>
        <div class="traffic-item">
          <label>Total Traffic:</label>
          <span>{{ formatBandwidth((interface.bps_in || 0) + (interface.bps_out || 0)) }}</span>
        </div>
      </div>

      <div
        class="error-metrics"
        v-if="(interface.in_errors || 0) + (interface.out_errors || 0) > 0"
      >
        <div class="error-item alert">
          <label>Errors In:</label>
          <span>{{ interface.in_errors || 0 }}</span>
        </div>
        <div class="error-item alert">
          <label>Errors Out:</label>
          <span>{{ interface.out_errors || 0 }}</span>
        </div>
      </div>

      <div class="interface-footer">
        <small>Updated: {{ formatTimeDetailed(interface.timestamp) }}</small>
      </div>
    </div>
  </div>
</template>

<script setup>
import { formatUtils } from './utils/formatUtils'

const props = defineProps({
  interface: Object,
})

const { formatTimeDetailed } = formatUtils

const formatBandwidth = (bps) => {
  if (!bps) return '0 bps'

  const units = ['bps', 'Kbps', 'Mbps', 'Gbps']
  let value = bps
  let unitIndex = 0

  while (value >= 1000 && unitIndex < units.length - 1) {
    value /= 1000
    unitIndex++
  }

  return `${value.toFixed(1)} ${units[unitIndex]}`
}
</script>

<style scoped>
.interface-card {
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.interface-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #dee2e6;
}

.interface-header h4 {
  margin: 0;
  color: #495057;
}

.status-up {
  color: #28a745;
  font-weight: 600;
  text-transform: uppercase;
  font-size: 12px;
}

.status-down {
  color: #dc3545;
  font-weight: 600;
  text-transform: uppercase;
  font-size: 12px;
}

.traffic-metrics {
  margin-bottom: 15px;
}

.traffic-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
}

.traffic-item label {
  color: #6c757d;
  font-weight: 500;
}

.error-metrics {
  margin-bottom: 15px;
  padding: 10px;
  background: #fff5f5;
  border: 1px solid #fed7d7;
  border-radius: 4px;
}

.error-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
  font-size: 14px;
}

.error-item.alert {
  color: #721c24;
}

.error-item label {
  font-weight: 500;
}

.interface-footer {
  padding-top: 10px;
  border-top: 1px solid #dee2e6;
  text-align: center;
}

.interface-footer small {
  color: #6c757d;
  font-size: 12px;
}
</style>
