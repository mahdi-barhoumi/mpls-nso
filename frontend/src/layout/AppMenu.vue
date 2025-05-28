<script setup>
import { ref } from 'vue'
import AppMenuItem from './AppMenuItem.vue'

const model = ref([
  {
    label: 'Overview',
    icon: 'pi pi-fw pi-th-large',
    items: [
      {
        label: 'Dashboard',
        icon: 'pi pi-fw pi-home',
        to: '/',
      },
    ],
  },

  {
    label: 'Administration',
    items: [
      {
        label: 'Device Inventory',
        icon: 'pi pi-fw pi-server',
        to: '/inventory',
      },
      {
        label: 'Monitoring',
        icon: 'pi pi-fw pi-chart-bar',
        to: '/monitoring',
      },
      {
        label: 'Services',
        icon: 'pi pi-fw pi-briefcase',
        items: [
          {
            label: 'Customers',
            icon: 'pi pi-fw pi-users',
            to: '/customers',
          },
          {
            label: 'Sites',
            icon: 'pi pi-fw pi-building',
            to: '/sites',
          },
          {
            label: 'VPN',
            icon: 'pi pi-fw pi-shield',
            to: '/vpns',
          }
        ],
      },
      {
        label: 'Settings',
        icon: 'pi pi-fw pi-cog',
        items: [
          {
            label: 'System Settings',
            icon: 'pi pi-fw pi-sliders-h',
            to: '/settings/server',
          },
          {
            label: 'User Settings',
            icon: 'pi pi-fw pi-user-edit',
            to: '/settings/user',
          }
        ],
      },
      {
        label: 'Troubleshooting',
        icon: 'pi pi-fw pi-wrench',
        items: [
          {
            label: 'Documentation',
            icon: 'pi pi-fw pi-book',
            to: '/troubleshooting/guide',
          },
          {
            label: 'Logs',
            icon: 'pi pi-fw pi-file',
            to: '/troubleshooting/logs',
          }
        ],
      },
    ],
  },
])
</script>

<template>
  <ul class="layout-menu">
    <template v-for="(item, i) in model" :key="item">
      <app-menu-item v-if="!item.separator" :item="item" :index="i"></app-menu-item>
      <li v-if="item.separator" class="menu-separator"></li>
    </template>
  </ul>
</template>

<style lang="scss" scoped></style>
