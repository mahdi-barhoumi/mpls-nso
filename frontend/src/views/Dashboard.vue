<script setup>
import NetworkMap from '@/components/NetworkMap.vue'
</script>

<template>
  <div class="grid grid-cols-12 gap-8">
    <!-- The next two sections are split into two equal parts for larger screens (6 columns each) -->
    <div class="col-span-12 xl:col-span-6">
      <NetworkMap />
    </div>
    <div class="col-span-12 xl:col-span-6">
      <div />
      <div />
    </div>
  </div>
</template>
