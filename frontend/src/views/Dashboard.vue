<script setup>
import MapWidget from '@/components/dashboard/MapWidget.vue'
import RouterWidget from '@/components/dashboard/RouterWidget.vue'
import { ref } from 'vue'

const selectedRouter = ref(null)

const handleRouterSelect = (router) => {
  selectedRouter.value = router
}
</script>

<template>
  <div class="grid grid-cols-12 gap-10">
    <div class="col-span-12 xl:col-span-8">
      <MapWidget @node-selected="handleRouterSelect" />
    </div>
    <div class="col-span-12 xl:col-span-4">
      <RouterWidget :selected-router="selectedRouter" />
    </div>
  </div>
</template>
