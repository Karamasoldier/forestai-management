<template>
  <div class="card mb-4">
    <div class="card-header">
      <h5 class="mb-0">Organisme financeur</h5>
    </div>
    <div class="card-body">
      <p><strong>{{ subsidy.provider }}</strong></p>
      <p v-if="subsidy.provider_address">{{ subsidy.provider_address }}</p>
      <p v-if="subsidy.provider_contact">
        <i class="bi bi-envelope me-2"></i> {{ subsidy.provider_contact }}
      </p>
      <p v-if="subsidy.provider_website">
        <i class="bi bi-globe me-2"></i>
        <a :href="subsidy.provider_website" target="_blank" rel="noopener noreferrer">
          Site web
        </a>
      </p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SubsidyProvider',
  props: {
    subsidy: {
      type: Object,
      required: true
    }
  }
}
</script>
