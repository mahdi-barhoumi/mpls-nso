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

// Notifications state and polling logic
const notifications = ref([])
let pollingInterval = null

const fetchNotifications = async () => {
  try {
    // Fetch all notifications, not just unacknowledged
    const data = await notificationService.fetchNotifications({}) // pass empty params
    notifications.value = data.map(notification => ({
      ...notification,
      timestamp: new Date(notification.created_at)
    }))
  } catch (error) {
    // Optionally handle error
  }
}

const startPolling = (intervalMs = 30000) => {
  stopPolling()
  fetchNotifications()
  pollingInterval = setInterval(fetchNotifications, intervalMs)
}

const stopPolling = () => {
  if (pollingInterval) {
    clearInterval(pollingInterval)
    pollingInterval = null
  }
}

const acknowledgeNotification = async (id) => {
  await notificationService.acknowledgeNotification(id)
  notifications.value = notifications.value.map(n =>
    n.id === id ? { ...n, acknowledged: true } : n
  )
}

const deleteNotification = async (id) => {
  await notificationService.deleteNotification(id)
  notifications.value = notifications.value.filter(n => n.id !== id)
}

const clearAllNotifications = async () => {
  // Delete all notifications in parallel
  await Promise.all(notifications.value.map(n => deleteNotification(n.id)))
}

const notificationCount = computed(() => notifications.value?.filter(n => !n.acknowledged).length || 0)

onMounted(() => {
  currentUser.value = authService.getCurrentUser()
  startPolling()
})

onUnmounted(() => {
  stopPolling()
})

async function handleLogout() {
  await authService.logout()
  router.push('/auth/login')
}

function goToSettings() {
  router.push('settings/user')
}

// Notification click handler using source and id
async function handleNotificationClick(notification) {
  // Route based on notification source
  if (notification.source === 'monitoring') {
    router.push('/monitoring')
  } else if (notification.source === 'provisioning') {
    router.push('/sites')
  } else if (notification.source === 'network') {
    router.push('/logs')
  } else if (notification.source === 'security') {
    router.push('/logs')
  }
  // Always acknowledge after click
  if (!notification.acknowledged) {
    await acknowledgeNotification(notification.id)
  }
}

// Icon and color based on severity and source
const getNotificationIcon = (notification) => {
  if (notification.severity === 'critical') return 'pi-exclamation-triangle'
  if (notification.severity === 'warning') return 'pi-exclamation-circle'
  if (notification.severity === 'info') return 'pi-info-circle'
  return 'pi-bell'
}

const getNotificationColor = (notification) => {
  if (notification.severity === 'critical') return 'text-red-600'
  if (notification.severity === 'warning') return 'text-yellow-500'
  if (notification.severity === 'info') return 'text-blue-500'
  return 'text-gray-500'
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
          <!-- Show badge for unacknowledged notifications -->
          <span
            v-if="notificationCount > 0"
            class="absolute -top-1 -right-0 bg-gray-700 text-white rounded-full h-5 w-5 flex items-center justify-center z-10"
            style="font-size:10px;"
          >
            {{ notificationCount }}
          </span>
        </button>

        <div
          class="hidden absolute right-0 top-[3rem] w-[400px] max-h-[600px] overflow-y-auto p-4 bg-surface-0 dark:bg-surface-900 border border-surface-200 dark:border-surface-700 rounded-md shadow-md"
          style="opacity:0.93;"
        >
          <div
            class="flex justify-between items-center mb-4 border-b pb-2 border-surface-200 dark:border-surface-700"
          >
            <h3 class="text-lg font-semibold text-surface-900 dark:text-surface-0 m-0">
              Notifications
            </h3>
            <button
              v-if="notifications.length > 0"
              @click="clearAllNotifications"
              class="text-sm opacity-90 px-3 py-1 rounded transition-colors bg-transparent text-surface-700 dark:text-surface-200 hover:bg-surface-100 dark:hover:bg-surface-800"
              style="box-shadow:none;"
            >
              Clear all
            </button>
          </div>

          <div v-if="notifications.length > 0" class="flex flex-col gap-0">
            <div
              v-for="(notification, idx) in notifications"
              :key="notification.id"
              :class="[
                'flex p-3 rounded-none transition-colors text-left relative border-0 group',
                notification.acknowledged 
                  ? 'opacity-60 cursor-default bg-surface-50 dark:bg-surface-900'
                  : 'cursor-pointer hover:bg-surface-100 dark:hover:bg-surface-800',
                idx !== notifications.length - 1 ? 'border-b border-surface-100 dark:border-surface-800' : ''
              ]"
              style="outline:none;"
            >
              <div class="flex flex-col items-center mr-3 mt-0.5">
                <i :class="['pi', getNotificationIcon(notification), getNotificationColor(notification), 'text-xl']"></i>
              </div>
              <div 
                class="flex-1 min-w-0"
                @click="!notification.acknowledged && acknowledgeNotification(notification.id)"
                style="position:relative;"
              >
                <div class="flex items-center gap-2 mb-0.5">
                  <span class="font-semibold text-xs" :class="getNotificationColor(notification)">
                    {{ notification.severity_display }}
                  </span>
                  <span class="text-xs text-surface-500 truncate max-w-[120px]">
                    {{ notification.source_display }}
                  </span>
                </div>
                <p class="text-surface-900 dark:text-surface-0 font-medium text-sm mb-0 truncate">
                  {{ notification.title }}
                </p>
                <p class="text-surface-700 dark:text-surface-200 text-xs mb-1 truncate">
                  {{ notification.message }}
                </p>
                <p class="text-xs text-surface-500">
                  {{ new Date(notification.timestamp).toLocaleString() }}
                </p>
              </div>
              <button
                @click.stop="deleteNotification(notification.id)"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-lg text-gray-400 hover:text-red-500 transition p-0 bg-transparent border-0 focus:outline-none"
                title="Delete"
                style="z-index:2;"
              >
                &times;
              </button>
            </div>
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
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
