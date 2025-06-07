<template>
  <div
    class="bg-surface-0 dark:bg-surface-900 py-12 px-8 sm:px-20 rounded-[2.5rem] w-full max-w-[32rem] mx-auto"
  >
    <div v-if="adminExists" class="flex flex-col items-center justify-center text-center py-12">
      <i class="pi pi-user text-4xl text-primary mb-4"></i>
      <div class="text-surface-900 dark:text-surface-0 font-medium text-2xl mb-2">
        Administrator Already Exists
      </div>
      <div class="text-muted-color mb-6">
        An administrator account has already been set up. You can proceed to the next step.
      </div>
    </div>
    <div v-else>
      <div class="text-surface-900 dark:text-surface-0 font-medium text-2xl mb-2">
        Create Administrator Account
      </div>
      <div class="text-muted-color mb-6">Set up your credentials to manage the system</div>

      <div class="flex flex-col gap-6">
        <div>
          <span class="p-float-label p-input-icon-right w-full">
            <i class="pi pi-user mr-3"></i>
            <label for="username" class="text-surface-600 dark:text-surface-200 font-medium"
              >Username</label
            >
            <InputText
              id="username"
              v-model.trim="adminData.username"
              :class="{ 'p-invalid': submitted && !adminData.username }"
              class="w-full mt-2"
            />
          </span>
          <small v-if="submitted && !adminData.username" class="p-error block mt-2">
            Username is required
          </small>
        </div>

        <div>
          <span class="p-float-label p-input-icon-right w-full">
            <i class="pi pi-envelope mr-3"></i>
            <label for="email" class="text-surface-600 dark:text-surface-200 font-medium"
              >Email</label
            >
            <InputText
              id="email"
              type="email"
              v-model.trim="adminData.email"
              :class="{ 'p-invalid': submitted && !adminData.email }"
              class="w-full mt-2"
            />
          </span>
          <small v-if="submitted && !adminData.email" class="p-error block mt-2">
            Email is required
          </small>
        </div>

        <div>
          <span class="p-float-label w-full">
            <i class="pi pi-lock mr-3"></i>
            <label for="password" class="text-surface-600 dark:text-surface-200 font-medium"
              >Password</label
            >
            <Password
              id="password"
              v-model="adminData.password"
              :feedback="true"
              :toggleMask="true"
              class="w-full mt-2"
              :inputClass="{
                'w-full': true,
                'p-invalid': submitted && !adminData.password,
              }"
            >
              <template #header>
                <h6 class="m-0">Pick a password</h6>
              </template>
              <template #footer>
                <Divider />
                <p class="mt-2 mb-2">Suggestions</p>
                <ul class="pl-2 ml-2 mt-0 line-height-3">
                  <li>At least one lowercase</li>
                  <li>At least one uppercase</li>
                  <li>At least one numeric</li>
                  <li>Minimum 8 characters</li>
                </ul>
              </template>
            </Password>
          </span>
          <small v-if="submitted && !adminData.password" class="p-error block mt-2">
            Password is required
          </small>
        </div>
      </div>
    </div>
    <div class="flex items-center justify-between mt-8">
      <Button label="Back" icon="pi pi-arrow-left" text @click="$emit('prev')" />
      <Button label="Next" icon="pi pi-arrow-right" iconPos="right" @click="handleNext" />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import SetupService from '@/service/SetupService'

const toast = useToast()
const emit = defineEmits(['prev', 'next'])

const submitted = ref(false)
const adminData = reactive({
  username: '',
  email: '',
  password: '',
})
const adminExists = ref(false)

onMounted(async () => {
  try {
    const status = await SetupService.checkSetupStatus()
    adminExists.value = status.has_admin
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to check setup status',
      life: 3000,
    })
  }
})

const handleNext = async () => {
  submitted.value = true

  if (!adminData.username || !adminData.email || !adminData.password) {
    return
  }

  try {
    await SetupService.setupAdmin(adminData)
    submitted.value = false
    emit('next')
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: error.response?.data?.message || 'Failed to create admin account',
      life: 3000,
    })
    // If admin already exists, update UI
    if (error.response?.data?.message === 'Admin user already exists') {
      adminExists.value = true
    }
  }
}
</script>

<style scoped>
:deep(.p-password-input),
:deep(.p-inputtext) {
  width: 100%;
}
</style>
