<template>
  <div class="card mb-4">
    <div class="card-header">
      <h5 class="mb-0">Détails de la subvention</h5>
    </div>
    <div class="card-body">
      <div class="mb-4">
        <h6>Conditions d'éligibilité</h6>
        <ul>
          <li v-for="(condition, index) in subsidy.eligibility_conditions" :key="index">
            {{ condition }}
          </li>
        </ul>
      </div>
      
      <div class="mb-4">
        <h6>Dépenses éligibles</h6>
        <ul>
          <li v-for="(expense, index) in subsidy.eligible_expenses" :key="index">
            {{ expense }}
          </li>
        </ul>
      </div>
      
      <div v-if="subsidy.non_eligible_expenses && subsidy.non_eligible_expenses.length > 0" class="mb-4">
        <h6>Dépenses non éligibles</h6>
        <ul>
          <li v-for="(expense, index) in subsidy.non_eligible_expenses" :key="index">
            {{ expense }}
          </li>
        </ul>
      </div>
      
      <div v-if="subsidy.additional_info" class="mb-4">
        <h6>Informations complémentaires</h6>
        <p>{{ subsidy.additional_info }}</p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SubsidyDetails',
  props: {
    subsidy: {
      type: Object,
      required: true
    }
  }
}
</script>
