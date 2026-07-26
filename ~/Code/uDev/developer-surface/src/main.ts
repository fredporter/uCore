import { createApp } from 'vue'
import { createPinia } from 'pinia'
import DeveloperSurface from './DeveloperSurface.vue'

const app = createApp(DeveloperSurface)
app.use(createPinia())
app.mount('#app')