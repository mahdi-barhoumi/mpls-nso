<script setup>
import FloatingConfigurator from '@/components/FloatingConfigurator.vue'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import AuthService from '@/service/AuthService'
import { useToast } from 'primevue/usetoast'

const router = useRouter()
const toast = useToast()
<<<<<<< HEAD
const username = ref('')
=======
const email = ref('')
>>>>>>> origin/28-fix-site-deletion-and-interface-connection
const password = ref('')
const checked = ref(false)

const handleLogin = async () => {
  try {
    const auth = new AuthService()
<<<<<<< HEAD
    await auth.login(username.value, password.value)
=======
    await auth.login(email.value, password.value)
>>>>>>> origin/28-fix-site-deletion-and-interface-connection
    router.push('/')
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: error.response?.data?.error || 'Invalid credentials',
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
              Welcome to MPLS-NSO
            </div>
            <span class="text-muted-color font-medium">Sign in to continue</span>
          </div>

          <form @submit.prevent="handleLogin">
            <div>
              <label
<<<<<<< HEAD
                for="username"
=======
                for="email1"
>>>>>>> origin/28-fix-site-deletion-and-interface-connection
                class="block text-surface-900 dark:text-surface-0 text-xl font-medium mb-2"
                >Username</label
              >
              <InputText
<<<<<<< HEAD
                id="username"
                type="text"
                placeholder="Username"
                class="w-full md:w-[30rem] mb-8"
                v-model="username"
=======
                id="email1"
                type="text"
                placeholder="Username"
                class="w-full md:w-[30rem] mb-8"
                v-model="email"
>>>>>>> origin/28-fix-site-deletion-and-interface-connection
                required
              />

              <label
<<<<<<< HEAD
                for="password"
=======
                for="password1"
>>>>>>> origin/28-fix-site-deletion-and-interface-connection
                class="block text-surface-900 dark:text-surface-0 font-medium text-xl mb-2"
                >Password</label
              >
              <Password
<<<<<<< HEAD
                id="password"
=======
                id="password1"
>>>>>>> origin/28-fix-site-deletion-and-interface-connection
                v-model="password"
                placeholder="Password"
                :toggleMask="true"
                class="mb-4"
                fluid
                :feedback="false"
                required
              ></Password>

              <div class="flex items-center justify-between mt-2 mb-8 gap-8">
                <div class="flex items-center">
                  <Checkbox v-model="checked" id="rememberme1" binary class="mr-2"></Checkbox>
                  <label for="rememberme1">Remember me</label>
                </div>
              </div>
              <Button type="submit" label="Sign In" class="w-full"></Button>
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
