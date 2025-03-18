import { defineStore } from 'pinia';
import axios from 'axios';
import router from '@/router';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    user: JSON.parse(localStorage.getItem('user')) || null,
    loading: false,
    error: null
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    currentUser: (state) => state.user,
    isAdmin: (state) => state.user?.role === 'admin'
  },

  actions: {
    async login(credentials) {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await axios.post('/api/auth/login', credentials);
        const { token, user } = response.data;
        
        this.setToken(token);
        this.setUser(user);
        
        return true;
      } catch (error) {
        this.error = error.response?.data?.message || 'Erreur d\'authentification';
        return false;
      } finally {
        this.loading = false;
      }
    },
    
    async register(userData) {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await axios.post('/api/auth/register', userData);
        const { token, user } = response.data;
        
        this.setToken(token);
        this.setUser(user);
        
        return true;
      } catch (error) {
        this.error = error.response?.data?.message || 'Erreur d\'enregistrement';
        return false;
      } finally {
        this.loading = false;
      }
    },
    
    async logout() {
      try {
        // Optionnel: Appel au backend pour invalider le token
        await axios.post('/api/auth/logout', {}, {
          headers: { Authorization: `Bearer ${this.token}` }
        });
      } catch (error) {
        // Ignorer l'erreur, on déconnecte quand même
      }
      
      this.clearAuth();
      router.push('/auth/login');
    },
    
    async checkAuthentication() {
      if (!this.token) return false;
      
      try {
        // Vérifier la validité du token
        const response = await axios.get('/api/auth/me', {
          headers: { Authorization: `Bearer ${this.token}` }
        });
        
        // Mettre à jour les infos utilisateur
        this.setUser(response.data);
        return true;
      } catch (error) {
        // Token invalide ou expiré
        this.clearAuth();
        return false;
      }
    },
    
    setToken(token) {
      this.token = token;
      localStorage.setItem('token', token);
      // Configurer axios pour inclure le token dans toutes les requêtes
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    },
    
    setUser(user) {
      this.user = user;
      localStorage.setItem('user', JSON.stringify(user));
    },
    
    clearAuth() {
      this.token = null;
      this.user = null;
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      delete axios.defaults.headers.common['Authorization'];
    }
  }
});
