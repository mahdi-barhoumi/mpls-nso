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
    label: 'Tools',
    items: [
      {
        label: 'Monitoring',
        icon: 'pi pi-fw pi-chart-bar',
        to: '/monitoring',
      },
      {
        label: 'Administration',
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
            icon: 'pi pi-fw pi-sitemap',
            to: '/vpn',
          },
          {
            label: 'Device Inventory',
            icon: 'pi pi-fw pi-server',
            to: '/device-inventory',
          },
        ],
      },
      {
        label: 'Settings',
        icon: 'pi pi-fw pi-cog',
        items: [
          {
            label: 'User Settings',
            icon: 'pi pi-fw pi-user-edit',
            to: '/settings/user',
          },
          {
            label: 'Server Settings',
            icon: 'pi pi-fw pi-sliders-h',
            to: '/settings/server',
          },
        ],
      },
      {
        label: 'Troubleshooting',
        icon: 'pi pi-fw pi-wrench',
        items: [
          {
            label: 'Logs',
            icon: 'pi pi-fw pi-file',
            to: '/troubleshooting/logs',
          },
          {
            label: 'Guide',
            icon: 'pi pi-fw pi-book',
            to: '/troubleshooting/guide',
          },
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
