<template>
  <div
    class="bg-surface-0 dark:bg-surface-900 py-3 px-2 sm:px-20 rounded-[2.5rem] w-full max-w-[32rem] mx-auto"
  >
    <div class="flex flex-col items-center text-center">
      <div class="mb-8">
        <span
          class="inline-flex items-center justify-center bg-green-50 dark:bg-green-400/10 rounded-full mb-4"
          style="width: 4rem; height: 4rem"
        >
          <i class="pi pi-check-circle text-green-500 text-4xl"></i>
        </span>
        <div class="text-surface-900 dark:text-surface-0 text-3xl font-medium mb-3">
          Setup Complete!
        </div>
        <p class="text-muted-color mb-0">
          Your network management system has been configured successfully. The following services
          have been initialized and are ready to use:
        </p>
      </div>

      <div class="flex flex-col gap-4 w-full mb-8">
        <div class="bg-surface-50 dark:bg-surface-900 p-4 rounded-xl flex items-center gap-4">
          <span
            class="inline-flex items-center justify-center bg-primary-50 dark:bg-primary-400/10 rounded-full w-8 h-8"
          >
            <i class="pi pi-search text-primary text-xl"></i>
          </span>
          <span class="text-surface-900 dark:text-surface-0 font-medium">Discovery Service</span>
          <span class="text-muted-color ml-auto">Automatic network topology discovery enabled</span>
        </div>
        <div class="bg-surface-50 dark:bg-surface-900 p-4 rounded-xl flex items-center gap-4">
          <span
            class="inline-flex items-center justify-center bg-primary-50 dark:bg-primary-400/10 rounded-full w-8 h-8"
          >
            <i class="pi pi-server text-primary text-xl"></i>
          </span>
          <span class="text-surface-900 dark:text-surface-0 font-medium">DHCP Service</span>
          <span class="text-muted-color ml-auto">IP address management service is running</span>
        </div>
        <div class="bg-surface-50 dark:bg-surface-900 p-4 rounded-xl flex items-center gap-4">
          <span
            class="inline-flex items-center justify-center bg-primary-50 dark:bg-primary-400/10 rounded-full w-8 h-8"
          >
            <i class="pi pi-upload text-primary text-xl"></i>
          </span>
          <span class="text-surface-900 dark:text-surface-0 font-medium">TFTP Service</span>
          <span class="text-muted-color ml-auto">Configuration deployment service is ready</span>
        </div>
      </div>

      <Button
        label="Login to Dashboard"
        icon="pi pi-sign-in"
        size="large"
        @click="$emit('complete')"
        class="w-full"
      />
    </div>
  </div>
</template>

<script setup>
defineEmits(['complete'])
</script>
