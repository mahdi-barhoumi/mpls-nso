<template>
  <div
    class="bg-surface-0 dark:bg-surface-900 py-9 px-8 sm:px-20 rounded-[2.5rem] w-full max-w-[32rem] mx-auto"
  >
    <div class="text-center mb-8">
      <div
        class="inline-flex items-center justify-center bg-primary-50 dark:bg-primary-400/10 rounded-full mb-4"
        style="width: 4rem; height: 4rem"
      >
        <i class="pi pi-wrench text-primary text-3xl"></i>
      </div>
      <div class="text-surface-900 dark:text-surface-0 text-3xl font-medium mb-4">
        Welcome to MPLS-NSO
      </div>
      <span class="text-muted-color font-medium">Let's set up your network management system</span>
    </div>

    <div class="flex flex-col gap-4 mb-8">
      <div class="bg-surface-50 dark:bg-surface-900 p-4 rounded-xl flex items-center gap-4">
        <span
          class="inline-flex items-center justify-center bg-primary-50 dark:bg-primary-400/10 rounded-full w-8 h-8"
        >
          <i class="pi pi-user text-primary text-xl"></i>
        </span>
        <div class="flex flex-col">
          <span class="text-surface-900 dark:text-surface-0 font-medium">Administrator</span>
          <span class="text-muted-color text-sm">Manage users, roles, and system settings</span>
        </div>
      </div>
      <div class="bg-surface-50 dark:bg-surface-900 p-4 rounded-xl flex items-center gap-4">
        <span
          class="inline-flex items-center justify-center bg-primary-50 dark:bg-primary-400/10 rounded-full w-8 h-8"
        >
          <i class="pi pi-server text-primary text-xl"></i>
        </span>
        <div class="flex flex-col">
          <span class="text-surface-900 dark:text-surface-0 font-medium">Network</span>
          <span class="text-muted-color text-sm">Configure and monitor network devices</span>
        </div>
      </div>
      <div class="bg-surface-50 dark:bg-surface-900 p-4 rounded-xl flex items-center gap-4">
        <span
          class="inline-flex items-center justify-center bg-primary-50 dark:bg-primary-400/10 rounded-full w-8 h-8"
        >
          <i class="pi pi-shield text-primary text-xl"></i>
        </span>
        <div class="flex flex-col">
          <span class="text-surface-900 dark:text-surface-0 font-medium">Security</span>
          <span class="text-muted-color text-sm"
            >Protect your network with advanced security features</span
          >
        </div>
      </div>
    </div>

    <div class="flex justify-center mt-8">
      <Button
        label="Get Started"
        icon="pi pi-arrow-right"
        iconPos="right"
        @click="$emit('next')"
        class="w-full"
      />
    </div>
  </div>
</template>

<script setup>
defineEmits(['next'])
</script>
