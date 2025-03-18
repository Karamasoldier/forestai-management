<template>
  <div class="parcels-list">
    <div class="page-header">
      <h1>Parcelles forestières</h1>
      <div class="actions">
        <Button label="Nouvelle parcelle" icon="pi pi-plus" @click="showNewParcelDialog" />
        <Button label="Filtres" icon="pi pi-filter" outlined class="ml-2" @click="showFiltersDialog" />
      </div>
    </div>

    <div class="grid">
      <div class="col-12">
        <Card>
          <template #content>
            <!-- Barre de recherche -->
            <div class="search-container mb-3">
              <span class="p-input-icon-left w-full md:w-6">
                <i class="pi pi-search" />
                <InputText v-model="searchQuery" placeholder="Rechercher une parcelle..." class="w-full" />
              </span>
            </div>

            <!-- Tableau des parcelles -->
            <DataTable 
              :value="filteredParcels" 
              :paginator="true" 
              :rows="10"
              :rowsPerPageOptions="[5, 10, 20, 50]"
              :loading="loading"
              v-model:selection="selectedParcels"
              v-model:filters="filters"
              filterDisplay="menu"
              responsiveLayout="scroll"
              dataKey="id"
              :globalFilterFields="['id', 'commune', 'section', 'numero', 'forestType', 'area']"
              class="p-datatable-sm"
              stripedRows
              @row-click="onRowClick"
            >
              <template #empty>
                <div class="text-center p-4">
                  Aucune parcelle trouvée.
                </div>
              </template>
              
              <template #loading>
                <div class="text-center p-4">
                  Chargement des parcelles...
                </div>
              </template>

              <Column selectionMode="multiple" headerStyle="width: 3em" />
              
              <Column field="id" header="ID" sortable style="width: 15%">
                <template #body="{ data }">
                  <span class="font-semibold">{{ data.id }}</span>
                </template>
              </Column>
              
              <Column field="commune" header="Commune" sortable style="width: 15%" />
              
              <Column field="section" header="Section" sortable style="width: 10%" />
              
              <Column field="numero" header="Numéro" sortable style="width: 10%" />
              
              <Column field="forestType" header="Type" sortable style="width: 15%">
                <template #body="{ data }">
                  <span class="forest-type-badge" :class="'type-' + data.forestType.toLowerCase().replace(/\s+/g, '-')">
                    {{ data.forestType }}
                  </span>
                </template>
              </Column>
              
              <Column field="area" header="Surface (ha)" sortable style="width: 10%">
                <template #body="{ data }">
                  {{ formatNumber(data.area) }}
                </template>
              </Column>
              
              <Column field="health" header="Santé" sortable style="width: 10%">
                <template #body="{ data }">
                  <div class="health-indicator">
                    <div class="health-bar">
                      <div 
                        class="health-value" 
                        :style="{ width: data.health + '%', backgroundColor: getHealthColor(data.health) }"
                      ></div>
                    </div>
                    <span>{{ data.health }}%</span>
                  </div>
                </template>
              </Column>
              
              <Column style="width: 10%">
                <template #body="{ data }">
                  <div class="action-buttons">
                    <Button icon="pi pi-eye" text rounded title="Voir" @click.stop="viewParcel(data)" />
                    <Button icon="pi pi-pencil" text rounded title="Modifier" @click.stop="editParcel(data)" />
                    <Button icon="pi pi-trash" text rounded severity="danger" title="Supprimer" @click.stop="confirmDeleteParcel(data)" />
                  </div>
                </template>
              </Column>
            </DataTable>
          </template>
        </Card>
      </div>
    </div>

    <!-- Dialogue de création/édition de parcelle -->
    <Dialog 
      v-model:visible="parcelDialogVisible" 
      :style="{ width: '550px' }" 
      header="Parcelle forestière" 
      :modal="true"
      class="p-fluid"
    >
      <div class="grid p-fluid">
        <div class="col-12 md:col-6">
          <div class="field">
            <label for="commune">Commune</label>
            <InputText id="commune" v-model="parcel.commune" :class="{'p-invalid': submitted && !parcel.commune}" />
            <small class="p-error" v-if="submitted && !parcel.commune">La commune est requise.</small>
          </div>
        </div>
        
        <div class="col-12 md:col-3">
          <div class="field">
            <label for="section">Section</label>
            <InputText id="section" v-model="parcel.section" :class="{'p-invalid': submitted && !parcel.section}" />
            <small class="p-error" v-if="submitted && !parcel.section">La section est requise.</small>
          </div>
        </div>
        
        <div class="col-12 md:col-3">
          <div class="field">
            <label for="numero">Numéro</label>
            <InputText id="numero" v-model="parcel.numero" :class="{'p-invalid': submitted && !parcel.numero}" />
            <small class="p-error" v-if="submitted && !parcel.numero">Le numéro est requis.</small>
          </div>
        </div>
        
        <div class="col-12 md:col-6">
          <div class="field">
            <label for="forestType">Type de forêt</label>
            <Dropdown 
              id="forestType" 
              v-model="parcel.forestType" 
              :options="forestTypes" 
              optionLabel="name"
              optionValue="value"
              placeholder="Sélectionner un type"
              :class="{'p-invalid': submitted && !parcel.forestType}"
            />
            <small class="p-error" v-if="submitted && !parcel.forestType">Le type de forêt est requis.</small>
          </div>
        </div>
        
        <div class="col-12 md:col-6">
          <div class="field">
            <label for="area">Surface (ha)</label>
            <InputText id="area" v-model="parcel.area" type="number" step="0.01" :class="{'p-invalid': submitted && !parcel.area}" />
            <small class="p-error" v-if="submitted && !parcel.area">La surface est requise.</small>
          </div>
        </div>
        
        <div class="col-12">
          <div class="field">
            <label for="address">Adresse</label>
            <InputText id="address" v-model="parcel.address" />
          </div>
        </div>
        
        <div class="col-12">
          <div class="field">
            <label for="description">Description</label>
            <Textarea id="description" v-model="parcel.description" rows="3" autoResize />
          </div>
        </div>
      </div>
      
      <template #footer>
        <Button label="Annuler" icon="pi pi-times" text @click="hideDialog" />
        <Button label="Enregistrer" icon="pi pi-check" @click="saveParcel" />
      </template>
    </Dialog>

    <!-- Dialogue de confirmation de suppression -->
    <Dialog 
      v-model:visible="deleteDialogVisible" 
      :style="{ width: '450px' }" 
      header="Confirmation" 
      :modal="true"
    >
      <div class="confirmation-content">
        <i class="pi pi-exclamation-triangle mr-3" style="font-size: 2rem; color: var(--orange-500);" />
        <span v-if="parcel">Êtes-vous sûr de vouloir supprimer la parcelle <b>{{ parcel.id }}</b> ?</span>
      </div>
      
      <template #footer>
        <Button label="Non" icon="pi pi-times" text @click="deleteDialogVisible = false" />
        <Button label="Oui" icon="pi pi-check" severity="danger" @click="deleteParcel" />
      </template>
    </Dialog>

    <!-- Dialogue de filtres avancés -->
    <Dialog 
      v-model:visible="filtersDialogVisible" 
      :style="{ width: '550px' }" 
      header="Filtres avancés" 
      :modal="true"
      class="p-fluid"
    >
      <div class="grid">
        <div class="col-12 md:col-6">
          <div class="field">
            <label for="forestTypeFilter">Type de forêt</label>
            <MultiSelect 
              id="forestTypeFilter" 
              v-model="activeFilters.forestTypes" 
              :options="forestTypes" 
              optionLabel="name"
              optionValue="value"
              placeholder="Tous les types"
              display="chip"
            />
          </div>
        </div>
        
        <div class="col-12 md:col-6">
          <div class="field">
            <label for="healthFilter">Santé minimum (%)</label>
            <Slider v-model="activeFilters.minHealth" :min="0" :max="100" />
            <span class="mt-2 inline-block">{{ activeFilters.minHealth }}%</span>
          </div>
        </div>
        
        <div class="col-12 md:col-6">
          <div class="field">
            <label for="areaMinFilter">Surface minimum (ha)</label>
            <InputText id="areaMinFilter" v-model="activeFilters.minArea" type="number" step="0.1" />
          </div>
        </div>
        
        <div class="col-12 md:col-6">
          <div class="field">
            <label for="areaMaxFilter">Surface maximum (ha)</label>
            <InputText id="areaMaxFilter" v-model="activeFilters.maxArea" type="number" step="0.1" />
          </div>
        </div>
      </div>
      
      <template #footer>
        <Button label="Réinitialiser" icon="pi pi-refresh" text @click="resetFilters" />
        <Button label="Appliquer" icon="pi pi-check" @click="applyFilters" />
      </template>
    </Dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useToast } from 'primevue/usetoast';
