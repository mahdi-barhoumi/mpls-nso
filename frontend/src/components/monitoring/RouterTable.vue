<template>
  <table class="router-table">
    <thead>
      <tr>
        <th>Hostname</th>
        <th>Status</th>
        <th>CPU Usage</th>
        <th>Memory Usage</th>
        <th>Storage Usage</th>
        <th>Last Updated</th>
        <th>Data Age</th>
      </tr>
    </thead>
    <tbody>
      <RouterRow
        v-for="router in routers"
        :key="router.id"
        :router="router"
        :is-selected="selectedRouter?.id === router.id"
        @click="$emit('router-selected', router)"
      />
    </tbody>
  </table>
</template>

<script setup>
import RouterRow from './RouterRow.vue'

const props = defineProps({
  routers: Array,
  selectedRouter: Object,
})

defineEmits(['router-selected'])
</script>

<style scoped>
.router-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.router-table th {
  background: #f8f9fa;
  padding: 12px;
  text-align: left;
  font-weight: 600;
  color: #495057;
  border-bottom: 2px solid #dee2e6;
}
</style>
