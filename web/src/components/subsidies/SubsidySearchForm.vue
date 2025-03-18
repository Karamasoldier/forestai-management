<template>
  <div class="card mb-4">
    <div class="card-body">
      <form @submit.prevent="onSubmit">
        <div class="row g-3">
          <div class="col-md-4">
            <label for="project_type" class="form-label">Type de projet</label>
            <select 
              class="form-select" 
              id="project_type" 
              v-model="localParams.project_type" 
              required
              :disabled="loading"
            >
              <option value="">Sélectionnez...</option>
              <option value="reboisement">Reboisement</option>
              <option value="boisement">Boisement</option>
              <option value="amelioration">Amélioration forestière</option>
              <option value="protection">Protection forestière</option>
              <option value="autre">Autre</option>
            </select>
          </div>
          
          <div class="col-md-4">
            <label for="region" class="form-label">Région</label>
            <select 
              class="form-select" 
              id="region" 
              v-model="localParams.region"
              :disabled="loading"
            >
              <option value="">Toutes les régions</option>
              <option v-for="region in regions" :key="region" :value="region">{{ region }}</option>
            </select>
          </div>
          
          <div class="col-md-4">
            <label for="owner_type" class="form-label">Type de propriétaire</label>
            <select 
              class="form-select" 
              id="owner_type" 
              v-model="localParams.owner_type"
              :disabled="loading"
            >
              <option value="">Tous les types</option>
              <option value="private">Privé</option>
              <option value="public">Public</option>
              <option value="association">Association</option>
            </select>
          </div>
          
          <div class="col-12 d-flex justify-content-end">
            <button 
              type="button" 
              class="btn btn-outline-secondary me-2" 
              @click="resetForm"
              :disabled="loading"
            >
              Réinitialiser
            </button>
            <button 
              type="submit" 
              class="btn btn-primary" 
              :disabled="loading || !isFormValid"
            >
              <span v-if="loading" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
              Rechercher
            </button>
          </div>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import { reactive, computed, toRefs } from 'vue'

export default {
  name: 'SubsidySearchForm',
  props: {
    searchParams: {
      type: Object,
      default: () => ({
        project_type: '',
        region: '',
        owner_type: ''
      })
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  emits: ['search', 'reset'],
  setup(props, { emit }) {
    const localParams = reactive({
      project_type: props.searchParams.project_type,
      region: props.searchParams.region,
      owner_type: props.searchParams.owner_type
    })
    
    const regions = [
      'Auvergne-Rhône-Alpes',
      'Bourgogne-Franche-Comté',
      'Bretagne',
      'Centre-Val de Loire',
      'Corse',
      'Grand Est',
      'Hauts-de-France',
      'Île-de-France',
      'Normandie',
      'Nouvelle-Aquitaine',
      'Occitanie',
      'Pays de la Loire',
      'Provence-Alpes-Côte d\'Azur'
    ]
    
    const isFormValid = computed(() => {
      return localParams.project_type !== ''
    })
    
    const onSubmit = () => {
      if (!isFormValid.value) return
      emit('search', localParams)
    }
    
    const resetForm = () => {
      localParams.project_type = ''
      localParams.region = ''
      localParams.owner_type = ''
      emit('reset')
    }
    
    return {
      localParams,
      regions,
      isFormValid,
      onSubmit,
      resetForm
    }
  }
}
</script>
