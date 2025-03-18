<template>
  <div class="main-layout">
    <!-- En-tête -->
    <header class="header">
      <div class="header-left">
        <Button 
          icon="pi pi-bars" 
          text 
          rounded 
          class="menu-toggle" 
          @click="menuVisible = !menuVisible" 
        />
        <h1 class="app-title">ForestAI</h1>
      </div>
      
      <div class="header-right">
        <Button 
          icon="pi pi-user" 
          text 
          rounded 
          class="user-profile" 
          @click="userMenuVisible = !userMenuVisible" 
        />
        <Menu 
          id="user-menu" 
          ref="userMenu" 
          :model="userMenuItems" 
          :popup="true" 
        />
      </div>
    </header>
    
    <!-- Layout principal -->
    <div class="main-container">
      <!-- Menu latéral -->
      <aside class="sidebar" :class="{ 'sidebar-visible': menuVisible }">
        <div class="sidebar-content">
          <div class="nav-header">
            <img src="@/assets/images/logo.svg" alt="ForestAI Logo" class="logo" />
            <h3>ForestAI Management</h3>
          </div>
          
          <div class="nav-links">
            <router-link to="/dashboard" class="nav-link" active-class="active">
              <i class="pi pi-chart-line"></i>
              <span>Tableau de bord</span>
            </router-link>
            
            <router-link to="/parcels" class="nav-link" active-class="active">
              <i class="pi pi-map"></i>
              <span>Parcelles</span>
            </router-link>
            
            <router-link to="/subsidies" class="nav-link" active-class="active">
              <i class="pi pi-euro"></i>
              <span>Subventions</span>
            </router-link>
            
            <router-link to="/diagnostics" class="nav-link" active-class="active">
              <i class="pi pi-file-edit"></i>
              <span>Diagnostics</span>
            </router-link>
            
            <router-link to="/reports" class="nav-link" active-class="active">
              <i class="pi pi-file-pdf"></i>
              <span>Rapports</span>
            </router-link>
          </div>
        </div>
      </aside>
      
      <!-- Contenu principal -->
      <main class="content">
        <slot></slot>
      </main>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import { useAuthStore } from '@/stores/auth';

export default {
  name: 'MainLayout',
  setup() {
    const menuVisible = ref(true);
    const userMenuVisible = ref(false);
    const userMenu = ref(null);
    const authStore = useAuthStore();
    
    // Items du menu utilisateur
    const userMenuItems = ref([
      {
        label: 'Profil',
        icon: 'pi pi-user',
        command: () => {}
      },
      {
        label: 'Paramètres',
        icon: 'pi pi-cog',
        command: () => {}
      },
      {
        separator: true
      },
      {
        label: 'Déconnexion',
        icon: 'pi pi-sign-out',
        command: () => {
          authStore.logout();
        }
      }
    ]);
    
    // Affiche/masque le menu utilisateur
    const toggleUserMenu = (event) => {
      userMenu.value.toggle(event);
    };
    
    // Adapte l'affichage selon la taille de l'écran
    onMounted(() => {
      const handleResize = () => {
        if (window.innerWidth < 768) {
          menuVisible.value = false;
        } else {
          menuVisible.value = true;
        }
      };
      
      window.addEventListener('resize', handleResize);
      handleResize(); // État initial
      
      return () => {
        window.removeEventListener('resize', handleResize);
      };
    });
    
    return {
      menuVisible,
      userMenuVisible,
      userMenu,
      userMenuItems,
      toggleUserMenu
    };
  }
};
</script>

<style lang="scss" scoped>
.main-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 1rem;
  background-color: var(--primary-color);
  color: var(--primary-color-text);
  height: 60px;
  
  .header-left, .header-right {
    display: flex;
    align-items: center;
  }
  
  .app-title {
    margin: 0 0 0 1rem;
    font-size: 1.5rem;
  }
  
  .user-profile {
    margin-left: 0.5rem;
  }
}

.main-container {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.sidebar {
  width: 250px;
  background-color: var(--surface-card);
  border-right: 1px solid var(--surface-border);
  transition: transform 0.3s ease;
  overflow-y: auto;
  
  @media (max-width: 768px) {
    position: fixed;
    top: 60px;
    bottom: 0;
    left: 0;
    z-index: 999;
    transform: translateX(-100%);
    
    &.sidebar-visible {
      transform: translateX(0);
    }
  }
  
  .sidebar-content {
    display: flex;
    flex-direction: column;
    height: 100%;
  }
  
  .nav-header {
    padding: 1rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    border-bottom: 1px solid var(--surface-border);
    
    .logo {
      width: 60px;
      height: 60px;
      margin-bottom: 0.5rem;
    }
    
    h3 {
      margin: 0;
      font-size: 1rem;
      text-align: center;
      color: var(--text-color);
    }
  }
  
  .nav-links {
    padding: 1rem 0;
    
    .nav-link {
      display: flex;
      align-items: center;
      padding: 0.75rem 1rem;
      color: var(--text-color);
      text-decoration: none;
      transition: background-color 0.2s;
      
      &:hover {
        background-color: var(--surface-hover);
      }
      
      &.active {
        background-color: var(--surface-ground);
        border-left: 3px solid var(--primary-color);
        color: var(--primary-color);
      }
      
      i {
        margin-right: 0.75rem;
        font-size: 1.2rem;
      }
    }
  }
}

.content {
  flex: 1;
  padding: 1rem;
  overflow-y: auto;
  background-color: var(--surface-ground);
}
</style>
