<script setup>
import FloatingConfigurator from '@/components/FloatingConfigurator.vue'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import AuthService from '@/service/AuthService'
import { useToast } from 'primevue/usetoast'

const router = useRouter()
const toast = useToast()
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const checked = ref(false)

const handleRegister = async () => {
  if (!checked.value) {
    toast.add({
      severity: 'warn',
      summary: 'Warning',
      detail: 'Please accept terms and conditions',
      life: 3000,
    })
    return
  }
  if (password.value !== confirmPassword.value) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Passwords do not match', life: 3000 })
    return
  }
  try {
    const auth = new AuthService()
    await auth.register(email.value, password.value)
    toast.add({
      severity: 'success',
      summary: 'Success',
      detail: 'Registration successful',
      life: 3000,
    })
    router.push('/auth/login')
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: error.response?.data?.error || 'Registration failed',
      life: 3000,
    })
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
              Create an Account
            </div>
            <span class="text-muted-color font-medium">Sign up to get started</span>
          </div>

          <form @submit.prevent="handleRegister">
            <div>
              <label
                for="email1"
                class="block text-surface-900 dark:text-surface-0 text-xl font-medium mb-2"
                >Email</label
              >
              <InputText
                id="email1"
                type="text"
                placeholder="Email address"
                class="w-full md:w-[30rem] mb-8"
                v-model="email"
                required
              />

              <label
                for="password1"
                class="block text-surface-900 dark:text-surface-0 font-medium text-xl mb-2"
                >Password</label
              >
              <Password
                id="password1"
                v-model="password"
                placeholder="Password"
                :toggleMask="true"
                class="mb-4"
                fluid
                :feedback="true"
                required
              ></Password>

              <label
                for="confirmPassword1"
                class="block text-surface-900 dark:text-surface-0 font-medium text-xl mb-2"
                >Confirm Password</label
              >
              <Password
                id="confirmPassword1"
                v-model="confirmPassword"
                placeholder="Confirm Password"
                :toggleMask="true"
                class="mb-4"
                fluid
                :feedback="false"
                required
              ></Password>

              <div class="flex items-center justify-between mt-2 mb-8 gap-8">
                <div class="flex items-center">
                  <Checkbox v-model="checked" id="terms" binary class="mr-2"></Checkbox>
                  <label for="terms">I agree to the terms and conditions</label>
                </div>
              </div>
              <Button type="submit" label="Sign Up" class="w-full"></Button>
              <div class="text-center mt-4">
                <router-link to="/auth/login" class="text-primary"
                  >Already have an account? Sign in</router-link
                >
              </div>
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
</style>
