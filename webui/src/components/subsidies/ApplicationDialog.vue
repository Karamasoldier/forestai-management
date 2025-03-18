<template>
  <Dialog 
    :visible="visible" 
    header="Déposer un dossier de subvention" 
    :modal="true" 
    :closable="true"
    :style="{ width: '650px' }"
    @update:visible="$emit('update:visible', $event)"
  >
    <div class="p-3">
      <div class="mb-4">
        <h3 class="font-medium text-lg mb-2">{{ subsidyName }}</h3>
        <p class="text-gray-600 mb-3">{{ subsidyProvider }}</p>
        
        <div class="bg-blue-50 border border-blue-200 rounded p-3 mb-4">
          <h4 class="font-medium mb-1">Montant estimé</h4>
          <div class="text-2xl font-bold text-blue-700 mb-1">
            {{ estimatedAmount }}
          </div>
          <div class="text-sm text-gray-600">
            {{ amountDescription }}
          </div>
        </div>
      </div>
      
      <h4 class="font-medium mb-2">Sélectionner les parcelles</h4>
      <MultiSelect 
        v-model="selectedParcels"
        :options="parcelOptions"
        optionLabel="name"
        placeholder="Sélectionner les parcelles"
        class="w-full mb-4"
        display="chip"
      />
      
      <div class="bg-yellow-50 border border-yellow-200 rounded p-3 mb-4">
        <h4 class="font-medium flex items-center">
          <i class="pi pi-info-circle mr-2 text-yellow-600"></i>
          Documents requis
        </h4>
        <ul class="pl-6 mt-2 space-y-1 list-disc text-sm">
          <li v-for="(doc, index) in requiredDocuments" :key="index">
            {{ doc }}
          </li>
        </ul>
      </div>
      
      <div class="mb-4">
        <h4 class="font-medium mb-2">Remarques supplémentaires</h4>
        <Textarea v-model="notes" rows="3" class="w-full" placeholder="Ajoutez des informations complémentaires pour le dossier..." />
      </div>
    </div>
    
    <template #footer>
      <Button label="Annuler" icon="pi pi-times" class="p-button-text" @click="closeDialog" />
      <Button 
        label="Générer le dossier" 
        icon="pi pi-file" 
        class="p-button-primary" 
        @click="generateApplication"
        :disabled="!selectedParcels.length"
      />
    </template>
  </Dialog>
</template>

<script>
import { defineComponent, ref, watch, computed } from 'vue';
import { useToast } from 'primevue/usetoast';

export default defineComponent({
  name: 'ApplicationDialog',
  props: {
    visible: {
      type: Boolean,
      required: true
    },
    subsidyId: {
      type: [String, Number],
      required: true
    },
    subsidyName: {
      type: String,
      required: true
    },
    subsidyProvider: {
      type: String,
      required: true
    },
    amountType: {
      type: String,
      required: true
    },
    amount: {
      type: Number,
      default: 0
    },
    minAmount: {
      type: Number,
      default: null
    },
    maxAmount: {
      type: Number,
      default: null
    },
    amountDescription: {
      type: String,
      default: ''
    },
    requiredDocuments: {
      type: Array,
      default: () => []
    },
    parcelOptions: {
      type: Array,
      default: () => []
    }
  },
  emits: ['update:visible', 'application-submitted'],
  setup(props, { emit }) {
    const toast = useToast();
    
    const selectedParcels = ref([]);
    const notes = ref('');
    
    // Reset state when dialog becomes visible
    watch(() => props.visible, (newVisible) => {
      if (newVisible) {
        selectedParcels.value = [];
        notes.value = '';
      }
    });
    
    const closeDialog = () => {
      emit('update:visible', false);
    };
    
    const generateApplication = async () => {
      if (selectedParcels.value.length === 0) {
        return;
      }
      
      try {
        toast.add({
          severity: 'info',
          summary: 'Génération en cours',
          detail: 'Préparation de votre dossier de demande de subvention...',
          life: 3000
        });
        
        // Simulate API call with a timeout
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Simulate successful submission
        const result = {
          applicationId: Math.floor(Math.random() * 1000000),
          submissionDate: new Date().toISOString(),
          fileUrl: '#',
          parcels: selectedParcels.value.map(p => p.id),
          status: 'pending'
        };
        
        emit('application-submitted', result);
        
        toast.add({
          severity: 'success',
          summary: 'Dossier généré',
          detail: 'Votre dossier de demande a été généré avec succès',
          life: 3000
        });
        
        closeDialog();
      } catch (error) {
        console.error('Erreur lors de la génération du dossier:', error);
        toast.add({
          severity: 'error',
          summary: 'Erreur',
          detail: 'Une erreur est survenue lors de la génération du dossier',
          life: 3000
        });
      }
    };
    
    const estimatedAmount = computed(() => {
      if (props.amountType === 'fixed') {
        return formatCurrency(props.amount);
      } else if (props.amountType === 'percentage') {
        // Estimation basée sur la surface moyenne des parcelles sélectionnées
        // (Dans une vraie application, ce calcul serait plus complexe)
        return `${props.amount}% (estimation à venir)`;
      } else if (props.amountType === 'range') {
        return `${formatCurrency(props.minAmount)} - ${formatCurrency(props.maxAmount)}`;
      }
      
      return 'À déterminer';
    });
    
    const formatCurrency = (value) => {
      if (!value && value !== 0) return '';
      return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(value);
    };
    
    return {
      selectedParcels,
      notes,
      closeDialog,
      generateApplication,
      estimatedAmount
    };
  }
});
</script>
