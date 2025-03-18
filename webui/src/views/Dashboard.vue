<template>
  <div class="dashboard">
    <div class="page-header">
      <h1>Tableau de bord</h1>
      <div class="actions">
        <Button label="Actualiser" icon="pi pi-refresh" outlined @click="refreshData" :loading="loading" />
      </div>
    </div>

    <!-- Cartes statistiques -->
    <div class="grid">
      <div class="col-12 md:col-6 lg:col-3">
        <Card class="stats-card">
          <template #header>
            <div class="card-header">
              <i class="pi pi-map text-green-500"></i>
              <span class="text-lg font-bold">Parcelles</span>
            </div>
          </template>
          <template #content>
            <div class="card-content">
              <span class="text-4xl font-bold">{{ stats.parcels.count }}</span>
              <span class="text-sm text-500">Total de parcelles</span>
            </div>
          </template>
          <template #footer>
            <div class="card-footer">
              <span :class="stats.parcels.trend >= 0 ? 'text-green-500' : 'text-red-500'">
                <i :class="stats.parcels.trend >= 0 ? 'pi pi-arrow-up' : 'pi pi-arrow-down'"></i>
                {{ Math.abs(stats.parcels.trend) }}%
              </span>
              <span class="text-sm text-500">vs mois précédent</span>
            </div>
          </template>
        </Card>
      </div>
      
      <div class="col-12 md:col-6 lg:col-3">
        <Card class="stats-card">
          <template #header>
            <div class="card-header">
              <i class="pi pi-euro text-yellow-500"></i>
              <span class="text-lg font-bold">Subventions</span>
            </div>
          </template>
          <template #content>
            <div class="card-content">
              <span class="text-4xl font-bold">{{ stats.subsidies.count }}</span>
              <span class="text-sm text-500">Subventions disponibles</span>
            </div>
          </template>
          <template #footer>
            <div class="card-footer">
              <span class="text-green-500">
                <i class="pi pi-check-circle"></i>
                {{ stats.subsidies.eligible }}
              </span>
              <span class="text-sm text-500">subventions éligibles</span>
            </div>
          </template>
        </Card>
      </div>
      
      <div class="col-12 md:col-6 lg:col-3">
        <Card class="stats-card">
          <template #header>
            <div class="card-header">
              <i class="pi pi-file-edit text-blue-500"></i>
              <span class="text-lg font-bold">Diagnostics</span>
            </div>
          </template>
          <template #content>
            <div class="card-content">
              <span class="text-4xl font-bold">{{ stats.diagnostics.count }}</span>
              <span class="text-sm text-500">Diagnostics réalisés</span>
            </div>
          </template>
          <template #footer>
            <div class="card-footer">
              <span :class="stats.diagnostics.trend >= 0 ? 'text-green-500' : 'text-red-500'">
                <i :class="stats.diagnostics.trend >= 0 ? 'pi pi-arrow-up' : 'pi pi-arrow-down'"></i>
                {{ Math.abs(stats.diagnostics.trend) }}%
              </span>
              <span class="text-sm text-500">vs mois précédent</span>
            </div>
          </template>
        </Card>
      </div>
      
      <div class="col-12 md:col-6 lg:col-3">
        <Card class="stats-card">
          <template #header>
            <div class="card-header">
              <i class="pi pi-file-pdf text-purple-500"></i>
              <span class="text-lg font-bold">Rapports</span>
            </div>
          </template>
          <template #content>
            <div class="card-content">
              <span class="text-4xl font-bold">{{ stats.reports.count }}</span>
              <span class="text-sm text-500">Rapports générés</span>
            </div>
          </template>
          <template #footer>
            <div class="card-footer">
              <span :class="stats.reports.trend >= 0 ? 'text-green-500' : 'text-red-500'">
                <i :class="stats.reports.trend >= 0 ? 'pi pi-arrow-up' : 'pi pi-arrow-down'"></i>
                {{ Math.abs(stats.reports.trend) }}%
              </span>
              <span class="text-sm text-500">vs mois précédent</span>
            </div>
          </template>
        </Card>
      </div>
    </div>

    <!-- Graphiques -->
    <div class="grid">
      <div class="col-12 lg:col-8">
        <Card>
          <template #title>
            <div class="flex align-items-center justify-content-between mb-3">
              <span class="text-xl font-medium">Évolution annuelle</span>
              <Dropdown v-model="selectedChartType" :options="chartTypes" optionLabel="name" optionValue="value" placeholder="Type de données" class="w-12rem" />
            </div>
          </template>
          <template #content>
            <Chart type="line" :data="lineChartData" :options="lineChartOptions" class="w-full h-20rem" />
          </template>
        </Card>
      </div>
      
      <div class="col-12 lg:col-4">
        <Card>
          <template #title>
            <span class="text-xl font-medium">Répartition des parcelles</span>
          </template>
          <template #content>
            <Chart type="doughnut" :data="doughnutChartData" :options="doughnutChartOptions" class="w-full h-20rem" />
          </template>
        </Card>
      </div>
    </div>

    <!-- Activité récente -->
    <div class="grid">
      <div class="col-12">
        <Card>
          <template #title>
            <div class="flex align-items-center justify-content-between">
              <span class="text-xl font-medium">Activité récente</span>
              <Button label="Voir tout" icon="pi pi-external-link" text />
            </div>
          </template>
          <template #content>
            <DataTable :value="recentActivity" :rows="5" stripedRows class="p-datatable-sm" responsiveLayout="scroll">
              <Column field="date" header="Date" style="width: 15%">
                <template #body="slotProps">
                  {{ formatDate(slotProps.data.date) }}
                </template>
              </Column>
              <Column field="type" header="Type" style="width: 15%">
                <template #body="slotProps">
                  <span :class="getActivityTypeClass(slotProps.data.type)">
                    {{ slotProps.data.type }}
                  </span>
                </template>
              </Column>
              <Column field="description" header="Description" style="width: 55%" />
              <Column header="Action" style="width: 15%">
                <template #body="slotProps">
                  <Button icon="pi pi-eye" text rounded @click="viewActivity(slotProps.data)" />
                </template>
              </Column>
            </DataTable>
          </template>
        </Card>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useToast } from 'primevue/usetoast';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';

