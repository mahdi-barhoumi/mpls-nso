<script setup>
import { useLayout } from '@/layout/composables/layout'
import AppConfigurator from './AppConfigurator.vue'
import AuthService from '@/service/AuthService'
import notificationService from '@/service/NotificationService'
import { useRouter } from 'vue-router'
import { ref, onMounted, onUnmounted, computed } from 'vue'

const { toggleMenu, toggleDarkMode, isDarkTheme } = useLayout()
const router = useRouter()
const authService = new AuthService()
const currentUser = ref(null)
const notifications = notificationService.getNotifications()

// Computed property to safely check notifications length
const notificationCount = computed(() => notifications.value?.length || 0)

onMounted(() => {
  currentUser.value = authService.getCurrentUser()
  notificationService.startPolling()
})

onUnmounted(() => {
  notificationService.stopPolling()
})

async function handleLogout() {
  await authService.logout()
  router.push('/auth/login')
}

function goToSettings() {
  router.push('settings/user')
}

function handleNotificationClick(notification) {
  if (notification.type === 'log') {
    router.push('/logs')
  } else if (notification.type === 'monitoring') {
    router.push(`/monitoring/routers/${notification.resourceId}`)
  }
  notificationService.clearNotification(notification.id)
}

function clearAllNotifications() {
  notificationService.clearAllNotifications()
}

const getNotificationIcon = (notification) => {
  if (notification.type === 'log') return 'pi-exclamation-circle'
  return 'pi-server'
}
</script>

<template>
  <div class="layout-topbar">
    <div class="layout-topbar-logo-container">
      <button class="layout-menu-button layout-topbar-action" @click="toggleMenu">
        <i class="pi pi-bars"></i>
      </button>
      <router-link to="/" class="layout-topbar-logo">
        <span>MPLS-NSO</span>
      </router-link>
    </div>

    <div class="layout-topbar-actions">
      <div class="layout-config-menu">
        <button type="button" class="layout-topbar-action" @click="toggleDarkMode">
          <i :class="['pi', { 'pi-moon': isDarkTheme, 'pi-sun': !isDarkTheme }]"></i>
        </button>
      </div>

      <!-- Notifications dropdown -->
      <div class="relative">
        <button
          class="layout-topbar-action"
          v-styleclass="{
            selector: '@next',
            enterFromClass: 'hidden',
            enterActiveClass: 'animate-scalein',
            leaveToClass: 'hidden',
            leaveActiveClass: 'animate-fadeout',
            hideOnOutsideClick: true,
          }"
        >
          <i class="pi pi-bell"></i>
          <span
            v-if="notificationCount > 0"
            class="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center"
          >
            {{ notificationCount }}
          </span>
        </button>

        <div
          class="hidden absolute right-0 top-[3rem] w-[400px] max-h-[600px] overflow-y-auto p-4 bg-surface-0 dark:bg-surface-900 border border-surface-200 dark:border-surface-700 rounded-md shadow-md"
        >
          <div
            class="flex justify-between items-center mb-4 border-b pb-2 border-surface-200 dark:border-surface-700"
          >
            <h3 class="text-lg font-semibold text-surface-900 dark:text-surface-0">
              Notifications
            </h3>
            <button
              v-if="notificationCount > 0"
              @click="clearAllNotifications"
              class="text-sm text-primary-500 hover:text-primary-600 dark:hover:text-primary-400"
            >
              Clear all
            </button>
          </div>

          <div v-if="notificationCount > 0" class="flex flex-col gap-2">
            <button
              v-for="notification in notifications.value"
              :key="notification.id"
              @click="handleNotificationClick(notification)"
              class="flex items-start gap-3 p-3 rounded-md hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors text-left"
            >
              <i :class="['pi', getNotificationIcon(notification), 'mt-0.5 text-red-500']"></i>
              <div class="flex-1">
                <p class="text-surface-900 dark:text-surface-0 font-medium">
                  {{ notification.message }}
                </p>
                <p class="text-sm text-surface-500">
                  {{ new Date(notification.timestamp).toLocaleString() }}
                </p>
              </div>
            </button>
          </div>

          <div v-else class="text-center py-8 text-surface-500 dark:text-surface-400">
            No new notifications
          </div>
        </div>
      </div>

      <!-- User profile dropdown -->
      <div class="relative">
        <button
          class="layout-topbar-action"
          v-styleclass="{
            selector: '@next',
            enterFromClass: 'hidden',
            enterActiveClass: 'animate-scalein',
            leaveToClass: 'hidden',
            leaveActiveClass: 'animate-fadeout',
            hideOnOutsideClick: true,
          }"
        >
          <i class="pi pi-user"></i>
        </button>

        <div
          class="hidden absolute right-0 top-[3rem] min-w-[250px] p-4 bg-surface-0 dark:bg-surface-900 border border-surface-200 dark:border-surface-700 rounded-md shadow-md"
        >
          <div v-if="currentUser" class="flex flex-col gap-3">
            <div class="border-b border-surface-200 dark:border-surface-700 pb-2">
              <div class="font-medium text-surface-900 dark:text-surface-0">
                {{ currentUser.username }}
              </div>
              <div class="text-sm text-surface-600 dark:text-surface-400">
                {{ currentUser.email }}
              </div>
            </div>
            <button
              @click="goToSettings"
              class="flex items-center gap-2 p-2 rounded-md hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors"
            >
              <i class="pi pi-cog"></i>
              <span>User Settings</span>
            </button>
          </div>
        </div>
      </div>

      <button
        class="layout-topbar-menu-button layout-topbar-action"
        v-styleclass="{
          selector: '@next',
          enterFromClass: 'hidden',
          enterActiveClass: 'animate-scalein',
          leaveToClass: 'hidden',
          leaveActiveClass: 'animate-fadeout',
          hideOnOutsideClick: true,
        }"
      >
        <i class="pi pi-ellipsis-v"></i>
      </button>

      <div class="layout-topbar-menu hidden lg:block">
        <div class="layout-topbar-menu-content">
          <button type="button" class="layout-topbar-action" @click="handleLogout">
            <i class="pi pi-sign-out"></i>
            <span>Logout</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
