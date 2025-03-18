<template>
  <div class="parcel-detail">
    <!-- En-tête avec actions -->
    <ParcelHeader 
      :parcel="parcel" 
      :loading="loading" 
      @back="goBack" 
      @edit="editParcel" 
      @new-diagnostic="newDiagnostic" 
      @generate-report="generateReport" 
      @toggle-menu="toggleContextMenu"
    />
    <Menu id="context-menu" ref="contextMenu" :model="contextMenuItems" :popup="true" />

    <!-- Contenu principal -->
    <div class="grid">
      <!-- Colonne principale -->
      <div class="col-12 lg:col-8">
        <ParcelGeneralInfo :parcel="parcel" :loading="loading" :formatNumber="formatNumber" />
        <ParcelStatistics 
          :parcel="parcel" 
          :loading="loading" 
          :formatNumber="formatNumber" 
          :formatDate="formatDate" 
          :getHealthColor="getHealthColor" 
          :compositionChartData="compositionChartData" 
          :compositionChartOptions="compositionChartOptions" 
        />
        <ParcelHistory 
          :parcel="parcel" 
          :loading="loading" 
          :formatDate="formatDate" 
          :getHistoryIconClass="getHistoryIconClass" 
          @navigate="navigateTo" 
        />
      </div>
      
      <!-- Colonne latérale -->
      <div class="col-12 lg:col-4">
        <ParcelMap :parcel="parcel" :loading="loading" @openInGIS="openInGIS" />
        <ParcelSubsidies 
          :parcel="parcel" 
          :loading="loading" 
          :formatNumber="formatNumber" 
          @viewSubsidy="viewSubsidy" 
          @searchSubsidies="searchSubsidies" 
        />
        <ParcelDiagnostics 
          :parcel="parcel" 
          :loading="loading" 
          :formatDate="formatDate" 
          @viewDiagnostic="viewDiagnostic" 
          @newDiagnostic="newDiagnostic" 
        />
      </div>
    </div>
    
    <!-- Dialogue de génération de rapport -->
    <ReportDialog 
      v-model:visible="reportDialogVisible" 
      :reportTypes="reportTypes" 
      :reportFormats="reportFormats" 
      v-model:form="reportForm" 
      @cancel="reportDialogVisible = false" 
      @generate="downloadReport" 
    />
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useToast } from 'primevue/usetoast';
import { parcelService } from '@/services/api';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';

// Importation des composants
import ParcelHeader from '@/components/parcels/ParcelHeader.vue';
import ParcelGeneralInfo from '@/components/parcels/ParcelGeneralInfo.vue';
import ParcelStatistics from '@/components/parcels/ParcelStatistics.vue';
import ParcelHistory from '@/components/parcels/ParcelHistory.vue';
import ParcelMap from '@/components/parcels/ParcelMap.vue';
import ParcelSubsidies from '@/components/parcels/ParcelSubsidies.vue';
import ParcelDiagnostics from '@/components/parcels/ParcelDiagnostics.vue';
import ReportDialog from '@/components/reports/ReportDialog.vue';

