<template>
  <Card>
    <template #title>
      <div class="flex align-items-center">
        <i class="pi pi-info-circle mr-2"></i>
        <span>Informations générales</span>
      </div>
    </template>
    <template #content>
      <div v-if="loading" class="flex justify-content-center">
        <i class="pi pi-spin pi-spinner" style="font-size: 2rem"></i>
      </div>
      <div v-else>
        <div class="grid">
          <div class="col-12 md:col-6">
            <div class="info-group">
              <label>Commune</label>
              <div class="info-value">{{ parcel.commune }}</div>
            </div>
          </div>
          
          <div class="col-12 md:col-3">
            <div class="info-group">
              <label>Section</label>
              <div class="info-value">{{ parcel.section }}</div>
            </div>
          </div>
          
          <div class="col-12 md:col-3">
            <div class="info-group">
              <label>Numéro</label>
              <div class="info-value">{{ parcel.numero }}</div>
            </div>
          </div>
          
          <div class="col-12 md:col-6">
            <div class="info-group">
              <label>Adresse</label>
              <div class="info-value">{{ parcel.address || 'Non spécifiée' }}</div>
            </div>
          </div>
          
          <div class="col-12 md:col-6">
            <div class="info-group">
              <label>Surface</label>
              <div class="info-value">{{ formatNumber(parcel.area) }} ha</div>
            </div>
          </div>
          
          <div class="col-12">
            <div class="info-group">
              <label>Description</label>
              <div class="info-value description">{{ parcel.description || 'Aucune description disponible' }}</div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </Card>
</template>

<script>
export default {
  name: 'ParcelGeneralInfo',
  props: {
    parcel: {
      type: Object,
      required: true
    },
    loading: {
      type: Boolean,
      default: false
    },
    formatNumber: {
      type: Function,
      required: true
    }
  }
};
</script>

<style lang="scss" scoped>
.info-group {
  margin-bottom: 1rem;
  
  label {
    display: block;
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--text-color-secondary);
    margin-bottom: 0.25rem;
  }
  
  .info-value {
    font-size: 1rem;
    color: var(--text-color);
    
    &.description {
      white-space: pre-line;
      line-height: 1.5;
    }
  }
}
</style>
