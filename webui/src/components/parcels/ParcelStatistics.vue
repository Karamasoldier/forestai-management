<template>
  <div class="parcel-statistics-container p-4 border rounded-lg bg-white shadow-sm">
    <h3 class="text-xl font-semibold mb-4">Statistiques de la parcelle</h3>
    
    <!-- Performance générale -->
    <div class="mb-6">
      <h4 class="text-lg font-medium mb-2">Performance forestière</h4>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div 
          v-for="(stat, index) in performanceStats" 
          :key="index" 
          class="stat-card p-3 border rounded-lg"
          :class="getStatCardColorClass(stat.trend)"
        >
          <div class="text-sm text-gray-600">{{ stat.label }}</div>
          <div class="flex items-end justify-between">
            <div class="text-2xl font-bold">{{ stat.value }}</div>
            <div class="flex items-center text-sm" :class="getTrendTextColorClass(stat.trend)">
              <i class="pi mr-1" :class="getTrendIconClass(stat.trend)"></i>
              <span>{{ stat.trendValue }}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Graphique d'évolution -->
    <div class="mb-6">
      <h4 class="text-lg font-medium mb-2">Évolution sur 5 ans</h4>
      <div class="h-80">
        <Chart type="line" :data="chartData" :options="chartOptions" />
      </div>
    </div>
    
    <!-- Composition forestière -->
    <div class="mb-6">
      <h4 class="text-lg font-medium mb-2">Composition forestière</h4>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="h-64">
          <Chart type="pie" :data="pieData" :options="pieOptions" />
        </div>
        <div class="flex flex-col justify-center">
          <ul class="space-y-2">
            <li v-for="(species, index) in speciesComposition" :key="index" class="flex items-center">
              <div 
                class="w-4 h-4 rounded-full mr-2" 
                :style="{ backgroundColor: pieData.datasets[0].backgroundColor[index] }"
              ></div>
              <span class="text-sm">{{ species.name }}: <strong>{{ species.percentage }}%</strong></span>
            </li>
          </ul>
        </div>
      </div>
    </div>
    
    <!-- Indicateurs de santé -->
    <div>
      <h4 class="text-lg font-medium mb-2">Indicateurs de santé</h4>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div v-for="(indicator, index) in healthIndicators" :key="index" class="border rounded-lg p-3">
          <div class="flex justify-between mb-1">
            <span class="text-sm">{{ indicator.label }}</span>
            <span class="text-sm font-medium">{{ indicator.value }}/10</span>
          </div>
          <ProgressBar 
            :value="indicator.value * 10" 
            :class="getHealthIndicatorColorClass(indicator.value)"
          />
          <div class="text-xs text-gray-500 mt-1">{{ indicator.description }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent, ref, computed } from 'vue';
import { Chart } from 'primevue/chart';
import ProgressBar from 'primevue/progressbar';

export default defineComponent({
  name: 'ParcelStatistics',
  components: {
    Chart,
    ProgressBar
  },
  props: {
    parcelId: {
      type: [String, Number],
      required: true
    },
    parcelData: {
      type: Object,
      default: () => ({})
    }
  },
  setup(props) {
    // Normalement ces données viendraient du backend via props.parcelId
    // Ici c'est un mock pour démonstration
    
    const performanceStats = ref([
      { 
        label: 'Biomasse (tonnes)', 
        value: '486', 
        trend: 'up', 
        trendValue: 12.4 
      },
      { 
        label: 'Séquestration C02 (t/an)', 
        value: '18.3', 
        trend: 'up', 
        trendValue: 5.2 
      },
      { 
        label: 'Indice biodiversité', 
        value: '7.2/10', 
        trend: 'down', 
        trendValue: 2.1 
      }
    ]);
    
    const speciesComposition = ref([
      { name: 'Chêne sessile', percentage: 45 },
      { name: 'Hêtre', percentage: 30 },
      { name: 'Pin sylvestre', percentage: 15 },
      { name: 'Bouleau', percentage: 10 }
    ]);
    
    const healthIndicators = ref([
      { 
        label: 'Résistance aux maladies', 
        value: 7, 
        description: 'Bonne résistance globale avec quelques signes de dépérissement localisés'
      },
      { 
        label: 'Résistance aux sécheresses', 
        value: 5, 
        description: 'Vulnérabilité modérée aux épisodes de sécheresse prolongée'
      },
      { 
        label: 'Régénération naturelle', 
        value: 8, 
        description: 'Excellente régénération naturelle, bonne diversité de semis'
      },
      { 
        label: 'Stabilité face aux tempêtes', 
        value: 6, 
        description: 'Stabilité moyenne, parcelle partiellement exposée aux vents dominants'
      }
    ]);
    
    // Configuration du graphique d'évolution
    const chartData = ref({
      labels: ['2020', '2021', '2022', '2023', '2024', '2025'],
      datasets: [
        {
          label: 'Biomasse (tonnes)',
          data: [320, 350, 400, 430, 460, 486],
          fill: false,
          borderColor: '#2563EB',
          tension: 0.4
        },
        {
          label: 'Séquestration CO2 (t/an)',
          data: [12.1, 13.4, 15.2, 16.7, 17.5, 18.3],
          fill: false,
          borderColor: '#16A34A',
          tension: 0.4
        }
      ]
    });
    
    const chartOptions = ref({
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top'
        }
      },
      scales: {
        y: {
          beginAtZero: false
        }
      }
    });
    
    // Configuration du graphique en camembert
    const pieData = computed(() => ({
      labels: speciesComposition.value.map(s => s.name),
      datasets: [
        {
          data: speciesComposition.value.map(s => s.percentage),
          backgroundColor: [
            '#3B82F6', // Bleu
            '#10B981', // Vert
            '#F59E0B', // Orange
            '#6366F1'  // Indigo
          ],
          hoverBackgroundColor: [
            '#2563EB',
            '#059669',
            '#D97706',
            '#4F46E5'
          ]
        }
      ]
    }));
    
    const pieOptions = ref({
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        }
      }
    });
    
    // Méthodes utilitaires pour les classes CSS dynamiques
    const getStatCardColorClass = (trend) => {
      return trend === 'up' ? 'border-green-100 bg-green-50' : 'border-red-100 bg-red-50';
    };
    
    const getTrendTextColorClass = (trend) => {
      return trend === 'up' ? 'text-green-600' : 'text-red-600';
    };
    
    const getTrendIconClass = (trend) => {
      return trend === 'up' ? 'pi-arrow-up' : 'pi-arrow-down';
    };
    
    const getHealthIndicatorColorClass = (value) => {
      if (value >= 8) return 'green-progress';
      if (value >= 6) return 'blue-progress';
      if (value >= 4) return 'yellow-progress';
      return 'red-progress';
    };
    
    return {
      performanceStats,
      speciesComposition,
      healthIndicators,
      chartData,
      chartOptions,
      pieData,
      pieOptions,
      getStatCardColorClass,
      getTrendTextColorClass,
      getTrendIconClass,
      getHealthIndicatorColorClass
    };
  }
});
</script>

<style scoped>
.green-progress :deep(.p-progressbar-value) {
  background-color: #10B981;
}

.blue-progress :deep(.p-progressbar-value) {
  background-color: #3B82F6;
}

.yellow-progress :deep(.p-progressbar-value) {
  background-color: #F59E0B;
}

.red-progress :deep(.p-progressbar-value) {
  background-color: #EF4444;
}

.stat-card {
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}
</style>
