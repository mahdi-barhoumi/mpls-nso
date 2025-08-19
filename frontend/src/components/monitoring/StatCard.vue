<template>
  <div class="stat-card" :class="{ alert }">
    <h3>{{ title }}</h3>
    <p>{{ value }}</p>
    <small>{{ subtitle }}</small>
  </div>
</template>

<script setup>
const props = defineProps({
  title: String,
  value: String,
  subtitle: String,
  alert: Boolean,
})
</script>

<style scoped>
.stat-card {
  border: 1px solid #ddd;
  padding: 20px;
  border-radius: 8px;
  background: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.stat-card h3 {
  margin: 0 0 10px 0;
  color: #333;
}

.stat-card p {
  margin: 0 0 5px 0;
  font-size: 18px;
  font-weight: bold;
}

.stat-card small {
  color: #666;
  font-size: 12px;
}

.stat-card.alert {
  background-color: #fff5f5;
  border-color: #fed7d7;
}
</style>