export default {
  name: 'DashboardView',
  setup() {
    const router = useRouter();
    const toast = useToast();
    
    // État de chargement
    const loading = ref(false);
    
    // Statistiques
    const stats = reactive({
      parcels: { count: 182, trend: 15 },
      subsidies: { count: 24, eligible: 12 },
      diagnostics: { count: 78, trend: 8 },
      reports: { count: 56, trend: -3 }
    });
    
    // Type de graphique sélectionné
    const selectedChartType = ref('parcels');
    const chartTypes = [
      { name: 'Parcelles', value: 'parcels' },
      { name: 'Diagnostics', value: 'diagnostics' },
      { name: 'Subventions', value: 'subsidies' },
      { name: 'Rapports', value: 'reports' }
    ];
    
    // Données du graphique linéaire
    const lineChartData = reactive({
      labels: ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'],
      datasets: [
        {
          label: 'Parcelles',
          data: [28, 35, 42, 56, 58, 68, 70, 79, 85, 92, 100, 118],
          borderColor: '#22C55E',
          backgroundColor: 'rgba(34, 197, 94, 0.2)',
          tension: 0.4,
          fill: true
        }
      ]
    });
    
    // Options du graphique linéaire
    const lineChartOptions = {
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        y: {
          beginAtZero: true
        }
      },
      maintainAspectRatio: false
    };
    
    // Données du graphique en anneau
    const doughnutChartData = {
      labels: ['Forêt de conifères', 'Forêt de feuillus', 'Forêt mixte', 'Taillis', 'Plantation récente'],
      datasets: [
        {
          data: [35, 25, 22, 12, 6],
          backgroundColor: ['#22C55E', '#3B82F6', '#F59E0B', '#8B5CF6', '#10B981'],
          hoverBackgroundColor: ['#16A34A', '#2563EB', '#D97706', '#7C3AED', '#059669']
        }
      ]
    };
    
    // Options du graphique en anneau
    const doughnutChartOptions = {
      plugins: {
        legend: {
          position: 'bottom'
        }
      },
      maintainAspectRatio: false
    };
    
    // Activité récente
    const recentActivity = ref([
      { id: 1, type: 'Parcelle', date: new Date(2025, 2, 18), description: 'Ajout d\'une nouvelle parcelle forestière de 12.5 ha', reference: 'P12345' },
      { id: 2, type: 'Diagnostic', date: new Date(2025, 2, 17), description: 'Diagnostic forestier complet effectué sur la parcelle BD4567', reference: 'D6789' },
      { id: 3, type: 'Subvention', date: new Date(2025, 2, 15), description: 'Demande de subvention approuvée pour le reboisement de la parcelle AC3456', reference: 'S2345' },
      { id: 4, type: 'Rapport', date: new Date(2025, 2, 14), description: 'Génération d\'un rapport d\'analyse de croissance forestière', reference: 'R7890' },
      { id: 5, type: 'Parcelle', date: new Date(2025, 2, 12), description: 'Mise à jour des données pour 3 parcelles forestières', reference: 'P5678' }
    ]);
    
    // Mise à jour des données du graphique en fonction du type sélectionné
    watch(selectedChartType, (newType) => {
      switch (newType) {
        case 'parcels':
          lineChartData.datasets[0].label = 'Parcelles';
          lineChartData.datasets[0].data = [28, 35, 42, 56, 58, 68, 70, 79, 85, 92, 100, 118];
          lineChartData.datasets[0].borderColor = '#22C55E';
          lineChartData.datasets[0].backgroundColor = 'rgba(34, 197, 94, 0.2)';
          break;
        case 'diagnostics':
          lineChartData.datasets[0].label = 'Diagnostics';
          lineChartData.datasets[0].data = [10, 12, 15, 18, 22, 25, 28, 32, 38, 42, 48, 52];
          lineChartData.datasets[0].borderColor = '#3B82F6';
          lineChartData.datasets[0].backgroundColor = 'rgba(59, 130, 246, 0.2)';
          break;
        case 'subsidies':
          lineChartData.datasets[0].label = 'Subventions';
          lineChartData.datasets[0].data = [2, 3, 3, 4, 5, 6, 8, 9, 12, 15, 18, 22];
          lineChartData.datasets[0].borderColor = '#F59E0B';
          lineChartData.datasets[0].backgroundColor = 'rgba(245, 158, 11, 0.2)';
          break;
        case 'reports':
          lineChartData.datasets[0].label = 'Rapports';
          lineChartData.datasets[0].data = [5, 8, 10, 12, 15, 18, 22, 25, 28, 32, 38, 45];
          lineChartData.datasets[0].borderColor = '#8B5CF6';
          lineChartData.datasets[0].backgroundColor = 'rgba(139, 92, 246, 0.2)';
          break;
      }
    });
    
    // Récupération des données
    const fetchData = async () => {
      try {
        loading.value = true;
        
        // Simulation de l'appel API pour récupérer les données
        // Dans un environnement réel, vous utiliseriez les services API
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Mise à jour des statistiques avec les données simulées
        // En production, ces données viendraient de l'API
        
        loading.value = false;
      } catch (error) {
        console.error('Erreur lors de la récupération des données:', error);
        toast.add({
          severity: 'error',
          summary: 'Erreur',
          detail: 'Impossible de récupérer les données du tableau de bord',
          life: 3000
        });
        loading.value = false;
      }
    };
    
    // Actualisation des données
    const refreshData = () => {
      fetchData();
    };
    
    // Formatage de la date
    const formatDate = (date) => {
      return format(date, 'dd MMM yyyy', { locale: fr });
    };
    
    // Obtention de la classe CSS en fonction du type d'activité
    const getActivityTypeClass = (type) => {
      switch (type) {
        case 'Parcelle':
          return 'activity-type parcelle';
        case 'Diagnostic':
          return 'activity-type diagnostic';
        case 'Subvention':
          return 'activity-type subvention';
        case 'Rapport':
          return 'activity-type rapport';
        default:
          return 'activity-type';
      }
    };
    
    // Affichage des détails d'une activité
    const viewActivity = (activity) => {
      const type = activity.type.toLowerCase();
      let route = '';
      
      switch (type) {
        case 'parcelle':
          route = `/parcels/${activity.reference.substring(1)}`;
          break;
        case 'diagnostic':
          route = `/diagnostics/${activity.reference.substring(1)}`;
          break;
        case 'subvention':
          route = `/subsidies/${activity.reference.substring(1)}`;
          break;
        case 'rapport':
          route = `/reports/${activity.reference.substring(1)}`;
          break;
      }
      
      if (route) {
        router.push(route);
      }
    };
    
    // Chargement initial des données
    onMounted(() => {
      fetchData();
    });
    
    return {
      loading,
      stats,
      selectedChartType,
      chartTypes,
      lineChartData,
      lineChartOptions,
      doughnutChartData,
      doughnutChartOptions,
      recentActivity,
      refreshData,
      formatDate,
      getActivityTypeClass,
      viewActivity
    };
  }
};
</script>

