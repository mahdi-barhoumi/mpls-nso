<script setup>
import MapWidget from '@/components/dashboard/MapWidget.vue'
import CustomerCrud from './pages/CustomerCrud.vue'
</script>

<template>
  <div class="grid grid-cols-12 gap-8">
    <!-- The next two sections are split into two equal parts for larger screens (6 columns each) -->
    <div class="col-span-12 xl:col-span-8">
      <MapWidget />
    </div>
    <div class="col-span-12 xl:col-span-4"></div>
  </div>
</template>
