<template>
  <div class="auth-layout">
    <div class="auth-container">
      <div class="auth-logo">
        <img src="@/assets/images/logo.svg" alt="ForestAI Logo" />
        <h1>ForestAI Management</h1>
      </div>
      
      <div class="auth-card">
        <slot></slot>
      </div>
      
      <div class="auth-footer">
        <p>&copy; {{ currentYear }} ForestAI - Tous droits réservés</p>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue';

export default {
  name: 'AuthLayout',
  setup() {
    const currentYear = computed(() => new Date().getFullYear());
    
    return {
      currentYear
    };
  }
};
</script>

<style lang="scss" scoped>
.auth-layout {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, var(--green-50) 0%, var(--green-100) 100%);
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-image: url('@/assets/images/forest-bg.jpg');
    background-size: cover;
    background-position: center;
    opacity: 0.1;
    z-index: -1;
  }
}

.auth-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  max-width: 460px;
  padding: 2rem;
}

.auth-logo {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 2rem;
  
  img {
    width: 80px;
    height: 80px;
    margin-bottom: 1rem;
  }
  
  h1 {
    color: var(--green-900);
    font-size: 1.8rem;
    margin: 0;
    text-align: center;
  }
}

.auth-card {
  width: 100%;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.auth-footer {
  margin-top: 2rem;
  text-align: center;
  color: var(--green-800);
  font-size: 0.875rem;
}
</style>
