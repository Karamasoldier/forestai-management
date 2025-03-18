<template>
  <div class="mb-4 p-4 bg-white rounded-lg shadow-sm">
    <div class="flex flex-col md:flex-row justify-between items-start md:items-center">
      <div>
        <div class="flex items-center">
          <Button 
            icon="pi pi-arrow-left" 
            class="p-button-text p-button-sm mr-2" 
            @click="goBack" 
          />
          <Tag 
            :value="status" 
            :severity="getStatusSeverity(status)" 
            class="mr-2"
          />
          <h1 class="text-2xl font-bold text-gray-800">{{ name }}</h1>
        </div>
        <div class="text-gray-600 mt-1">
          {{ provider }} | {{ category }}
        </div>
      </div>
      <div class="mt-3 md:mt-0 flex flex-wrap gap-2">
        <Button 
          label="Analyser l'éligibilité" 
          icon="pi pi-check-circle" 
          class="p-button-outlined p-button-secondary" 
          @click="$emit('analyze')"
        />
        <Button 
          label="Déposer un dossier" 
          icon="pi pi-file" 
          class="p-button-primary" 
          @click="$emit('apply')"
        />
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SubsidyHeader',
  props: {
    name: { type: String, required: true },
    provider: { type: String, required: true },
    category: { type: String, required: true },
    status: { type: String, required: true }
  },
  emits: ['analyze', 'apply'],
  methods: {
    goBack() {
      this.$router.push('/subsidies');
    },
    getStatusSeverity(status) {
      switch (status) {
        case 'Ouvert': return 'success';
        case 'Bientôt clôturé': return 'warning';
        case 'Prochainement': return 'info';
        case 'Permanent': return 'info';
        default: return null;
      }
    }
  }
}
</script>
