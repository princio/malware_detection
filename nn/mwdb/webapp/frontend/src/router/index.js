import Vue from 'vue'
import VueRouter from 'vue-router'
import Home from '../views/Home.vue'
import Applies from '../views/Applies.vue'
import Apply from '../views/Apply.vue'
import Pcaps from '../views/Pcaps.vue'

Vue.use(VueRouter)

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/applies',
    name: 'Applies',
    component: Applies
  },
  {
    path: '/apply/:apply_id',
    name: 'ApplyRoute',
    component: Apply,
    props: true 
  },
  {
    path: '/comparer',
    name: 'Comparer',
    component: Applies
  },
  {
    path: '/pcaps',
    name: 'Pcaps',
    component: Pcaps
  },
  {
    path: '/about',
    name: 'About',
    // route level code-splitting
    // this generates a separate chunk (about.[hash].js) for this route
    // which is lazy-loaded when the route is visited.
    component: () => import(/* webpackChunkName: "about" */ '../views/About.vue')
  }
]

const router = new VueRouter({
  routes
})

export default router
