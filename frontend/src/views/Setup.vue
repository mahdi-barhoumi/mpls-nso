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
          class="w-full min-w-[32rem] bg-surface-0 dark:bg-surface-900 py-20 px-8 sm:px-20"
          style="border-radius: 53px"
        >
          <Stepper v-model:value="activeStep" class="w-full">
            <StepList>
              <Step v-slot="{ activateCallback, value, a11yAttrs }" asChild :value="1">
                <div class="flex flex-row flex-auto gap-2" v-bind="a11yAttrs.root">
                  <button
                    class="bg-transparent border-0 inline-flex flex-col gap-2 items-center"
                    @click="activateCallback"
                    v-bind="a11yAttrs.header"
                  >
                    <span
                      :class="[
                        'rounded-full border-2 w-12 h-12 inline-flex items-center justify-center',
                        {
                          'bg-primary text-primary-contrast border-primary': value <= activeStep,
                          'border-surface-200 dark:border-surface-700': value > activeStep,
                        },
                      ]"
                    >
                      <i class="pi pi-home" />
                    </span>
                    <span class="text-sm text-center">Welcome</span>
                  </button>
                  <Divider />
                </div>
              </Step>
              <Step v-slot="{ activateCallback, value, a11yAttrs }" asChild :value="2">
                <div class="flex flex-row flex-auto gap-2 pl-2" v-bind="a11yAttrs.root">
                  <button
                    class="bg-transparent border-0 inline-flex flex-col gap-2 items-center"
                    @click="activateCallback"
                    v-bind="a11yAttrs.header"
                  >
                    <span
                      :class="[
                        'rounded-full border-2 w-12 h-12 inline-flex items-center justify-center',
                        {
                          'bg-primary text-primary-contrast border-primary': value <= activeStep,
                          'border-surface-200 dark:border-surface-700': value > activeStep,
                        },
                      ]"
                    >
                      <i class="pi pi-user" />
                    </span>
                    <span class="text-sm text-center">Account</span>
                  </button>
                  <Divider />
                </div>
              </Step>
              <Step v-slot="{ activateCallback, value, a11yAttrs }" asChild :value="3">
                <div class="flex flex-row flex-auto gap-2 pl-2" v-bind="a11yAttrs.root">
                  <button
                    class="bg-transparent border-0 inline-flex flex-col gap-2 items-center"
                    @click="activateCallback"
                    v-bind="a11yAttrs.header"
                  >
                    <span
                      :class="[
                        'rounded-full border-2 w-12 h-12 inline-flex items-center justify-center',
                        {
                          'bg-primary text-primary-contrast border-primary': value <= activeStep,
                          'border-surface-200 dark:border-surface-700': value > activeStep,
                        },
                      ]"
                    >
                      <i class="pi pi-cog" />
                    </span>
                    <span class="text-sm text-center">Settings</span>
                  </button>
                  <Divider />
                </div>
              </Step>
              <Step v-slot="{ activateCallback, value, a11yAttrs }" asChild :value="4">
                <div class="flex flex-row pl-2" v-bind="a11yAttrs.root">
                  <button
                    class="bg-transparent border-0 inline-flex flex-col gap-2 items-center"
                    @click="activateCallback"
                    v-bind="a11yAttrs.header"
                  >
                    <span
                      :class="[
                        'rounded-full border-2 w-12 h-12 inline-flex items-center justify-center',
                        {
                          'bg-primary text-primary-contrast border-primary': value <= activeStep,
                          'border-surface-200 dark:border-surface-700': value > activeStep,
                        },
                      ]"
                    >
                      <i class="pi pi-check" />
                    </span>
                    <span class="text-sm text-center">Complete</span>
                  </button>
                </div>
              </Step>
            </StepList>

            <StepPanels>
              <StepPanel v-slot="{ activateCallback }" :value="1">
                <SetupWelcome @next="() => activateCallback(2)" />
              </StepPanel>
              <StepPanel v-slot="{ activateCallback }" :value="2">
                <SetupAdmin @prev="() => activateCallback(1)" @next="() => activateCallback(3)" />
              </StepPanel>
              <StepPanel v-slot="{ activateCallback }" :value="3">
                <SetupNetwork @prev="() => activateCallback(2)" @next="() => activateCallback(4)" />
              </StepPanel>
              <StepPanel :value="4">
                <SetupComplete @complete="goToLogin" />
              </StepPanel>
            </StepPanels>
          </Stepper>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import FloatingConfigurator from '@/components/FloatingConfigurator.vue'
import SetupWelcome from '@/components/setup/SetupWelcome.vue'
import SetupAdmin from '@/components/setup/SetupAdmin.vue'
import SetupNetwork from '@/components/setup/SetupNetwork.vue'
import SetupComplete from '@/components/setup/SetupComplete.vue'
import Stepper from 'primevue/stepper'
import StepList from 'primevue/steplist'
import StepPanels from 'primevue/steppanels'
import Step from 'primevue/step'
import StepPanel from 'primevue/steppanel'
import Divider from 'primevue/divider'

const router = useRouter()
const activeStep = ref(1)

const goToLogin = () => {
  router.push('/auth/login')
}
</script>

<style scoped>
.surface-card {
  background: var(--surface-card);
}
</style>
