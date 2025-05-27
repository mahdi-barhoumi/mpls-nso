<template>
  <div
    v-if="message"
    :style="{
      padding: '10px',
      marginTop: '20px',
      backgroundColor: type === 'error' ? '#f8d7da' : '#d4edda',
      color: type === 'error' ? '#721c24' : '#155724',
      border: '1px solid ' + (type === 'error' ? '#f5c6cb' : '#c3e6cb'),
      borderRadius: '4px',
    }"
  >
    {{ message }}
  </div>
</template>

<script setup>
defineProps({
  message: String,
  type: {
    type: String,
    default: 'success',
  },
})
</script>