<style lang="scss" scoped>
.dashboard {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
    
    h1 {
      margin: 0;
      font-size: 1.75rem;
      font-weight: 600;
      color: var(--text-color);
    }
  }
  
  .stats-card {
    height: 100%;
    
    .card-header {
      display: flex;
      align-items: center;
      padding: 1rem;
      border-bottom: 1px solid var(--surface-border);
      
      i {
        font-size: 1.5rem;
        margin-right: 0.75rem;
      }
    }
    
    .card-content {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 1.5rem 1rem;
      
      .text-4xl {
        margin-bottom: 0.5rem;
      }
    }
    
    .card-footer {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 1rem;
      border-top: 1px solid var(--surface-border);
      background-color: var(--surface-section);
      
      i {
        margin-right: 0.25rem;
      }
    }
  }
  
  .activity-type {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 1rem;
    font-size: 0.875rem;
    font-weight: 600;
    
    &.parcelle {
      background-color: rgba(34, 197, 94, 0.2);
      color: #16A34A;
    }
    
    &.diagnostic {
      background-color: rgba(59, 130, 246, 0.2);
      color: #2563EB;
    }
    
    &.subvention {
      background-color: rgba(245, 158, 11, 0.2);
      color: #D97706;
    }
    
    &.rapport {
      background-color: rgba(139, 92, 246, 0.2);
      color: #7C3AED;
    }
  }
}
</style>
