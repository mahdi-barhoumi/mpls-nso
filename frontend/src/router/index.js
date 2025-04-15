import { createRouter, createWebHistory } from 'vue-router'
import AppLayout from '@/layout/AppLayout.vue'
import axios from 'axios'

// Setup route guard
const requiresSetup = async (to, from, next) => {
  try {
    const response = await axios.get('http://127.0.0.1:8000/api/setup/status/')
    if (response.data.needs_setup && to.name !== 'setup') {
      next({ name: 'setup' })
    } else if (!response.data.needs_setup && to.name === 'setup') {
      next({ name: 'dashboard' })
    } else {
      next()
    }
  } catch (error) {
    console.error('Error checking setup status:', error)
    next()
  }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/setup',
      name: 'setup',
      component: () => import('@/views/Setup.vue'),
    },
    {
      path: '/',
      component: AppLayout,
      beforeEnter: requiresSetup,
      children: [
        {
          path: '/',
          name: 'dashboard',
          component: () => import('@/views/Dashboard.vue'),
        },
        {
          path: '/pages/empty',
          name: 'empty',
          component: () => import('@/views/pages/Empty.vue'),
        },
        {
          path: '/customers',
          name: 'customer',
          component: () => import('@/views/pages/CustomerCrud.vue'),
        },
        {
          path: '/sites',
          name: 'sites',
          component: () => import('@/views/pages/SiteCrud.vue'),
        },
        {
          path: '/vpn',
          name: 'vpns',
          component: () => import('@/views/pages/VPNCrud.vue'),
        },
      ],
    },
    {
      path: '/landing',
      name: 'landing',
      component: () => import('@/views/pages/Landing.vue'),
    },
    {
      path: '/pages/notfound',
      name: 'notfound',
      component: () => import('@/views/pages/NotFound.vue'),
    },

    {
      path: '/auth/login',
      name: 'login',
      component: () => import('@/views/pages/auth/Login.vue'),
    },
    {
      path: '/auth/access',
      name: 'accessDenied',
      component: () => import('@/views/pages/auth/Access.vue'),
    },
    {
      path: '/auth/error',
      name: 'error',
      component: () => import('@/views/pages/auth/Error.vue'),
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/pages/auth/Register.vue'),
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/pages/NotFound.vue'),
    },
  ],
})

// Navigation guard to check setup status
router.beforeEach(async (to, from, next) => {
  if (to.path === '/setup') {
    next()
    return
  }

  try {
    const response = await fetch('http://127.0.0.1:8000/api/setup/status/')
    const data = await response.json()

    if (data.needs_setup) {
      next('/setup')
    } else {
      next()
    }
  } catch (error) {
    console.error('Error checking setup status:', error)
    next()
  }
})

export default router
