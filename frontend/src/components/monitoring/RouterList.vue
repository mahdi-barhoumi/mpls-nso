<template>
  <div class="router-section">
    <h2>Routers</h2>
    <div class="controls">
      <input v-model="searchQuery" type="text" placeholder="Search routers..." />
      <select v-model="sortBy">
        <option value="hostname">Sort by Hostname</option>
        <option value="cpu_usage_5m">Sort by CPU Usage</option>
        <option value="mem_used_percent">Sort by Memory Usage</option>
        <option value="timestamp">Sort by Last Update</option>
      </select>
    </div>

    <RouterTable
      :routers="sortedAndFilteredRouters"
      :selected-router="selectedRouter"
      @router-selected="$emit('router-selected', $event)"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import RouterTable from './RouterTable.vue'

const props = defineProps({
  routers: Array,
  selectedRouter: Object,
})

const emit = defineEmits(['router-selected'])

const searchQuery = ref('')
const sortBy = ref('hostname')

const filteredRouters = computed(() => {
  if (!searchQuery.value) return props.routers
  const query = searchQuery.value.toLowerCase()
  return props.routers.filter(
    (router) =>
      router.hostname.toLowerCase().includes(query) || router.router_id.toString().includes(query),
  )
})

const sortedAndFilteredRouters = computed(() => {
  const filtered = [...filteredRouters.value]
  return filtered.sort((a, b) => {
    switch (sortBy.value) {
      case 'hostname':
        return a.hostname.localeCompare(b.hostname)
      case 'cpu_usage_5m':
        return (b.cpu_usage_5m || 0) - (a.cpu_usage_5m || 0)
      case 'mem_used_percent':
        return (b.mem_used_percent || 0) - (a.mem_used_percent || 0)
      case 'timestamp':
        return new Date(b.timestamp) - new Date(a.timestamp)
      default:
        return 0
    }
  })
})
</script>

<style scoped>
.router-section {
  margin-bottom: 30px;
}

.controls {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
  align-items: center;
}

.controls input,
.controls select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}
</style>
