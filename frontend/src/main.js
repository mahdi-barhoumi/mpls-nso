import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import PrimeVue from 'primevue/config'
import Aura from '@primeuix/themes/aura'
import '@/assets/styles.scss'
import ConfirmationService from 'primevue/confirmationservice'
import ToastService from 'primevue/toastservice'

const app = createApp(App)

app.use(router)
app.use(PrimeVue, {
  theme: {
    preset: Aura,
    options: {
      prefix: 'p',
      darkModeSelector: '.app-dark',
    },
  },
})
app.use(ToastService)
app.use(ConfirmationService)

// Mount the app and hide preloader with animation
app.mount('#app')

// Hide preloader after app is mounted
const preloader = document.querySelector('.preloader')
if (preloader) {
  // Wait for initial animations to complete
  setTimeout(() => {
    // Add fade-out class to trigger transitions
    preloader.classList.add('fade-out')

    // Remove from DOM after animation completes
    preloader.addEventListener(
      'transitionend',
      () => {
        preloader.remove()
      },
      { once: true },
    )
  }, 800)
}
