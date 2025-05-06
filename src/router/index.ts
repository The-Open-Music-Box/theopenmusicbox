import { createRouter, createWebHistory } from 'vue-router'
import MainContent from '../views/HomePage.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: MainContent
  },
  {
    path: '/about',
    name: 'About',
    component: () => import('../views/AboutPage.vue')
  },
  {
    path: '/contact',
    name: 'Contact',
    component: () => import('../views/ContactPage.vue')
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/SettingsPage.vue')
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router