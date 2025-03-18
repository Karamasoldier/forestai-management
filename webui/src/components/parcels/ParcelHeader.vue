<template>
  <div class="page-header">
    <div class="header-content">
      <Button icon="pi pi-arrow-left" text rounded class="back-button" @click="$emit('back')" />
      <h1>{{ parcel.id || 'Détail de la parcelle' }}</h1>
      <span class="forest-type-badge" v-if="parcel.forestType" :class="'type-' + parcel.forestType.toLowerCase().replace(/\s+/g, '-')">
        {{ parcel.forestType }}
      </span>
    </div>
    <div class="header-actions">
      <Button label="Modifier" icon="pi pi-pencil" outlined class="mr-2" @click="$emit('edit')" />
      <Button label="Diagnostic" icon="pi pi-file-edit" class="mr-2" severity="info" @click="$emit('new-diagnostic')" />
      <Button label="Rapport" icon="pi pi-file-pdf" severity="success" @click="$emit('generate-report')" />
      <Button icon="pi pi-ellipsis-v" text rounded class="ml-2" @click="$emit('toggle-menu', $event)" aria-haspopup="true" aria-controls="context-menu" />
    </div>
  </div>
</template>

<script>
export default {
  name: 'ParcelHeader',
  props: {
    parcel: {
      type: Object,
      required: true
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  emits: ['back', 'edit', 'new-diagnostic', 'generate-report', 'toggle-menu']
};
</script>

<style lang="scss" scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  
  .header-content {
    display: flex;
    align-items: center;
    
    h1 {
      margin: 0 1rem;
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
}

@media screen and (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    
    .header-actions {
      margin-top: 1rem;
      width: 100%;
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
    }
  }
}
</style>
