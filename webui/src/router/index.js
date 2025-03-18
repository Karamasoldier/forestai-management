import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

// Layouts
const AuthLayout = () => import('@/layouts/AuthLayout.vue');
const MainLayout = () => import('@/layouts/MainLayout.vue');

// Views - Auth
const Login = () => import('@/views/auth/Login.vue');
const Register = () => import('@/views/auth/Register.vue');
const ForgotPassword = () => import('@/views/auth/ForgotPassword.vue');

// Views - Main
const Dashboard = () => import('@/views/Dashboard.vue');
const ParcelsList = () => import('@/views/parcels/ParcelsList.vue');
const ParcelDetail = () => import('@/views/parcels/ParcelDetail.vue');
const SubsidiesList = () => import('@/views/subsidies/SubsidiesList.vue');
const SubsidyDetail = () => import('@/views/subsidies/SubsidyDetail.vue');
const DiagnosticsList = () => import('@/views/diagnostics/DiagnosticsList.vue');
const DiagnosticDetail = () => import('@/views/diagnostics/DiagnosticDetail.vue');
const ReportsList = () => import('@/views/reports/ReportsList.vue');
const ReportDetail = () => import('@/views/reports/ReportDetail.vue');

// Routes
const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/auth',
    component: AuthLayout,
    children: [
      {
        path: 'login',
        name: 'Login',
        component: Login
      },
      {
        path: 'register',
        name: 'Register',
        component: Register
      },
      {
        path: 'forgot-password',
        name: 'ForgotPassword',
        component: ForgotPassword
      }
    ]
  },
  {
    path: '/',
    component: MainLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: Dashboard
      },
      {
        path: 'parcels',
        name: 'ParcelsList',
        component: ParcelsList
      },
      {
        path: 'parcels/:id',
        name: 'ParcelDetail',
        component: ParcelDetail,
        props: true
      },
      {
        path: 'subsidies',
        name: 'SubsidiesList',
        component: SubsidiesList
      },
      {
        path: 'subsidies/:id',
        name: 'SubsidyDetail',
        component: SubsidyDetail,
        props: true
      },
      {
        path: 'diagnostics',
        name: 'DiagnosticsList',
        component: DiagnosticsList
      },
      {
        path: 'diagnostics/:id',
        name: 'DiagnosticDetail',
        component: DiagnosticDetail,
        props: true
      },
      {
        path: 'reports',
        name: 'ReportsList',
        component: ReportsList
      },
      {
        path: 'reports/:id',
        name: 'ReportDetail',
        component: ReportDetail,
        props: true
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/dashboard'
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

// Navigation guards
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
  
  if (requiresAuth && !authStore.isAuthenticated) {
    next('/auth/login');
  } else if (to.path === '/auth/login' && authStore.isAuthenticated) {
    next('/dashboard');
  } else {
    next();
  }
});

export default router;
