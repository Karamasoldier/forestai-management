<template>
  <div class="login-form">
    <h2>Connexion</h2>
    
    <form @submit.prevent="handleLogin">
      <div class="form-group">
        <label for="email">Email</label>
        <InputText 
          id="email" 
          v-model="form.email" 
          type="email" 
          :class="{'p-invalid': v$.email.$invalid && v$.email.$dirty}"
          class="w-full"
          aria-describedby="email-error"
        />
        <small id="email-error" class="p-error" v-if="v$.email.$invalid && v$.email.$dirty">
          {{ v$.email.$errors[0].$message }}
        </small>
      </div>
      
      <div class="form-group">
        <label for="password">Mot de passe</label>
        <InputText 
          id="password" 
          v-model="form.password" 
          type="password" 
          :class="{'p-invalid': v$.password.$invalid && v$.password.$dirty}"
          class="w-full"
          aria-describedby="password-error"
        />
        <small id="password-error" class="p-error" v-if="v$.password.$invalid && v$.password.$dirty">
          {{ v$.password.$errors[0].$message }}
        </small>
      </div>
      
      <div class="form-options">
        <div class="p-field-checkbox">
          <Checkbox id="remember" v-model="form.remember" binary />
          <label for="remember" class="p-checkbox-label">Se souvenir de moi</label>
        </div>
        <router-link to="/auth/forgot-password" class="forgot-password">
          Mot de passe oublié?
        </router-link>
      </div>
      
      <div class="form-actions">
        <Button 
          type="submit" 
          label="Connexion" 
          icon="pi pi-sign-in" 
          class="w-full" 
          :loading="loading"
        />
      </div>
      
      <div class="form-footer">
        <p>
          Pas encore de compte?
          <router-link to="/auth/register" class="register-link">
            Inscription
          </router-link>
        </p>
      </div>
    </form>
  </div>
</template>

<script>
import { useVuelidate } from '@vuelidate/core';
import { required, email, minLength } from '@vuelidate/validators';
import { reactive, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useToast } from 'primevue/usetoast';

export default {
  name: 'LoginView',
  setup() {
    const router = useRouter();
    const authStore = useAuthStore();
    const toast = useToast();
    
    // Formulaire de connexion
    const form = reactive({
      email: '',
      password: '',
      remember: false
    });
    
    // Règles de validation
    const rules = computed(() => ({
      email: { required, email },
      password: { required, minLength: minLength(6) }
    }));
    
    const v$ = useVuelidate(rules, form);
    
    // État de chargement
    const loading = computed(() => authStore.loading);
    
    // Gestion de la connexion
    const handleLogin = async () => {
      const isValid = await v$.value.$validate();
      
      if (!isValid) {
        toast.add({
          severity: 'error',
          summary: 'Erreur',
          detail: 'Veuillez corriger les erreurs dans le formulaire',
          life: 3000
        });
        return;
      }
      
      const success = await authStore.login({
        email: form.email,
        password: form.password,
        remember: form.remember
      });
      
      if (success) {
        toast.add({
          severity: 'success',
          summary: 'Succès',
          detail: 'Vous êtes connecté',
          life: 3000
        });
        router.push('/dashboard');
      } else {
        toast.add({
          severity: 'error',
          summary: 'Erreur',
          detail: authStore.error || 'Identifiants incorrects',
          life: 5000
        });
      }
    };
    
    return {
      form,
      v$,
      loading,
      handleLogin
    };
  }
};
</script>

<style lang="scss" scoped>
.login-form {
  padding: 2rem;
  
  h2 {
    margin-top: 0;
    margin-bottom: 1.5rem;
    text-align: center;
    color: var(--primary-color);
  }
  
  .form-group {
    margin-bottom: 1.5rem;
    
    label {
      display: block;
      margin-bottom: 0.5rem;
      font-weight: 500;
    }
  }
  
  .form-options {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
    
    .forgot-password {
      color: var(--primary-color);
      font-size: 0.875rem;
      text-decoration: none;
      
      &:hover {
        text-decoration: underline;
      }
    }
  }
  
  .form-actions {
    margin-bottom: 1.5rem;
  }
  
  .form-footer {
    text-align: center;
    font-size: 0.875rem;
    
    .register-link {
      color: var(--primary-color);
      font-weight: 500;
      text-decoration: none;
      
      &:hover {
        text-decoration: underline;
      }
    }
  }
}
</style>
