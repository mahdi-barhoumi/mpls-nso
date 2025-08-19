<script setup>
import FloatingConfigurator from '@/components/FloatingConfigurator.vue'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import AuthService from '@/service/AuthService'
import { useToast } from 'primevue/usetoast'

const router = useRouter()
const toast = useToast()
const username = ref('')
const password = ref('')
const checked = ref(false)
const loading = ref(false)
const errors = ref({
  username: '',
  password: '',
})

const clearErrors = () => {
  errors.value = {
    username: '',
    password: '',
  }
}

const handleLogin = async () => {
  clearErrors()
  loading.value = true
  try {
    const auth = new AuthService()
    await auth.login(username.value, password.value)
    router.push('/')
  } catch (error) {
    // Set field-specific error if available
    if (error.field) {
      errors.value[error.field] = error.message
    }

    toast.add({
      severity: 'error',
      summary: 'Login Failed',
      detail: error.message || 'Invalid credentials',
      life: 5000,
    })
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <FloatingConfigurator />
  <div
    class="bg-surface-50 dark:bg-surface-950 flex items-center justify-center min-h-screen min-w-[100vw] overflow-hidden"
  >
    <div class="flex flex-col items-center justify-center">
      <div
        style="
          border-radius: 56px;
          padding: 0.3rem;
          background: linear-gradient(180deg, var(--primary-color) 10%, rgba(33, 150, 243, 0) 30%);
        "
      >
        <div
          class="w-full bg-surface-0 dark:bg-surface-900 py-20 px-8 sm:px-20"
          style="border-radius: 53px"
        >
          <div class="text-center mb-8">
            <div class="text-surface-900 dark:text-surface-0 text-3xl font-medium mb-4">
              Welcome to MPLS-NSO
            </div>
            <span class="text-muted-color font-medium">Sign in to continue</span>
          </div>

          <form @submit.prevent="handleLogin">
            <div>
              <label
                for="username"
                class="block text-surface-900 dark:text-surface-0 text-xl font-medium mb-2"
                >Username</label
              >
              <InputText
                id="username"
                type="text"
                placeholder="Username"
                class="w-full md:w-[30rem] mb-2"
                :class="{ 'p-invalid': errors.username }"
                v-model="username"
                required
                @focus="errors.username = ''"
              />
              <small v-if="errors.username" class="p-error block mb-4">{{ errors.username }}</small>

              <label
                for="password"
                class="block text-surface-900 dark:text-surface-0 font-medium text-xl mb-2 mt-4"
                >Password</label
              >
              <Password
                id="password"
                v-model="password"
                placeholder="Password"
                :toggleMask="true"
                :class="{ 'p-invalid': errors.password }"
                class="mb-2"
                :feedback="false"
                required
                @focus="errors.password = ''"
              ></Password>
              <small v-if="errors.password" class="p-error block mb-4">{{ errors.password }}</small>

              <div class="flex items-center justify-between mt-4 mb-8 gap-8">
                <div class="flex items-center">
                  <Checkbox v-model="checked" id="rememberme1" binary class="mr-2"></Checkbox>
                  <label for="rememberme1">Remember me</label>
                </div>
              </div>
              <Button
                type="submit"
                :label="loading ? 'Signing in...' : 'Sign In'"
                class="w-full"
                :loading="loading"
                :disabled="loading"
              ></Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pi-eye {
  transform: scale(1.6);
  margin-right: 1rem;
}

.pi-eye-slash {
  transform: scale(1.6);
  margin-right: 1rem;
}

.p-password {
  width: 100%;
}
.p-password :deep(input) {
  width: 100%;
}
</style>
