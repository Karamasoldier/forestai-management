<template>
  <Dialog 
    :visible="visible" 
    header="Analyse d'éligibilité" 
    :modal="true" 
    :closable="true"
    :style="{ width: '700px' }"
    @update:visible="$emit('update:visible', $event)"
  >
    <div class="p-3">
      <div class="mb-4" v-if="!analysisLoading && !analysisComplete">
        <h3 class="font-medium text-lg mb-3">Sélectionner les parcelles à analyser</h3>
        <div class="mb-3">
          <MultiSelect 
            v-model="selectedParcels"
            :options="parcelOptions"
            optionLabel="name"
            placeholder="Sélectionner les parcelles"
            class="w-full"
            display="chip"
          />
        </div>
        <div class="flex justify-end">
          <Button 
            label="Sélectionner toutes les parcelles" 
            icon="pi pi-check-square" 
            class="p-button-text p-button-sm" 
            @click="selectAllParcels"
          />
        </div>
      </div>
      
      <div v-if="analysisLoading" class="text-center p-5">
        <ProgressSpinner style="width:50px;height:50px" strokeWidth="4" />
        <div class="mt-3 font-medium">Analyse en cours...</div>
        <div class="text-sm text-gray-500">Veuillez patienter, cette opération peut prendre quelques instants.</div>
      </div>
      
      <div v-else-if="analysisComplete" class="space-y-4">
        <div class="bg-blue-50 p-3 rounded-lg mb-3">
          <div class="font-medium text-blue-800 mb-1">Résumé de l'analyse</div>
          <div class="text-sm">{{ analysisResults.summary }}</div>
        </div>
        
        <DataTable :value="analysisResults.parcels" stripedRows showGridlines class="mb-4">
          <Column field="reference" header="Référence" style="width: 120px"></Column>
          <Column field="location" header="Localisation" style="width: 150px"></Column>
          <Column field="surface" header="Surface (ha)" style="width: 100px"></Column>
          <Column field="eligibilityScore" header="Éligibilité" style="width: 140px">
            <template #body="{ data }">
              <div class="flex items-center">
                <Rating :modelValue="data.eligibilityScore" readonly :cancel="false" :stars="3" />
                <span class="ml-2">{{ data.eligibilityScore }}/3</span>
              </div>
            </template>
          </Column>
          <Column field="eligibilityLabel" header="Statut">
            <template #body="{ data }">
              <Tag 
                :value="data.eligibilityLabel" 
                :severity="getEligibilitySeverity(data.eligibilityScore)" 
              />
            </template>
          </Column>
        </DataTable>
        
        <h3 class="font-medium text-lg mb-2">Critères d'éligibilité</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
          <div 
            v-for="(criterion, index) in analysisResults.criteria" 
            :key="index"
            class="p-3 rounded-lg"
            :class="criterion.satisfied ? 'bg-green-50' : 'bg-red-50'"
          >
            <div class="flex items-start">
              <i 
                class="pi mr-2 mt-1" 
                :class="criterion.satisfied ? 'pi-check-circle text-green-500' : 'pi-times-circle text-red-500'"
              ></i>
              <div>
                <div class="font-medium">{{ criterion.name }}</div>
                <div class="text-sm" :class="criterion.satisfied ? 'text-gray-600' : 'text-red-600'">
                  {{ criterion.description }}
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div v-if="analysisResults.recommendations && analysisResults.recommendations.length > 0">
          <h3 class="font-medium text-lg mb-2">Recommandations</h3>
          <ul class="list-disc pl-5 space-y-1 mb-3">
            <li v-for="(rec, index) in analysisResults.recommendations" :key="index" class="text-sm">
              {{ rec }}
            </li>
          </ul>
        </div>
      </div>
    </div>
    
    <template #footer>
      <Button 
        v-if="!analysisLoading && !analysisComplete" 
        label="Annuler" 
        icon="pi pi-times" 
        class="p-button-text" 
        @click="closeDialog" 
      />
      <Button 
        v-if="!analysisLoading && !analysisComplete" 
        label="Lancer l'analyse" 
        icon="pi pi-check-circle" 
        class="p-button-primary" 
        @click="runAnalysis"
        :disabled="selectedParcels.length === 0"
      />
      <Button 
        v-if="analysisComplete" 
        label="Fermer" 
        icon="pi pi-times" 
        class="p-button-text" 
        @click="closeDialog" 
      />
      <Button 
        v-if="analysisComplete" 
        label="Générer un rapport" 
        icon="pi pi-file-pdf" 
        class="p-button-primary" 
        @click="generateReport"
      />
    </template>
  </Dialog>
</template>

