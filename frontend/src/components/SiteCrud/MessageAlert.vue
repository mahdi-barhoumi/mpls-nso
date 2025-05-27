<template>
  <Message
    v-if="message"
    :severity="getSeverity(type)"
    :closable="closable"
    class="mb-4"
    @close="handleClose"
  >
    <template #messageicon>
      <i :class="getIcon(type)" class="mr-2"></i>
    </template>
    {{ message }}
  </Message>
</template>

<script setup>
const props = defineProps({
  message: String,
  type: {
    type: String,
    default: 'success',
  },
  closable: {
    type: Boolean,
    default: true,
  },
})

const emit = defineEmits(['close'])

const getSeverity = (type) => {
  switch (type) {
    case 'error':
      return 'error'
    case 'success':
      return 'success'
    case 'warning':
      return 'warn'
    case 'info':
      return 'info'
    default:
      return 'success'
  }
}

const getIcon = (type) => {
  switch (type) {
    case 'error':
      return 'pi pi-times-circle'
    case 'success':
      return 'pi pi-check-circle'
    case 'warning':
      return 'pi pi-exclamation-triangle'
    case 'info':
      return 'pi pi-info-circle'
    default:
      return 'pi pi-check-circle'
  }
}

const handleClose = () => {
  emit('close')
}
</script>
