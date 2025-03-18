<template>
  <div class="card">
    <div class="card-header">
      <h5 class="mb-0">Dates importantes</h5>
    </div>
    <div class="card-body">
      <ul class="list-group list-group-flush">
        <li class="list-group-item d-flex justify-content-between align-items-center">
          <span>Date de publication</span>
          <span class="badge bg-secondary">{{ subsidy.publication_date || 'Non spécifiée' }}</span>
        </li>
        <li class="list-group-item d-flex justify-content-between align-items-center">
          <span>Date limite de dépôt</span>
          <span class="badge bg-warning">{{ subsidy.deadline || 'Non spécifiée' }}</span>
        </li>
        <li class="list-group-item d-flex justify-content-between align-items-center">
          <span>Date de réponse</span>
          <span class="badge bg-info">{{ subsidy.response_date || 'Non spécifiée' }}</span>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SubsidyDates',
  props: {
    subsidy: {
      type: Object,
      required: true
    }
  }
}
</script>
