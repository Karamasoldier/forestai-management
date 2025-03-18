<template>
  <div class="card mb-4">
    <div class="card-header">
      <h5 class="mb-0">Actions</h5>
    </div>
    <div class="card-body">
      <div class="d-grid gap-2">
        <button @click="$emit('check-eligibility')" class="btn btn-primary">
          <i class="bi bi-check-circle me-2"></i> Vérifier l'éligibilité
        </button>
        <button @click="$emit('generate-application')" class="btn btn-success">
          <i class="bi bi-file-earmark-text me-2"></i> Générer une demande
        </button>
        <button @click="$emit('download-information')" class="btn btn-outline-secondary">
          <i class="bi bi-download me-2"></i> Télécharger la fiche
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SubsidyActions',
  emits: ['check-eligibility', 'generate-application', 'download-information']
}
</script>
