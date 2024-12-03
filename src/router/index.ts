import { createRouter, createWebHistory } from 'vue-router'
import MainContent from '../views/HomePage.vue'
import About from '../views/AboutPage.vue'
import Contact from '../views/ContactPage.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: MainContent
  },
  {
    path: '/about',
    name: 'About',
    component: About
  },
  {
    path: '/contact',
    name: 'Contact',
    component: Contact
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router