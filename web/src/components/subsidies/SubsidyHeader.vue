<template>
  <div class="card mb-4">
    <div class="card-body">
      <div class="d-md-flex justify-content-between align-items-start">
        <div>
          <h1 class="h3 mb-2">{{ subsidy.title }}</h1>
          <div class="d-flex flex-wrap gap-2 mb-3">
            <span class="badge bg-primary">{{ subsidy.type }}</span>
            <span class="badge bg-secondary">{{ subsidy.region }}</span>
            <span class="badge bg-info">{{ subsidy.provider }}</span>
            <span v-if="subsidy.deadline" class="badge bg-warning">
              Date limite: {{ subsidy.deadline }}
            </span>
          </div>
          <p class="lead">{{ subsidy.description }}</p>
        </div>
        
        <div class="mt-3 mt-md-0">
          <div class="card">
            <div class="card-body">
              <h5 class="card-title">Montant de l'aide</h5>
              <p class="card-text" v-if="subsidy.amount_type === 'range'">
                Entre <strong>{{ subsidy.min_amount }} €</strong> et <strong>{{ subsidy.max_amount }} €</strong>
              </p>
              <p class="card-text" v-else-if="subsidy.amount_type === 'percentage'">
                <strong>{{ subsidy.percentage }}%</strong> des dépenses éligibles<br>
                (plafonné à <strong>{{ subsidy.max_amount }} €</strong>)
              </p>
              <p class="card-text" v-else>
                <strong>{{ subsidy.amount }} €</strong>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SubsidyHeader',
  props: {
    subsidy: {
      type: Object,
      required: true
    }
  }
}
</script>