export default {
  name: 'ParcelDetailView',
  components: {
    ParcelHeader,
    ParcelGeneralInfo,
    ParcelStatistics,
    ParcelHistory,
    ParcelMap,
    ParcelSubsidies,
    ParcelDiagnostics,
    ReportDialog
  },
  props: {
    id: {
      type: String,
      required: false
    }
  },
  setup(props) {
    const route = useRoute();
    const router = useRouter();
    const toast = useToast();
    const contextMenu = ref(null);
    
    // État
    const loading = ref(true);
    const parcel = ref({});
    const reportDialogVisible = ref(false);
    
    // Options pour les menus et formulaires
    const reportTypes = [
      { name: 'Diagnostic complet', value: 'full_diagnostic' },
      { name: 'Synthèse de parcelle', value: 'parcel_summary' },
      { name: 'Analyse de potentiel', value: 'potential_analysis' },
      { name: 'État sanitaire', value: 'health_report' }
    ];
    
    const reportFormats = [
      { name: 'PDF', value: 'pdf' },
      { name: 'HTML', value: 'html' },
      { name: 'DOCX', value: 'docx' },
      { name: 'Excel', value: 'xlsx' }
    ];
    
    // Formulaire de génération de rapport
    const reportForm = reactive({
      type: 'parcel_summary',
      format: 'pdf',
      includeMap: true,
      includeStats: true,
      includeHistory: true,
      includeSubsidies: true
    });
    
    // Items du menu contextuel
    const contextMenuItems = [
      {
        label: 'Télécharger les données',
        icon: 'pi pi-download',
        command: () => {
          downloadParcelData();
        }
      },
      {
        label: 'Copier l\'identifiant',
        icon: 'pi pi-copy',
        command: () => {
          navigator.clipboard.writeText(parcel.value.id)
            .then(() => {
              toast.add({
                severity: 'success',
                summary: 'Copié',
                detail: 'Identifiant copié dans le presse-papier',
                life: 3000
              });
            });
        }
      },
      {
        separator: true
      },
      {
        label: 'Supprimer la parcelle',
        icon: 'pi pi-trash',
        command: () => {
          confirmDeleteParcel();
        }
      }
    ];
    
    // Données pour le graphique de composition
    const compositionChartData = computed(() => {
      if (!parcel.value.composition) return null;
      
      return {
        labels: parcel.value.composition.map(item => item.name),
        datasets: [
          {
            data: parcel.value.composition.map(item => item.percentage),
            backgroundColor: [
              '#22C55E', '#3B82F6', '#8B5CF6', '#F59E0B', '#10B981', '#EF4444', '#6366F1'
            ],
            hoverBackgroundColor: [
              '#16A34A', '#2563EB', '#7C3AED', '#D97706', '#059669', '#DC2626', '#4F46E5'
            ]
          }
        ]
      };
    });
    
    // Options pour le graphique de composition
    const compositionChartOptions = {
      plugins: {
        legend: {
          position: 'right'
        }
      },
      maintainAspectRatio: false
    };
    
    // Récupération des détails de la parcelle
    const fetchParcelDetails = async () => {
      try {
        loading.value = true;
        const parcelId = props.id || route.params.id;
        
        // En environnement réel, appel au service API
        // const response = await parcelService.getParcel(parcelId);
        // parcel.value = response.data.result;
        
        // Simulation - Données fictives
        await new Promise(resolve => setTimeout(resolve, 1500));
        
        parcel.value = {
          id: 'P12345',
          commune: 'Saint-Martin-de-Crau',
          section: 'B',
          numero: '0012',
          forestType: 'Conifères',
          area: 15.234,
          health: 85,
          address: 'Route des Marais',
          description: 'Forêt de pins d\'Alep avec quelques chênes verts disséminés. Sol calcaire caractéristique de la région. Exposition sud-ouest, pente légère (5-10%). Zone classée à risque incendie modéré.',
          averageAge: 35,
          density: 720,
          lastDiagnostic: new Date(2024, 9, 15),
          fireRisk: 'Modéré',
          diseaseRisk: 'Faible',
          composition: [
            { name: 'Pin d\'Alep', percentage: 65 },
            { name: 'Chêne vert', percentage: 15 },
            { name: 'Pin parasol', percentage: 10 },
            { name: 'Autres conifères', percentage: 5 },
            { name: 'Divers feuillus', percentage: 5 }
          ],
          history: [
            { type: 'Diagnostic', date: new Date(2024, 9, 15), description: 'Diagnostic forestier complet avec analyse phytosanitaire', link: '/diagnostics/D6789' },
            { type: 'Intervention', date: new Date(2024, 7, 10), description: 'Éclaircie sélective sur 8 hectares', link: '' },
            { type: 'Subvention', date: new Date(2024, 5, 22), description: 'Demande de subvention pour reboisement acceptée', link: '/subsidies/S2345' },
            { type: 'Visite', date: new Date(2024, 3, 5), description: 'Inspection suite à tempête, dégâts mineurs constatés', link: '' },
            { type: 'Plantation', date: new Date(2023, 10, 15), description: 'Plantation complémentaire de 2 ha (pins parasols)', link: '' }
          ],
          eligibleSubsidies: [
            { id: 'S2345', title: 'Aide au reboisement France Relance 2025', amount: 20800, organization: 'Ministère de l\'Agriculture' },
            { id: 'S3456', title: 'Subvention régionale pour forêt résiliente', amount: 12500, organization: 'Région PACA' }
          ],
          diagnostics: [
            { id: 'D6789', date: new Date(2024, 9, 15), type: 'Complet', summary: 'Bon état sanitaire général, quelques signes de stress hydrique' },
            { id: 'D5678', date: new Date(2023, 8, 20), type: 'Rapide', summary: 'Développement normal, surveillance recommandée pour chenilles processionnaires' }
          ]
        };
        
        loading.value = false;
      } catch (error) {
        console.error('Erreur lors de la récupération des détails de la parcelle:', error);
        toast.add({
          severity: 'error',
          summary: 'Erreur',
          detail: 'Impossible de récupérer les détails de la parcelle',
          life: 3000
        });
        loading.value = false;
      }
    };
    
    // Formatage des nombres
    const formatNumber = (value) => {
      return new Intl.NumberFormat('fr-FR', { 
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(value);
    };
    
    // Formatage des dates
    const formatDate = (date) => {
      return format(new Date(date), 'dd MMM yyyy', { locale: fr });
    };
    
    // Obtention de la couleur en fonction de la santé
    const getHealthColor = (health) => {
      if (health >= 80) return '#22C55E'; // Vert
      if (health >= 60) return '#F59E0B'; // Orange
      return '#EF4444'; // Rouge
    };
    
    // Obtention de la classe d'icône pour les événements d'historique
    const getHistoryIconClass = (type) => {
      switch (type) {
        case 'Diagnostic':
          return 'pi pi-file-edit p-timeline-event-marker-icon';
        case 'Intervention':
          return 'pi pi-cog p-timeline-event-marker-icon';
        case 'Subvention':
          return 'pi pi-euro p-timeline-event-marker-icon';
        case 'Visite':
          return 'pi pi-eye p-timeline-event-marker-icon';
        case 'Plantation':
          return 'pi pi-seedling p-timeline-event-marker-icon';
        default:
          return 'pi pi-calendar p-timeline-event-marker-icon';
      }
    };
    
    // Retour à la liste des parcelles
    const goBack = () => {
      router.push('/parcels');
    };
    
    // Affichage du menu contextuel
    const toggleContextMenu = (event) => {
      contextMenu.value.toggle(event);
    };
    
    // Édition de la parcelle
    const editParcel = () => {
      toast.add({
        severity: 'info',
        summary: 'Édition',
        detail: 'Fonction d\'édition à implémenter',
        life: 3000
      });
    };
    
    // Création d'un nouveau diagnostic
    const newDiagnostic = () => {
      router.push(`/diagnostics/new?parcelId=${parcel.value.id}`);
    };
    
    // Génération d'un rapport
    const generateReport = () => {
      reportDialogVisible.value = true;
    };
    
    // Téléchargement du rapport
    const downloadReport = async () => {
      try {
        toast.add({
          severity: 'info',
          summary: 'Génération du rapport',
          detail: 'Le rapport est en cours de génération...',
          life: 3000
        });
        
        // Simulation
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        toast.add({
          severity: 'success',
          summary: 'Rapport généré',
          detail: 'Le rapport a été généré avec succès',
          life: 3000
        });
        
        reportDialogVisible.value = false;
      } catch (error) {
        console.error('Erreur lors de la génération du rapport:', error);
        toast.add({
          severity: 'error',
          summary: 'Erreur',
          detail: 'Impossible de générer le rapport',
          life: 3000
        });
      }
    };
    
    // Téléchargement des données de la parcelle
    const downloadParcelData = () => {
      toast.add({
        severity: 'info',
        summary: 'Téléchargement',
        detail: 'Fonction de téléchargement à implémenter',
        life: 3000
      });
    };
    
    // Confirmation de suppression
    const confirmDeleteParcel = () => {
      toast.add({
        severity: 'info',
        summary: 'Suppression',
        detail: 'Fonction de suppression à implémenter',
        life: 3000
      });
    };
    
    // Ouverture dans le SIG
    const openInGIS = () => {
      toast.add({
        severity: 'info',
        summary: 'SIG',
        detail: 'Fonction d\'ouverture dans le SIG à implémenter',
        life: 3000
      });
    };
    
    // Visualisation d'une subvention
    const viewSubsidy = (subsidy) => {
      router.push(`/subsidies/${subsidy.id}`);
    };
    
    // Recherche de subventions
    const searchSubsidies = () => {
      router.push(`/subsidies?parcelId=${parcel.value.id}`);
    };
    
    // Visualisation d'un diagnostic
    const viewDiagnostic = (diagnostic) => {
      router.push(`/diagnostics/${diagnostic.id}`);
    };
    
    // Navigation vers un lien
    const navigateTo = (link) => {
      if (link) {
        router.push(link);
      }
    };
    
    // Chargement initial des données
    onMounted(() => {
      fetchParcelDetails();
    });
    
    return {
      loading,
      parcel,
      contextMenu,
      contextMenuItems,
      reportDialogVisible,
      reportTypes,
      reportFormats,
      reportForm,
      compositionChartData,
      compositionChartOptions,
      formatNumber,
      formatDate,
      getHealthColor,
      getHistoryIconClass,
      goBack,
      toggleContextMenu,
      editParcel,
      newDiagnostic,
      generateReport,
      downloadReport,
      downloadParcelData,
      confirmDeleteParcel,
      openInGIS,
      viewSubsidy,
      searchSubsidies,
      viewDiagnostic,
      navigateTo
    };
  }
};
</script>
