<template>
  <div class="metric-cell" :class="getAlertClass">
    <div class="metric-values">
      <strong>{{ formatPercentage(value) }}</strong>
      <small v-if="secondaryValues">
        <span v-for="(val, key) in secondaryValues" :key="key">
          {{ key }}: {{ formatPercentage(val)
          }}{{ key !== Object.keys(secondaryValues).pop() ? ' | ' : '' }}
        </span>
      </small>
      <small v-if="total"> {{ formatBytes(used || 0) }} / {{ formatBytes(total) }} </small>
    </div>
    <div class="usage-bar">
      <div class="usage-fill" :style="{ width: (value || 0) + '%' }"></div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatUtils } from './utils/formatUtils'

const props = defineProps({
  value: Number,
  secondaryValues: Object,
  total: Number,
  used: Number,
  alertThreshold: Number,
  warningThreshold: Number,
})

const { formatPercentage, formatBytes } = formatUtils

const getAlertClass = computed(() => {
  if (!props.value) return ''
  if (props.value >= props.alertThreshold) return 'alert'
  if (props.value >= props.warningThreshold) return 'warning'
  return ''
})
</script>

<style scoped>
.metric-cell {
  min-width: 120px;
}

.metric-values strong {
  display: block;
  font-size: 14px;
}

.metric-values small {
  display: block;
  color: #6c757d;
  font-size: 11px;
  margin-top: 2px;
}

.usage-bar {
  height: 4px;
  background: #e9ecef;
  border-radius: 2px;
  margin-top: 4px;
  overflow: hidden;
}

.usage-fill {
  height: 100%;
  background: #007bff;
  transition: width 0.3s ease;
}

.metric-cell.warning .usage-fill {
  background: #ffc107;
}

.metric-cell.alert .usage-fill {
  background: #dc3545;
}
</style>
