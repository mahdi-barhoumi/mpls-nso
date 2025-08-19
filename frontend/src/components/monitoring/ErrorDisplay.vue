<template>
  <div class="error">
    <strong>Error:</strong> {{ error }}
    <button @click="$emit('close')" class="close-error">×</button>
  </div>
</template>

<script setup>
const props = defineProps({
  error: String,
})

defineEmits(['close'])
</script>

<style scoped>
.error {
  background: #f8d7da;
  color: #721c24;
  padding: 12px 16px;
  border: 1px solid #f5c6cb;
  border-radius: 4px;
  margin: 20px 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.close-error {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  padding: 0;
  margin-left: 10px;
}
</style>
