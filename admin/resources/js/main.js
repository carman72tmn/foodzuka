import { createApp } from 'vue'
import App from '@/App.vue'
import { registerPlugins } from '@core/utils/plugins'

// Styles
import '@core-scss/template/index.scss'
import '@layouts/styles/index.scss'
import '@styles/styles.scss'

// Create vue app
const app = createApp(App)


// Toast
import Toast from 'vue-toastification'
import 'vue-toastification/dist/index.css'

// Register plugins
registerPlugins(app)
app.use(Toast)

// Mount vue app
app.mount('#app')
