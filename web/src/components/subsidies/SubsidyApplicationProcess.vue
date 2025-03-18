<template>
  <div class="card mb-4">
    <div class="card-header">
      <h5 class="mb-0">Procédure de demande</h5>
    </div>
    <div class="card-body">
      <ol>
        <li v-for="(step, index) in subsidy.application_steps" :key="index" class="mb-2">
          {{ step }}
        </li>
      </ol>
      
      <div v-if="subsidy.required_documents && subsidy.required_documents.length > 0" class="mt-4">
        <h6>Documents requis</h6>
        <ul>
          <li v-for="(doc, index) in subsidy.required_documents" :key="index">
            {{ doc }}
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SubsidyApplicationProcess',
  props: {
    subsidy: {
      type: Object,
      required: true
    }
  }
}
</script>
