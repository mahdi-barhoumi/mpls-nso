<template>
  <tr
    class="router-row"
    :class="{
      selected: isSelected,
      stale: isDataStale(router.timestamp),
    }"
    @click="$emit('click')"
  >
    <td>
      <strong>{{ router.hostname }}</strong>
      <small>ID: {{ router.router_id }}</small>
    </td>
    <td>
      <span :class="getStatusClass(router)">
        {{ getStatusText(router) }}
      </span>
    </td>
    <td>
      <MetricCell
        :value="router.cpu_usage_5m"
        :secondary-values="{
          '5s': router.cpu_usage_5s,
          '1m': router.cpu_usage_1m,
        }"
        :alert-threshold="70"
        :warning-threshold="50"
      />
    </td>
    <td>
      <MetricCell
        :value="router.mem_used_percent"
        :total="router.mem_total"
        :used="router.mem_used"
        :alert-threshold="80"
        :warning-threshold="60"
      />
    </td>
    <td>
      <MetricCell
        :value="router.storage_used_percent"
        :total="router.storage_total"
        :used="router.storage_used"
        :alert-threshold="80"
        :warning-threshold="60"
      />
    </td>
    <td>{{ formatTimeDetailed(router.timestamp) }}</td>
    <td :class="{ stale: isDataStale(router.timestamp) }">
      {{ getDataAge(router.timestamp) }}
    </td>
  </tr>
</template>

<script setup>
import MetricCell from './MetricCell.vue'
import { formatUtils } from './utils/formatUtils'

const props = defineProps({
  router: Object,
  isSelected: Boolean,
})

defineEmits(['click'])

const { formatTimeDetailed, getDataAge, isDataStale } = formatUtils

const getStatusClass = (router) => {
  if (isDataStale(router.timestamp)) return 'stale'
  return 'online'
}

const getStatusText = (router) => {
  if (isDataStale(router.timestamp)) return 'Stale Data'
  return 'Online'
}
</script>

<style scoped>
.router-row {
  cursor: pointer;
  transition: background-color 0.2s;
}

.router-row:hover {
  background-color: #f8f9fa;
}

.router-row.selected {
  background-color: #e3f2fd;
}

.router-row.stale {
  background-color: #fff3cd;
}

.router-row td {
  padding: 12px;
  border-bottom: 1px solid #dee2e6;
}

.router-row small {
  display: block;
  color: #6c757d;
  font-size: 12px;
}

.status-up {
  color: #28a745;
}
.status-down {
  color: #dc3545;
}
.stale {
  color: #ffc107;
}
.online {
  color: #28a745;
}
</style>