import { FilterMatchMode } from 'primevue/api';
import { parcelService } from '@/services/api';

export default {
  name: 'ParcelsListView',
  setup() {
    const router = useRouter();
    const toast = useToast();
    
    // État
    const loading = ref(false);
    const parcels = ref([]);
    const selectedParcels = ref([]);
    const parcel = ref({});
    const parcelDialogVisible = ref(false);
    const deleteDialogVisible = ref(false);
    const filtersDialogVisible = ref(false);
    const submitted = ref(false);
    const searchQuery = ref('');
    
    // Options de type de forêt
    const forestTypes = [
      { name: 'Forêt de conifères', value: 'Conifères' },
      { name: 'Forêt de feuillus', value: 'Feuillus' },
      { name: 'Forêt mixte', value: 'Mixte' },
      { name: 'Taillis', value: 'Taillis' },
      { name: 'Plantation récente', value: 'Plantation' }
    ];
    
    // Configuration des filtres
    const filters = ref({
      global: { value: null, matchMode: FilterMatchMode.CONTAINS }
    });
    
    const activeFilters = reactive({
      forestTypes: [],
      minHealth: 0,
      minArea: null,
      maxArea: null
    });
    
    // Parcelles filtrées
    const filteredParcels = computed(() => {
      let filtered = [...parcels.value];
      
      // Filtre par recherche globale
      if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase();
        filtered = filtered.filter(p => 
          p.id.toLowerCase().includes(query) ||
          p.commune.toLowerCase().includes(query) ||
          p.section.toLowerCase().includes(query) ||
          p.numero.toLowerCase().includes(query) ||
          p.forestType.toLowerCase().includes(query)
        );
      }
      
      // Filtre par types de forêt
      if (activeFilters.forestTypes.length > 0) {
        filtered = filtered.filter(p => activeFilters.forestTypes.includes(p.forestType));
      }
      
      // Filtre par santé minimum
      if (activeFilters.minHealth > 0) {
        filtered = filtered.filter(p => p.health >= activeFilters.minHealth);
      }
      
      // Filtre par surface minimum
      if (activeFilters.minArea) {
        filtered = filtered.filter(p => p.area >= activeFilters.minArea);
      }
      
      // Filtre par surface maximum
      if (activeFilters.maxArea) {
        filtered = filtered.filter(p => p.area <= activeFilters.maxArea);
      }
      
      return filtered;
    });
    
    // Mise à jour du filtre global lorsque la recherche change
    watch(searchQuery, (newValue) => {
      filters.value.global.value = newValue;
    });
    
    // Récupération des parcelles
    const fetchParcels = async () => {
      try {
        loading.value = true;
        
        // En environnement réel, appel au service API
        // const response = await parcelService.getParcels();
        // parcels.value = response.data.result.parcels;
        
        // Données simulées pour le moment
        setTimeout(() => {
          parcels.value = [
            { id: 'P12345', commune: 'Saint-Martin-de-Crau', section: 'B', numero: '0012', forestType: 'Conifères', area: 15.234, health: 85, address: 'Route des Marais', description: 'Forêt de pins d\'Alep' },
            { id: 'P12346', commune: 'Saint-Martin-de-Crau', section: 'B', numero: '0013', forestType: 'Feuillus', area: 8.75, health: 92, address: 'Route des Marais', description: 'Forêt de chênes verts' },
            { id: 'P12347', commune: 'Arles', section: 'A', numero: '1234', forestType: 'Mixte', area: 22.5, health: 78, address: 'Chemin des Alpilles', description: 'Forêt mixte avec chênes et pins' },
            { id: 'P12348', commune: 'Arles', section: 'A', numero: '1235', forestType: 'Taillis', area: 5.8, health: 65, address: 'Chemin des Alpilles', description: 'Taillis de chênes pubescents' },
            { id: 'P12349', commune: 'Mouriès', section: 'C', numero: '0056', forestType: 'Plantation', area: 12.3, health: 95, address: 'Route D24', description: 'Plantation récente de pins parasols' },
            { id: 'P12350', commune: 'Mouriès', section: 'C', numero: '0057', forestType: 'Conifères', area: 18.9, health: 72, address: 'Route D24', description: 'Forêt ancienne de pins maritimes' },
            { id: 'P12351', commune: 'Fontvieille', section: 'D', numero: '2345', forestType: 'Feuillus', area: 7.45, health: 88, address: 'Chemin des Oliviers', description: 'Forêt de chênes-lièges' },
            { id: 'P12352', commune: 'Fontvieille', section: 'D', numero: '2346', forestType: 'Mixte', area: 14.2, health: 81, address: 'Chemin des Oliviers', description: 'Forêt mixte avec dominance de feuillus' },
            { id: 'P12353', commune: 'Salon-de-Provence', section: 'E', numero: '3456', forestType: 'Conifères', area: 25.8, health: 63, address: 'Route de la Crau', description: 'Forêt de cèdres en stress hydrique' },
            { id: 'P12354', commune: 'Salon-de-Provence', section: 'E', numero: '3457', forestType: 'Plantation', area: 9.3, health: 97, address: 'Route de la Crau', description: 'Plantation récente de pins parasols et cyprès' }
          ];
          loading.value = false;
        }, 1000);
        
      } catch (error) {
        console.error('Erreur lors de la récupération des parcelles:', error);
        toast.add({
          severity: 'error',
          summary: 'Erreur',
          detail: 'Impossible de récupérer les parcelles',
          life: 3000
        });
        loading.value = false;
      }
    };
    
    // Formatage des nombres
    const formatNumber = (value) => {
      return new Intl.NumberFormat('fr-FR', { 
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(value);
    };
    
    // Obtention de la couleur en fonction de la santé
    const getHealthColor = (health) => {
      if (health >= 80) return '#22C55E'; // Vert
      if (health >= 60) return '#F59E0B'; // Orange
      return '#EF4444'; // Rouge
    };
    
    // Afficher le dialogue de création de parcelle
    const showNewParcelDialog = () => {
      parcel.value = {
        commune: '',
        section: '',
        numero: '',
        forestType: '',
        area: null,
        address: '',
        description: ''
      };
      submitted.value = false;
      parcelDialogVisible.value = true;
    };
    
    // Afficher le dialogue de modification de parcelle
    const editParcel = (data) => {
      parcel.value = { ...data };
      parcelDialogVisible.value = true;
    };
    
    // Cacher le dialogue
    const hideDialog = () => {
      parcelDialogVisible.value = false;
      submitted.value = false;
    };
    
    // Sauvegarder la parcelle
    const saveParcel = async () => {
      submitted.value = true;
      
      if (parcel.value.commune && parcel.value.section && parcel.value.numero && parcel.value.forestType && parcel.value.area) {
        try {
          loading.value = true;
          
          if (parcel.value.id) {
            // Mise à jour d'une parcelle existante
            // En environnement réel, appel au service API
            // await parcelService.updateParcel(parcel.value.id, parcel.value);
            
            // Simulation
            const index = parcels.value.findIndex(p => p.id === parcel.value.id);
            if (index !== -1) {
              parcels.value[index] = { ...parcel.value };
            }
            
            toast.add({
              severity: 'success',
              summary: 'Succès',
              detail: 'Parcelle mise à jour',
              life: 3000
            });
          } else {
            // Création d'une nouvelle parcelle
            // En environnement réel, appel au service API
            // const response = await parcelService.createParcel(parcel.value);
            // const newParcel = response.data;
            
            // Simulation
            const newParcel = {
              ...parcel.value,
              id: 'P' + Math.floor(10000 + Math.random() * 90000),
              health: 90 // Valeur par défaut pour les nouvelles parcelles
            };
            
            parcels.value.push(newParcel);
            
            toast.add({
              severity: 'success',
              summary: 'Succès',
              detail: 'Parcelle créée',
              life: 3000
            });
          }
          
          hideDialog();
          loading.value = false;
        } catch (error) {
          console.error('Erreur lors de la sauvegarde de la parcelle:', error);
          toast.add({
            severity: 'error',
            summary: 'Erreur',
            detail: 'Impossible de sauvegarder la parcelle',
            life: 3000
          });
          loading.value = false;
        }
      }
    };
    
    // Confirmer la suppression d'une parcelle
    const confirmDeleteParcel = (data) => {
      parcel.value = data;
      deleteDialogVisible.value = true;
    };
    
    // Supprimer la parcelle
    const deleteParcel = async () => {
      try {
        loading.value = true;
        
        // En environnement réel, appel au service API
        // await parcelService.deleteParcel(parcel.value.id);
        
        // Simulation
        parcels.value = parcels.value.filter(p => p.id !== parcel.value.id);
        
        deleteDialogVisible.value = false;
        toast.add({
          severity: 'success',
          summary: 'Succès',
          detail: 'Parcelle supprimée',
          life: 3000
        });
        
        loading.value = false;
      } catch (error) {
        console.error('Erreur lors de la suppression de la parcelle:', error);
        toast.add({
          severity: 'error',
          summary: 'Erreur',
          detail: 'Impossible de supprimer la parcelle',
          life: 3000
        });
        loading.value = false;
      }
    };
    
    // Visualiser une parcelle
    const viewParcel = (data) => {
      router.push(`/parcels/${data.id}`);
    };
    
    // Clic sur une ligne
    const onRowClick = (event) => {
      router.push(`/parcels/${event.data.id}`);
    };
    
    // Afficher le dialogue des filtres
    const showFiltersDialog = () => {
      filtersDialogVisible.value = true;
    };
    
    // Appliquer les filtres
    const applyFilters = () => {
      filtersDialogVisible.value = false;
      
      // Notification de filtres appliqués
      if (activeFilters.forestTypes.length > 0 || activeFilters.minHealth > 0 || activeFilters.minArea || activeFilters.maxArea) {
        toast.add({
          severity: 'info',
          summary: 'Filtres appliqués',
          detail: `${filteredParcels.value.length} parcelles correspondent aux critères`,
          life: 3000
        });
      }
    };
    
    // Réinitialiser les filtres
    const resetFilters = () => {
      activeFilters.forestTypes = [];
      activeFilters.minHealth = 0;
      activeFilters.minArea = null;
      activeFilters.maxArea = null;
      
      toast.add({
        severity: 'info',
        summary: 'Filtres réinitialisés',
        detail: 'Tous les filtres ont été supprimés',
        life: 3000
      });
    };
    
    // Chargement initial des données
    onMounted(() => {
      fetchParcels();
    });
    
    return {
      loading,
      parcels,
      selectedParcels,
      parcel,
      parcelDialogVisible,
      deleteDialogVisible,
      filtersDialogVisible,
      submitted,
      searchQuery,
      forestTypes,
      filters,
      activeFilters,
      filteredParcels,
      formatNumber,
      getHealthColor,
      showNewParcelDialog,
      editParcel,
      hideDialog,
      saveParcel,
      confirmDeleteParcel,
      deleteParcel,
      viewParcel,
      onRowClick,
      showFiltersDialog,
      applyFilters,
      resetFilters
    };
  }
};
</script>

<style lang="scss" scoped>
.parcels-list {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
    
    h1 {
      margin: 0;
      font-size: 1.75rem;
      font-weight: 600;
      color: var(--text-color);
    }
  }
  
  .forest-type-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 1rem;
    font-size: 0.875rem;
    font-weight: 600;
    
    &.type-conifères {
      background-color: rgba(34, 197, 94, 0.2);
      color: #16A34A;
    }
    
    &.type-feuillus {
      background-color: rgba(59, 130, 246, 0.2);
      color: #2563EB;
    }
    
    &.type-mixte {
      background-color: rgba(139, 92, 246, 0.2);
      color: #7C3AED;
    }
    
    &.type-taillis {
      background-color: rgba(245, 158, 11, 0.2);
      color: #D97706;
    }
    
    &.type-plantation {
      background-color: rgba(16, 185, 129, 0.2);
      color: #059669;
    }
  }
  
  .health-indicator {
    display: flex;
    align-items: center;
    
    .health-bar {
      width: 60px;
      height: 8px;
      background-color: #E5E7EB;
      border-radius: 4px;
      margin-right: 0.5rem;
      
      .health-value {
        height: 100%;
        border-radius: 4px;
      }
    }
  }
  
  .action-buttons {
    display: flex;
    justify-content: flex-end;
    gap: 0.5rem;
  }
  
  .confirmation-content {
    display: flex;
    align-items: center;
  }
}
</style>
