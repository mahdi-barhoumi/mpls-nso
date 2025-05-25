<template>
  <div class="stats-section">
    <h2>Network Overview</h2>
    <div class="stats-grid">
      <StatCard
        title="Routers"
        :value="`${stats.reachable_routers}/${stats.total_routers} Online`"
        :subtitle="`${getPercentage(stats.reachable_routers, stats.total_routers)}% uptime`"
      />

      <StatCard
        title="Interfaces"
        :value="`${stats.enabled_interfaces}/${stats.total_interfaces} Active`"
        :subtitle="`${getPercentage(stats.enabled_interfaces, stats.total_interfaces)}% active`"
      />

      <StatCard
        v-if="stats.high_cpu_routers?.length"
        title="High CPU Alert"
        :value="`${stats.high_cpu_routers.length} routers above 70%`"
        :subtitle="`${getPercentage(stats.high_cpu_routers.length, stats.total_routers)}% of network`"
        alert
      />

      <StatCard
        v-if="stats.high_memory_routers?.length"
        title="Memory Alert"
        :value="`${stats.high_memory_routers.length} routers above 80%`"
        :subtitle="`${getPercentage(stats.high_memory_routers.length, stats.total_routers)}% of network`"
        alert
      />
    </div>

    <div class="update-info">
      <p>Last updated: {{ formatTimeDetailed(lastUpdate) }}</p>
      <p>Next refresh in: {{ refreshCountdown }}s</p>
    </div>
  </div>
</template>

<script setup>
import StatCard from './StatCard.vue'
import { formatUtils } from './utils/formatUtils'

const props = defineProps({
  stats: Object,
  lastUpdate: Date,
  refreshCountdown: Number,
})

const { getPercentage, formatTimeDetailed } = formatUtils
</script>

<style scoped>
.stats-section {
  margin-bottom: 30px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.update-info {
  background: #f8f9fa;
  padding: 10px 15px;
  border-radius: 4px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  color: #666;
}
</style>
