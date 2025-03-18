<template>
  <div id="app">
    <Toast position="top-right" />
    
    <template v-if="isAuthenticated">
      <main-layout>
        <router-view />
      </main-layout>
    </template>
    
    <template v-else>
      <auth-layout>
        <router-view />
      </auth-layout>
    </template>
  </div>
</template>

<script>
import MainLayout from '@/layouts/MainLayout.vue';
import AuthLayout from '@/layouts/AuthLayout.vue';
import { useAuthStore } from '@/stores/auth';
import { computed, onMounted } from 'vue';

export default {
  name: 'App',
  components: {
    MainLayout,
    AuthLayout
  },
  setup() {
    const authStore = useAuthStore();
    
    // Vérifier si l'utilisateur est déjà authentifié (via token stocké)
    onMounted(() => {
      authStore.checkAuthentication();
    });
    
    const isAuthenticated = computed(() => authStore.isAuthenticated);
    
    return {
      isAuthenticated
    };
  }
};
</script>

<style lang="scss">
/* Styles globaux */
html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  font-family: var(--font-family);
  background-color: var(--surface-ground);
  color: var(--text-color);
}

#app {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.p-component {
  font-family: var(--font-family);
}
</style>
