<script setup>
import FloatingConfigurator from '@/components/FloatingConfigurator.vue'
import { ref } from 'vue'

const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const checked = ref(false)
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
              :feedback="false"
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
            ></Password>

            <div class="flex items-center justify-between mt-2 mb-8 gap-8">
              <div class="flex items-center">
                <Checkbox v-model="checked" id="terms" binary class="mr-2"></Checkbox>
                <label for="terms">I agree to the terms and conditions</label>
              </div>
            </div>
            <Button label="Sign Up" class="w-full" as="router-link" to="/"></Button>
          </div>
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
