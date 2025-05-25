<template>
  <div class="interfaces-section">
    <h3>Network Interfaces</h3>
    <div v-if="interfaces.length" class="interfaces-grid">
      <InterfaceCard v-for="iface in interfaces" :key="iface.interface_id" :interface="iface" />
    </div>
    <div v-else class="no-data">
      <p>No interface data available</p>
    </div>
  </div>
</template>

<script setup>
import InterfaceCard from './InterfaceCard.vue'

const props = defineProps({
  interfaces: Array,
})
</script>

<style scoped>
.interfaces-section {
  margin-top: 30px;
}

.interfaces-section h3 {
  margin-bottom: 20px;
  color: #495057;
}

.interfaces-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
}

.no-data {
  text-align: center;
  padding: 40px;
  background: #f8f9fa;
  border-radius: 8px;
  color: #6c757d;
}
</style>
