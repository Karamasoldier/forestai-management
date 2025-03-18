<template>
  <div class="p-4 bg-white rounded-lg shadow-sm">
    <h2 class="text-xl font-semibold mb-3">Détails financiers</h2>
    
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
      <div class="p-3 bg-green-50 rounded-lg">
        <div class="text-sm text-gray-600 mb-1">Montant</div>
        <div class="text-lg font-bold" v-if="amountType === 'fixed'">
          {{ formatCurrency(amount) }}
        </div>
        <div class="text-lg font-bold" v-else-if="amountType === 'percentage'">
          {{ amount }}% du coût total
        </div>
        <div class="text-lg font-bold" v-else-if="amountType === 'range'">
          {{ formatCurrency(minAmount) }} - {{ formatCurrency(maxAmount) }}
        </div>
        <div class="text-sm text-gray-500 mt-1">{{ amountDescription }}</div>
      </div>
      
      <div class="p-3 bg-blue-50 rounded-lg">
        <div class="text-sm text-gray-600 mb-1">Date limite</div>
        <div class="text-lg font-bold" v-if="deadline">
          {{ formatDate(deadline) }}
          <span v-if="isDeadlineSoon(deadline)" class="text-sm text-red-500 ml-2">
            (Échéance proche)
          </span>
        </div>
        <div class="text-lg font-bold text-green-600" v-else>
          Aide permanente
        </div>
        <div class="text-sm text-gray-500 mt-1" v-if="deadlineDescription">
          {{ deadlineDescription }}
        </div>
      </div>
    </div>
    
    <!-- Modalités de paiement -->
    <h3 class="text-lg font-medium mb-2">Modalités de paiement</h3>
    <div class="mb-4">
      <Steps :model="paymentSteps" />
    </div>
    
    <!-- Dépenses éligibles -->
    <h3 class="text-lg font-medium mb-2">Dépenses éligibles</h3>
    <div class="mb-4">
      <DataTable :value="eligibleExpenses" stripedRows showGridlines>
        <Column field="category" header="Catégorie" style="width: 25%"></Column>
        <Column field="description" header="Description"></Column>
        <Column field="limit" header="Limite" style="width: 20%">
          <template #body="{ data }">
            <div v-if="data.limit" class="font-medium">{{ data.limit }}</div>
            <div v-else class="text-gray-500">Pas de limite spécifique</div>
          </template>
        </Column>
      </DataTable>
    </div>
    
    <!-- Simulateur financier -->
    <h3 class="text-lg font-medium mb-2">Simulateur de financement</h3>
    <div class="p-4 border border-gray-200 rounded-lg">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Surface concernée (ha)</label>
          <InputNumber v-model="simulationArea" class="w-full" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Coût total estimé (€)</label>
          <InputNumber v-model="simulationTotalCost" mode="currency" currency="EUR" locale="fr-FR" class="w-full" />
        </div>
      </div>
      
      <Button 
        label="Calculer" 
        icon="pi pi-calculator" 
        class="mb-4" 
        @click="calculateSimulation"
      />
      
      <div v-if="showSimulationResult" class="p-3 bg-blue-50 rounded-lg">
        <div class="text-lg font-medium mb-2">Résultat de la simulation</div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <div class="text-sm text-gray-600">Subvention estimée</div>
            <div class="text-xl font-bold text-blue-700">{{ formatCurrency(calculatedSubsidyAmount) }}</div>
          </div>
          <div>
            <div class="text-sm text-gray-600">Reste à charge</div>
            <div class="text-xl font-bold text-gray-700">{{ formatCurrency(calculatedRemainingCost) }}</div>
            <div class="text-sm text-gray-500">
              ({{ Math.round(calculatedRemainingPercentage) }}% du coût total)
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SubsidyFinancialDetails',
  props: {
    amountType: { type: String, required: true },
    amount: { type: Number, default: 0 },
    minAmount: { type: Number, default: null },
    maxAmount: { type: Number, default: null },
    amountDescription: { type: String, default: '' },
    deadline: { type: String, default: null },
    deadlineDescription: { type: String, default: '' },
    paymentSteps: { type: Array, default: () => [] },
    eligibleExpenses: { type: Array, default: () => [] }
  },
  data() {
    return {
      simulationArea: 1,
      simulationTotalCost: 10000,
      showSimulationResult: false,
      calculatedSubsidyAmount: 0,
      calculatedRemainingCost: 0,
      calculatedRemainingPercentage: 0
    };
  },
  methods: {
    formatCurrency(value) {
      if (!value && value !== 0) return '';
      return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(value);
    },
    
    formatDate(dateString) {
      if (!dateString) return '';
      const date = new Date(dateString);
      return new Intl.DateTimeFormat('fr-FR').format(date);
    },
    
    isDeadlineSoon(deadline) {
      if (!deadline) return false;
      
      const deadlineDate = new Date(deadline);
      const now = new Date();
      const diffDays = Math.ceil((deadlineDate - now) / (1000 * 60 * 60 * 24));
      
      return diffDays > 0 && diffDays < 30;
    },
    
    calculateSimulation() {
      let subsidyAmount = 0;
      
      if (this.amountType === 'fixed') {
        subsidyAmount = this.amount;
      } else if (this.amountType === 'percentage') {
        subsidyAmount = this.simulationTotalCost * (this.amount / 100);
      } else if (this.amountType === 'range') {
        // Simple approach: use middle of the range
        subsidyAmount = Math.min(
          this.maxAmount || Infinity,
          Math.max(this.minAmount || 0, this.simulationTotalCost * 0.5)
        );
      }
      
      const remainingCost = this.simulationTotalCost - subsidyAmount;
      const remainingPercentage = (remainingCost / this.simulationTotalCost) * 100;
      
      this.calculatedSubsidyAmount = subsidyAmount;
      this.calculatedRemainingCost = remainingCost;
      this.calculatedRemainingPercentage = remainingPercentage;
      this.showSimulationResult = true;
    }
  }
}
</script>
