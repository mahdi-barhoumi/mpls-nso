<template>
  <div class="grid">
    <div class="col-12 md:col-10 md:col-offset-1 lg:col-8 lg:col-offset-2">
      <div class="card">
        <!-- Simple Profile Header -->
        <div class="flex align-items-center mb-4 pb-2 border-bottom-1 surface-border">
          <i class="pi pi-user-edit text-2xl text-primary mr-3"></i>
          <h5 class="text-xl m-0">Profile Settings</h5>
        </div>

        <!-- Basic Form -->
        <div class="p-fluid formgrid grid">
          <div class="field col-12 md:col-6 mb-4">
            <label for="username" class="block font-medium mb-2">Username</label>
            <span class="p-input-icon-left w-full">
              <i class="pi pi-user"></i>
              <InputText
                id="username"
                v-model="formData.username"
                placeholder="Username"
                class="w-full"
              />
            </span>
          </div>

          <div class="field col-12 md:col-6 mb-4">
            <label for="email" class="block font-medium mb-2">Email</label>
            <span class="p-input-icon-left w-full">
              <i class="pi pi-envelope"></i>
              <InputText
                id="email"
                type="email"
                v-model="formData.email"
                placeholder="Email address"
                class="w-full"
              />
            </span>
          </div>

          <div class="field col-12 md:col-6 mb-4">
            <label for="new-password" class="block font-medium mb-2">New Password</label>
            <Password
              id="new-password"
              v-model="formData.new_password"
              :toggleMask="true"
              placeholder="Enter new password"
              class="w-full"
              :inputStyle="{ width: '100%' }"
              :feedback="true"
            />
          </div>

          <div class="field col-12 md:col-6 mb-4">
            <label for="confirm-password" class="block font-medium mb-2">Confirm Password</label>
            <Password
              id="confirm-password"
              v-model="formData.confirm_password"
              :toggleMask="true"
              placeholder="Confirm new password"
              class="w-full"
              :inputStyle="{ width: '100%' }"
              :feedback="false"
            />
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="flex flex-wrap justify-content-end gap-2 pt-3 border-top-1 surface-border">
          <Button label="Cancel" icon="pi pi-times" class="p-button-outlined" :disabled="loading" />
          <Button
            label="Save Changes"
            icon="pi pi-check"
            @click="updateProfile"
            :loading="loading"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import UserService from '@/service/UserService'

// Components
import Password from 'primevue/password'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'

const toast = useToast()
const loading = ref(false)

const formData = reactive({
  username: '',
  email: '',
  new_password: '',
  confirm_password: '',
})

// Load user profile
const loadProfile = async () => {
  try {
    loading.value = true
    const data = await UserService.getUserProfile()
    formData.username = data.username
    formData.email = data.email
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to load profile',
      life: 3000,
    })
  } finally {
    loading.value = false
  }
}

// Validate form before submission
const validateForm = () => {
  if (formData.new_password && formData.new_password !== formData.confirm_password) {
    toast.add({
      severity: 'warn',
      summary: 'Validation Error',
      detail: 'Passwords do not match',
      life: 3000,
    })
    return false
  }
  return true
}

// Update profile
const updateProfile = async () => {
  if (!validateForm()) return

  try {
    loading.value = true
    const updateData = {
      username: formData.username,
      email: formData.email,
    }

    if (formData.new_password) {
      updateData.new_password = formData.new_password
    }

    await UserService.updateProfile(updateData)

    toast.add({
      severity: 'success',
      summary: 'Success',
      detail: 'Profile updated successfully',
      life: 3000,
    })

    // Clear password fields after successful update
    formData.new_password = ''
    formData.confirm_password = ''
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: error.response?.data?.error || 'Failed to update profile',
      life: 3000,
    })
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadProfile()
})
</script>