<script>
import { defineComponent, ref, watch } from 'vue';
import { useToast } from 'primevue/usetoast';

export default defineComponent({
  name: 'EligibilityAnalysisDialog',
  props: {
    visible: {
      type: Boolean,
      required: true
    },
    subsidyId: {
      type: [String, Number],
      required: true
    },
    parcelOptions: {
      type: Array,
      default: () => []
    }
  },
  emits: ['update:visible', 'analysis-complete'],
  setup(props, { emit }) {
    const toast = useToast();
    
    const selectedParcels = ref([]);
    const analysisLoading = ref(false);
    const analysisComplete = ref(false);
    const analysisResults = ref({
      summary: '',
      parcels: [],
      criteria: [],
      recommendations: []
    });
    
    // Reset state when dialog becomes visible
    watch(() => props.visible, (newVisible) => {
      if (newVisible) {
        selectedParcels.value = [];
        analysisComplete.value = false;
        analysisResults.value = {
          summary: '',
          parcels: [],
          criteria: [],
          recommendations: []
        };
      }
    });
    
    const selectAllParcels = () => {
      selectedParcels.value = [...props.parcelOptions];
    };
    
    const closeDialog = () => {
      emit('update:visible', false);
    };
    
    const runAnalysis = async () => {
      if (selectedParcels.value.length === 0) {
        return;
      }
      
      analysisLoading.value = true;
      
      try {
        // Simulating API call with a timeout
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Simulated analysis results
        analysisResults.value = {
          summary: `L'analyse a identifié ${selectedParcels.value.length} parcelles dont ${Math.ceil(selectedParcels.value.length * 0.7)} sont éligibles à cette subvention. Environ 70% de vos parcelles sont compatibles avec les critères de cette aide.`,
          parcels: selectedParcels.value.map(parcel => {
            const score = Math.floor(Math.random() * 3) + 1; // Random score between 1-3
            let label = '';
            
            if (score === 3) label = 'Totalement éligible';
            else if (score === 2) label = 'Partiellement éligible';
            else label = 'Peu éligible';
            
            return {
              id: parcel.id,
              reference: parcel.name.split(' - ')[0],
              location: parcel.name.split(' - ')[1],
              surface: (Math.random() * 10 + 1).toFixed(2),
              eligibilityScore: score,
              eligibilityLabel: label
            };
          }),
          criteria: [
            {
              name: 'Surface minimale',
              description: 'Surface supérieure à 1 hectare d\'un seul tenant',
              satisfied: true
            },
            {
              name: 'Zonage géographique',
              description: 'Parcelles situées dans une zone éligible',
              satisfied: true
            },
            {
              name: 'Type de peuplement',
              description: 'Le type de peuplement est compatible avec l\'aide',
              satisfied: false
            },
            {
              name: 'Conditions écologiques',
              description: 'Les conditions écologiques correspondent aux critères',
              satisfied: true
            }
          ],
          recommendations: [
            'Privilégiez les essences adaptées au changement climatique pour augmenter l\'éligibilité',
            'Regroupez vos demandes en un seul dossier pour optimiser les chances d\'obtention',
            'Documentez précisément l\'état actuel des peuplements pour justifier le besoin d\'intervention'
          ]
        };
        
        analysisComplete.value = true;
        emit('analysis-complete', analysisResults.value);
        
      } catch (error) {
        console.error('Erreur lors de l\'analyse:', error);
        toast.add({
          severity: 'error',
          summary: 'Erreur',
          detail: 'Une erreur est survenue lors de l\'analyse d\'éligibilité',
          life: 3000
        });
      } finally {
        analysisLoading.value = false;
      }
    };
    
    const generateReport = () => {
      toast.add({
        severity: 'info',
        summary: 'Génération du rapport',
        detail: 'Le rapport d\'analyse d\'éligibilité est en cours de génération...',
        life: 3000
      });
      
      // Simulate report generation
      setTimeout(() => {
        toast.add({
          severity: 'success',
          summary: 'Rapport généré',
          detail: 'Le rapport d\'analyse d\'éligibilité a été téléchargé avec succès',
          life: 3000
        });
      }, 2000);
    };
    
    const getEligibilitySeverity = (score) => {
      if (score === 3) return 'success';
      if (score === 2) return 'info';
      return 'warning';
    };
    
    return {
      selectedParcels,
      analysisLoading,
      analysisComplete,
      analysisResults,
      selectAllParcels,
      closeDialog,
      runAnalysis,
      generateReport,
      getEligibilitySeverity
    };
  }
});
</script>

<style scoped>
:deep(.p-rating .p-rating-item.p-rating-item-active .p-rating-icon) {
  color: #F59E0B;
}
</style>
