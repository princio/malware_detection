import Vue from 'vue'
import App from './App.vue'
import { library } from '@fortawesome/fontawesome-svg-core'
import { faSortNumericUpAlt, faSortNumericDown } from '@fortawesome/free-solid-svg-icons'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import router from './router'


Vue.config.productionTip = false
Vue.config.devtools = true

library.add(faSortNumericUpAlt)
library.add(faSortNumericDown)

Vue.component('font-awesome-icon', FontAwesomeIcon)

new Vue({
  render: h => h(App),
  router,
  devtool: 'source-map'
}).$mount('#app')
