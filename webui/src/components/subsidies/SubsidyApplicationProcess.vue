<template>
  <div class="p-4 bg-white rounded-lg shadow-sm">
    <h2 class="text-xl font-semibold mb-3">Procédure de dépôt</h2>
    
    <h3 class="text-lg font-medium mb-2">Documents requis</h3>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
      <div 
        v-for="(doc, index) in requiredDocuments" 
        :key="index"
        class="flex items-start p-3 bg-gray-50 rounded-lg"
      >
        <i class="pi pi-file text-gray-500 mr-2 mt-1"></i>
        <div>{{ doc }}</div>
      </div>
    </div>
    
    <h3 class="text-lg font-medium mb-2">Étapes du dépôt</h3>
    <ol class="space-y-4 mb-4">
      <li v-for="(step, index) in applicationSteps" :key="index" class="flex">
        <div class="flex-shrink-0 bg-blue-100 text-blue-700 rounded-full w-8 h-8 flex items-center justify-center mr-3">
          {{ index + 1 }}
        </div>
        <div class="pt-1">
          <div class="font-medium">{{ step.title }}</div>
          <div class="text-gray-600 text-sm">{{ step.description }}</div>
        </div>
      </li>
    </ol>
    
    <div v-if="applicationUrl" class="bg-blue-50 p-3 rounded-lg mb-4">
      <h3 class="text-lg font-medium mb-2">Plateforme de dépôt</h3>
      <div class="flex items-center">
        <i class="pi pi-external-link text-blue-500 mr-2"></i>
        <a 
          :href="applicationUrl" 
          target="_blank" 
          rel="noopener noreferrer"
          class="text-blue-600 hover:underline"
        >
          {{ applicationUrl }}
        </a>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SubsidyApplicationProcess',
  props: {
    requiredDocuments: {
      type: Array,
      default: () => []
    },
    applicationSteps: {
      type: Array,
      default: () => []
    },
    applicationUrl: {
      type: String,
      default: null
    }
  }
}
</script>
