<template>
  <div class="p-4 bg-white rounded-lg shadow-sm">
    <h2 class="text-xl font-semibold mb-3">Présentation</h2>
    <div class="text-gray-700 mb-4" v-html="description"></div>
    
    <Divider />
    
    <!-- Objectifs -->
    <h3 class="text-lg font-medium mb-2">Objectifs</h3>
    <ul class="list-disc pl-5 mb-4 space-y-1">
      <li v-for="(objective, index) in objectives" :key="index">
        {{ objective }}
      </li>
    </ul>
    
    <!-- Actions éligibles -->
    <h3 class="text-lg font-medium mb-2">Actions éligibles</h3>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
      <div 
        v-for="(action, index) in eligibleActions" 
        :key="index"
        class="flex items-start p-3 bg-blue-50 rounded-lg"
      >
        <i class="pi pi-check-circle text-blue-500 mr-2 mt-1"></i>
        <div>
          <div class="font-medium">{{ action.title }}</div>
          <div class="text-sm text-gray-600">{{ action.description }}</div>
        </div>
      </div>
    </div>
    
    <!-- Conditions d'éligibilité -->
    <h3 class="text-lg font-medium mb-2">Conditions d'éligibilité</h3>
    <ul class="list-disc pl-5 mb-4 space-y-1">
      <li v-for="(condition, index) in eligibilityConditions" :key="index">
        {{ condition }}
      </li>
    </ul>
  </div>
</template>

<script>
export default {
  name: 'SubsidyPresentation',
  props: {
    description: { type: String, required: true },
    objectives: { type: Array, default: () => [] },
    eligibleActions: { type: Array, default: () => [] },
    eligibilityConditions: { type: Array, default: () => [] }
  }
}
</script>
