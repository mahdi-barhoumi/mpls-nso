<script setup>
import FloatingConfigurator from '@/components/FloatingConfigurator.vue'
</script>

<template>
  <FloatingConfigurator />
  <div class="flex items-center justify-center min-h-screen overflow-hidden">
    <div class="flex flex-col items-center justify-center">
      <img src="/favicon.ico" alt="Logo" class="mb-8 w-32 h-32 shrink-0" />
      <div
        style="
          border-radius: 56px;
          padding: 0.3rem;
          background: linear-gradient(
            180deg,
            color-mix(in srgb, var(--primary-color), transparent 60%) 10%,
            var(--surface-ground) 30%
          );
        "
      >
        <div
          class="w-full bg-surface-0 dark:bg-surface-900 py-20 px-8 sm:px-20 flex flex-col items-center"
          style="border-radius: 53px"
        >
          <span class="text-primary font-bold text-3xl">404</span>
          <h1 class="text-surface-900 dark:text-surface-0 font-bold text-3xl lg:text-5xl mb-2">
            Not Found
          </h1>
          <div class="text-surface-600 dark:text-surface-200 mb-8">
            Requested resource is not available.
          </div>
          <router-link
            to="/"
            class="w-full flex items-center py-8 border-surface-300 dark:border-surface-500 border-b"
          >
          </router-link>
          <Button as="router-link" label="Go to Dashboard" to="/" />
        </div>
      </div>
    </div>
  </div>
</template>
