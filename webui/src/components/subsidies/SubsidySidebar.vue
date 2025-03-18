<template>
  <div class="space-y-4">
    <!-- Informations clés -->
    <div class="p-4 bg-white rounded-lg shadow-sm">
      <h2 class="text-xl font-semibold mb-3">Informations clés</h2>
      
      <div class="space-y-3">
        <div>
          <div class="text-sm text-gray-500">Zone géographique</div>
          <div class="font-medium">{{ region }}</div>
          <div v-if="department" class="text-sm">{{ department }}</div>
        </div>
        
        <Divider />
        
        <div>
          <div class="text-sm text-gray-500">Organisme financeur</div>
          <div class="font-medium">{{ provider }}</div>
          <div v-if="providerType" class="text-sm">{{ providerType }}</div>
        </div>
        
        <Divider />
        
        <div>
          <div class="text-sm text-gray-500">Personne à contacter</div>
          <div v-if="contactPerson" class="font-medium">{{ contactPerson }}</div>
          <div v-else class="font-medium">Service des aides forestières</div>
          <div v-if="contactEmail" class="text-sm">
            <i class="pi pi-envelope text-gray-400 mr-1"></i>
            <a :href="`mailto:${contactEmail}`" class="text-blue-600 hover:underline">
              {{ contactEmail }}
            </a>
          </div>
          <div v-if="contactPhone" class="text-sm">
            <i class="pi pi-phone text-gray-400 mr-1"></i>
            <a :href="`tel:${contactPhone}`" class="text-blue-600 hover:underline">
              {{ contactPhone }}
            </a>
          </div>
        </div>
        
        <Divider />
        
        <div>
          <div class="text-sm text-gray-500">Mise à jour</div>
          <div class="font-medium">{{ formatDate(updatedAt) }}</div>
        </div>
      </div>
    </div>
    
    <!-- Compatibilité avec vos parcelles -->
    <div class="p-4 bg-white rounded-lg shadow-sm">
      <h2 class="text-xl font-semibold mb-3">Compatibilité avec vos parcelles</h2>
      <div class="mb-3">
        <Rating :modelValue="compatibilityScore" readonly :cancel="false" />
        <span class="ml-2 font-medium">{{ compatibilityScore }}/5</span>
      </div>
      
      <div class="mb-4">
        <Tag 
          v-if="compatibilityScore >= 4" 
          value="Fortement recommandée" 
          severity="success" 
          class="text-sm"
        />
        <Tag 
          v-else-if="compatibilityScore >= 3" 
          value="Recommandée" 
          severity="info" 
          class="text-sm"
        />
        <Tag 
          v-else-if="compatibilityScore >= 2" 
          value="Partiellement compatible" 
          severity="warning" 
          class="text-sm"
        />
      </div>
      
      <h3 class="text-lg font-medium mb-2">Parcelles compatibles</h3>
      <div v-if="compatibleParcels && compatibleParcels.length > 0" class="mb-4">
        <DataTable :value="compatibleParcels" stripedRows class="text-sm">
          <Column field="reference" header="Référence"></Column>
          <Column field="surface" header="Surface (ha)"></Column>
          <Column field="compatibility" header="Compatibilité" style="width: 140px">
            <template #body="{ data }">
              <Rating :modelValue="data.compatibility" readonly :cancel="false" :stars="3" />
            </template>
          </Column>
        </DataTable>
      </div>
      <div v-else class="p-3 bg-gray-50 rounded-lg mb-4 text-center">
        <i class="pi pi-info-circle text-gray-400 mb-2 text-xl"></i>
        <div>Aucune parcelle analysée</div>
        <div class="text-sm text-gray-500">Cliquez sur "Analyser l'éligibilité" pour évaluer vos parcelles.</div>
      </div>
      
      <Button 
        label="Analyser toutes les parcelles" 
        icon="pi pi-check-circle" 
        class="p-button-outlined w-full" 
        @click="$emit('analyze')"
      />
    </div>
    
    <!-- Aides similaires -->
    <div class="p-4 bg-white rounded-lg shadow-sm">
      <h2 class="text-xl font-semibold mb-3">Aides similaires</h2>
      
      <div v-if="similarSubsidies && similarSubsidies.length > 0" class="space-y-3">
        <div 
          v-for="similar in similarSubsidies" 
          :key="similar.id"
          class="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer"
          @click="goToSubsidyDetail(similar.id)"
        >
          <div class="font-medium text-blue-700">{{ similar.name }}</div>
          <div class="text-sm text-gray-600">{{ similar.provider }}</div>
          <div class="flex justify-between items-center mt-1">
            <div>
              <Tag 
                :value="similar.status" 
                :severity="getStatusSeverity(similar.status)" 
                class="text-xs"
              />
            </div>
            <div v-if="similar.amountType === 'fixed'" class="text-sm font-medium">
              {{ formatCurrency(similar.amount) }}
            </div>
            <div v-else-if="similar.amountType === 'percentage'" class="text-sm font-medium">
              {{ similar.amount }}%
            </div>
          </div>
        </div>
      </div>
      <div v-else class="p-3 bg-gray-50 rounded-lg text-center">
        <i class="pi pi-info-circle text-gray-400 mb-2 text-xl"></i>
        <div>Aucune aide similaire trouvée</div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SubsidySidebar',
  props: {
    region: { type: String, required: true },
    department: { type: String, default: null },
    provider: { type: String, required: true },
    providerType: { type: String, default: null },
    contactPerson: { type: String, default: null },
    contactEmail: { type: String, default: null },
    contactPhone: { type: String, default: null },
    updatedAt: { type: String, default: null },
    compatibilityScore: { type: Number, default: 0 },
    compatibleParcels: { type: Array, default: () => [] },
    similarSubsidies: { type: Array, default: () => [] }
  },
  emits: ['analyze'],
  methods: {
    formatDate(dateString) {
      if (!dateString) return '';
      const date = new Date(dateString);
      return new Intl.DateTimeFormat('fr-FR').format(date);
    },
    
    formatCurrency(value) {
      if (!value && value !== 0) return '';
      return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(value);
    },
    
    getStatusSeverity(status) {
      switch (status) {
        case 'Ouvert': return 'success';
        case 'Bientôt clôturé': return 'warning';
        case 'Prochainement': return 'info';
        case 'Permanent': return 'info';
        default: return null;
      }
    },
    
    goToSubsidyDetail(id) {
      this.$router.push({ name: 'SubsidyDetail', params: { id } });
    }
  }
}
</script>

<style scoped>
:deep(.p-rating .p-rating-item.p-rating-item-active .p-rating-icon) {
  color: #F59E0B;
}
</style>
