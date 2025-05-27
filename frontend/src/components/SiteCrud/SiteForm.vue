<template>
  <div v-if="show" style="border: 1px solid #ccc; padding: 20px; margin: 20px 0">
    <h3>{{ isEditing ? 'Edit Site' : 'Create New Site' }}</h3>

    <div style="margin-bottom: 15px">
      <label>Name*:</label>
      <input
        v-model="formData.name"
        type="text"
        required
        style="width: 100%; padding: 8px; margin-top: 5px"
      />
    </div>

    <div style="margin-bottom: 15px">
      <label>Location:</label>
      <input
        v-model="formData.location"
        type="text"
        style="width: 100%; padding: 8px; margin-top: 5px"
      />
    </div>

    <div style="margin-bottom: 15px">
      <label>Description:</label>
      <textarea
        v-model="formData.description"
        style="width: 100%; padding: 8px; margin-top: 5px; height: 60px"
      ></textarea>
    </div>

    <div v-if="!isEditing" style="margin-bottom: 15px">
      <label>Customer*:</label>
      <select
        v-model="formData.customer_id"
        required
        style="width: 100%; padding: 8px; margin-top: 5px"
      >
        <option value="">Select Customer</option>
        <option v-for="customer in customers" :key="customer.id" :value="customer.id">
          {{ customer.name }}
        </option>
      </select>
    </div>

    <div v-if="!isEditing" style="margin-bottom: 15px">
      <label>PE Router*:</label>
      <select
        v-model="selectedPERouter"
        @change="handlePERouterChange"
        required
        style="width: 100%; padding: 8px; margin-top: 5px"
      >
        <option value="">Select PE Router</option>
        <option v-for="router in peRouters" :key="router.id" :value="router.id">
          {{ router.hostname }}
        </option>
      </select>
    </div>

    <div v-if="!isEditing && selectedPERouter" style="margin-bottom: 15px">
      <label>PE Interface*:</label>
      <select
        v-model="formData.assigned_interface_id"
        required
        style="width: 100%; padding: 8px; margin-top: 5px"
      >
        <option value="">Select Interface</option>
        <option v-for="iface in peInterfaces" :key="iface.id" :value="iface.id">
          {{ iface.name }}
        </option>
      </select>
    </div>

    <div style="margin-top: 20px">
      <button @click="handleSave" :disabled="saving" style="padding: 10px 20px; margin-right: 10px">
        {{ saving ? 'Saving...' : isEditing ? 'Update' : 'Create' }}
      </button>
      <button @click="handleCancel" style="padding: 10px 20px">Cancel</button>
    </div>

    <div v-if="error" style="color: red; margin-top: 10px">
      {{ error }}
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  show: Boolean,
  isEditing: Boolean,
  customers: Array,
  peRouters: Array,
  peInterfaces: Array,
  saving: Boolean,
  error: String,
  initialData: Object,
})

const emit = defineEmits(['save', 'cancel', 'pe-router-change'])

const formData = ref({
  name: '',
  location: '',
  description: '',
  customer_id: '',
  assigned_interface_id: '',
})

const selectedPERouter = ref('')

// Watch for initial data changes (for editing)
watch(
  () => props.initialData,
  (newData) => {
    if (newData) {
      formData.value = { ...newData }
    }
  },
  { immediate: true, deep: true },
)

// Reset form when show changes to true and not editing
watch(
  () => props.show,
  (newShow) => {
    if (newShow && !props.isEditing) {
      formData.value = {
        name: '',
        location: '',
        description: '',
        customer_id: '',
        assigned_interface_id: '',
      }
      selectedPERouter.value = ''
    }
  },
)

const handleSave = () => {
  emit('save', formData.value)
}

const handleCancel = () => {
  emit('cancel')
}

const handlePERouterChange = () => {
  emit('pe-router-change', selectedPERouter.value)
  formData.value.assigned_interface_id = '' // Reset interface selection
}
</script>
