<template>
  <Dialog
    :visible="show"
    @update:visible="$emit('update:show', $event)"
    modal
    :header="isEditing ? 'Edit Site' : 'Create Site'"
    :style="{ width: '35rem' }"
  >
    <span class="text-surface-500 dark:text-surface-400 block mb-6">
      {{ isEditing ? 'Update site information.' : 'Create a new site.' }}
    </span>

    <div class="flex flex-col gap-4">
      <div class="flex items-center gap-4 mb-2">
        <label for="name" class="font-semibold w-32">Name*</label>
        <div class="flex-auto">
          <InputText
            id="name"
            v-model.trim="formData.name"
            required="true"
            autofocus
            :class="{ 'p-invalid': submitted && !formData.name }"
            class="w-full"
            autocomplete="off"
          />
          <small v-if="submitted && !formData.name" class="p-error">Name is required.</small>
        </div>
      </div>

      <div class="flex items-center gap-4 mb-2">
        <label for="location" class="font-semibold w-32">Location</label>
        <InputText id="location" v-model="formData.location" class="flex-auto" autocomplete="off" />
      </div>

      <div class="flex items-center gap-4 mb-2">
        <label for="description" class="font-semibold w-32">Description</label>
        <Textarea
          id="description"
          v-model="formData.description"
          rows="3"
          autoResize
          class="flex-auto"
        />
      </div>

      <div v-if="!isEditing" class="flex items-center gap-4 mb-2">
        <label for="customer" class="font-semibold w-32">Customer*</label>
        <div class="flex-auto">
          <Dropdown
            id="customer"
            v-model="formData.customer_id"
            :options="customers"
            optionLabel="name"
            optionValue="id"
            placeholder="Select Customer"
            :class="{ 'p-invalid': submitted && !formData.customer_id }"
            class="w-full"
          />
          <small v-if="submitted && !formData.customer_id" class="p-error">
            Customer is required.
          </small>
        </div>
      </div>

      <div v-if="!isEditing" class="flex items-center gap-4 mb-2">
        <label for="peRouter" class="font-semibold w-32">PE Router*</label>
        <div class="flex-auto">
          <Dropdown
            id="peRouter"
            v-model="selectedPERouter"
            :options="peRouters"
            optionLabel="hostname"
            optionValue="id"
            placeholder="Select PE Router"
            :class="{ 'p-invalid': submitted && !selectedPERouter }"
            class="w-full"
            @change="handlePERouterChange"
          />
          <small v-if="submitted && !selectedPERouter" class="p-error">
            PE Router is required.
          </small>
        </div>
      </div>

      <div v-if="!isEditing && selectedPERouter" class="flex items-center gap-4 mb-2">
        <label for="interface" class="font-semibold w-32">PE Interface*</label>
        <div class="flex-auto">
          <Dropdown
            id="interface"
            v-model="formData.assigned_interface_id"
            :options="peInterfaces"
            optionLabel="name"
            optionValue="id"
            placeholder="Select Interface"
            :class="{ 'p-invalid': submitted && !formData.assigned_interface_id }"
            class="w-full"
          />
          <small v-if="submitted && !formData.assigned_interface_id" class="p-error">
            Interface is required.
          </small>
        </div>
      </div>

      <small v-if="error" class="p-error block mt-2">{{ error }}</small>
    </div>

    <div class="flex justify-end gap-2 mt-8">
      <Button type="button" label="Cancel" severity="secondary" @click="handleCancel" />
      <Button
        type="button"
        :label="saving ? 'Saving...' : isEditing ? 'Update' : 'Create'"
        :loading="saving"
        @click="handleSave"
      />
    </div>
  </Dialog>
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

const emit = defineEmits(['save', 'cancel', 'pe-router-change', 'update:show'])

const formData = ref({
  name: '',
  location: '',
  description: '',
  customer_id: '',
  assigned_interface_id: '',
})

const selectedPERouter = ref('')
const submitted = ref(false)

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
      submitted.value = false
    }
  },
)

const handleSave = () => {
  submitted.value = true
  if (
    !formData.value.name ||
    (!props.isEditing &&
      (!formData.value.customer_id ||
        !selectedPERouter.value ||
        !formData.value.assigned_interface_id))
  ) {
    return
  }
  emit('save', formData.value)
}

const handleCancel = () => {
  submitted.value = false
  emit('update:show', false)
  emit('cancel')
}

const handlePERouterChange = () => {
  emit('pe-router-change', selectedPERouter.value)
  formData.value.assigned_interface_id = '' // Reset interface selection
}
</script>
