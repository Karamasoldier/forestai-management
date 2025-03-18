<template>
  <div class="subsidy-detail-container max-w-7xl mx-auto">
    <!-- Header -->
    <SubsidyHeader 
      :name="subsidy.name" 
      :provider="subsidy.provider" 
      :category="subsidy.category" 
      :status="subsidy.status" 
      @analyze="openEligibilityDialog"
      @apply="openApplicationDialog"
    />
    
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <!-- Colonne principale -->
      <div class="lg:col-span-2 space-y-4">
        <!-- Présentation -->
        <SubsidyPresentation 
          :description="subsidy.description"
          :objectives="subsidy.objectives"
          :eligibleActions="subsidy.eligibleActions"
          :eligibilityConditions="subsidy.eligibilityConditions"
        />
        
        <!-- Détails financiers -->
        <SubsidyFinancialDetails 
          :amountType="subsidy.amountType"
          :amount="subsidy.amount"
          :minAmount="subsidy.minAmount"
          :maxAmount="subsidy.maxAmount"
          :amountDescription="subsidy.amountDescription"
          :deadline="subsidy.deadline"
          :deadlineDescription="subsidy.deadlineDescription"
          :paymentSteps="subsidy.paymentSteps"
          :eligibleExpenses="subsidy.eligibleExpenses"
        />
        
        <!-- Procédure de dépôt -->
        <SubsidyApplicationProcess 
          :requiredDocuments="subsidy.requiredDocuments"
          :applicationSteps="subsidy.applicationSteps"
          :applicationUrl="subsidy.applicationUrl"
        />
      </div>
      
      <!-- Colonne latérale -->
      <div class="lg:col-span-1">
        <SubsidySidebar 
          :region="subsidy.region"
          :department="subsidy.department"
          :provider="subsidy.provider"
          :providerType="subsidy.providerType"
          :contactPerson="subsidy.contactPerson"
          :contactEmail="subsidy.contactEmail"
          :contactPhone="subsidy.contactPhone"
          :updatedAt="subsidy.updatedAt"
          :compatibilityScore="subsidy.compatibilityScore"
          :compatibleParcels="compatibleParcels"
          :similarSubsidies="similarSubsidies"
          @analyze="openEligibilityDialog"
        />
      </div>
    </div>
    
    <!-- Dialogs -->
    <EligibilityAnalysisDialog 
      v-model:visible="showEligibilityDialog"
      :subsidyId="subsidy.id"
      :parcelOptions="parcelOptions"
      @analysis-complete="handleAnalysisComplete"
    />
    
    <ApplicationDialog 
      v-model:visible="showApplicationDialog"
      :subsidyId="subsidy.id"
      :subsidyName="subsidy.name"
      :subsidyProvider="subsidy.provider"
      :amountType="subsidy.amountType"
      :amount="subsidy.amount"
      :minAmount="subsidy.minAmount"
      :maxAmount="subsidy.maxAmount"
      :amountDescription="subsidy.amountDescription"
      :requiredDocuments="subsidy.requiredDocuments"
      :parcelOptions="parcelOptions"
      @application-submitted="handleApplicationSubmitted"
    />
  </div>
</template>

<script>
import { defineComponent, ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { useToast } from 'primevue/usetoast';

// Importer les composants
import SubsidyHeader from '@/components/subsidies/SubsidyHeader.vue';
import SubsidyPresentation from '@/components/subsidies/SubsidyPresentation.vue';
import SubsidyFinancialDetails from '@/components/subsidies/SubsidyFinancialDetails.vue';
import SubsidyApplicationProcess from '@/components/subsidies/SubsidyApplicationProcess.vue';
import SubsidySidebar from '@/components/subsidies/SubsidySidebar.vue';
import EligibilityAnalysisDialog from '@/components/subsidies/EligibilityAnalysisDialog.vue';
import ApplicationDialog from '@/components/subsidies/ApplicationDialog.vue';

// Importer les services
import { subsidiesService } from '@/services/subsidies';
import { parcelsService } from '@/services/parcels';

export default defineComponent({
  name: 'SubsidyDetail',
  components: {
    SubsidyHeader,
    SubsidyPresentation,
    SubsidyFinancialDetails,
    SubsidyApplicationProcess,
    SubsidySidebar,
    EligibilityAnalysisDialog,
    ApplicationDialog
  },
  setup() {
    const route = useRoute();
    const toast = useToast();
    
    // États
    const loading = ref(false);
    const subsidy = ref({
      id: route.params.id,
      name: 'Aide au reboisement forestier',
      provider: 'Ministère de l\'Agriculture',
      providerType: 'Organisme public',
      category: 'Reboisement',
      status: 'Ouvert',
      region: 'Auvergne-Rhône-Alpes',
      department: null,
      amountType: 'percentage',
      amount: 80,
      minAmount: null,
      maxAmount: null,
      amountDescription: 'Jusqu\'à 80% des coûts éligibles de plantation',
      deadline: '2025-06-30',
      deadlineDescription: 'Dépôt des dossiers avant le 30 juin 2025',
      description: '<p>Cette aide vise à encourager le reboisement des parcelles forestières dégradées ou à faible valeur écologique par des essences diversifiées et adaptées au changement climatique.</p><p>Le programme s\'inscrit dans la stratégie nationale de développement forestier durable.</p>',
      objectives: [
        'Favoriser la résilience des forêts face au changement climatique',
        'Améliorer la biodiversité forestière',
        'Optimiser la séquestration carbone',
        'Soutenir la filière bois locale'
      ],
      eligibleActions: [
        {
          title: 'Plantation nouvelle',
          description: 'Création de boisements sur des terrains non forestiers'
        },
        {
          title: 'Reboisement',
          description: 'Renouvellement de peuplements existants dégradés'
        },
        {
          title: 'Diversification',
          description: 'Introduction d\'essences complémentaires'
        },
        {
          title: 'Enrichissement',
          description: 'Plantation dans des peuplements clairs'
        }
      ],
      eligibilityConditions: [
        'Surface minimale de 1 hectare d\'un seul tenant ou de 0,5 hectare si adjacent à une parcelle forestière existante',
        'Utilisation de plants forestiers conformes aux exigences réglementaires (MFR)',
        'Respect d\'une densité minimale de plantation selon les essences',
        'Projet comportant au moins 20% d\'essences d\'accompagnement',
        'Engagement de maintien de la destination forestière pendant 15 ans minimum'
      ],
      paymentSteps: [
        {
          label: 'Demande',
          icon: 'pi pi-file',
          description: 'Dépôt du dossier complet auprès de l\'organisme'
        },
        {
          label: 'Autorisation',
          icon: 'pi pi-check',
          description: 'Validation du dossier et autorisation de commencer les travaux'
        },
        {
          label: 'Acompte',
          icon: 'pi pi-wallet',
          description: 'Versement d\'un acompte de 30% après notification'
        },
        {
          label: 'Réalisation',
          icon: 'pi pi-cog',
          description: 'Réalisation des travaux selon cahier des charges'
        },
        {
          label: 'Solde',
          icon: 'pi pi-check-circle',
          description: 'Versement du solde après contrôle des travaux'
        }
      ],
      eligibleExpenses: [
        {
          category: 'Préparation du terrain',
          description: 'Coûts liés à la préparation du sol avant plantation',
          limit: 'Max 2 000€/ha'
        },
        {
          category: 'Plants forestiers',
          description: 'Achat des plants, transport et stockage',
          limit: null
        },
        {
          category: 'Plantation',
          description: 'Main d\'oeuvre et matériel pour la mise en place',
          limit: 'Max 3 000€/ha'
        },
        {
          category: 'Protection contre le gibier',
          description: 'Protections individuelles ou collectives',
          limit: 'Max 30% du coût total'
        },
        {
          category: 'Entretien initial',
          description: 'Dégagements, premiers entretiens (3 ans)',
          limit: 'Max 1 500€/ha'
        }
      ],
      applicationSteps: [
        {
          title: 'Préparer votre plan de reboisement',
          description: 'Définissez les essences, densités et modalités techniques selon les recommandations du guide de reboisement'
        },
        {
          title: 'Constituer le dossier technique',
          description: 'Incluez les plans cadastraux, l\'état des lieux actuel, les objectifs et le budget prévisionnel'
        },
        {
          title: 'Soumettre la demande',
          description: 'Envoyez le dossier complet à la DDT de votre département ou déposez-le sur la plateforme en ligne'
        },
        {
          title: 'Attendre l\'instruction',
          description: 'Délai d\'instruction de 2 à 3 mois avec possible visite de terrain'
        },
        {
          title: 'Démarrer les travaux après accord',
          description: 'Ne commencez pas les travaux avant d\'avoir reçu l\'autorisation officielle'
        }
      ],
      requiredDocuments: [
        'Formulaire de demande d\'aide complété et signé',
        'Justificatifs de propriété (relevé de propriété, matrice cadastrale)',
        'Plan de situation et plan cadastral des parcelles concernées',
        'Description technique du projet (essences, densités, travaux prévus)',
        'Devis détaillés des entreprises pour les travaux envisagés',
        'Attestation de certification forestière si applicable (PEFC, FSC)',
        'RIB du demandeur'
      ],
      applicationUrl: 'https://aides-territoires.beta.gouv.fr/',
      contactPerson: 'Service Forêt',
      contactEmail: 'foret.ddt@agriculture.gouv.fr',
      contactPhone: '01 49 55 49 55',
      updatedAt: '2025-01-15',
      compatibilityScore: 4
    });
    
    const parcelOptions = ref([]);
    const compatibleParcels = ref([]);
    const similarSubsidies = ref([
      {
        id: '2',
        name: 'Aide à la diversification des peuplements',
        provider: 'Conseil régional',
        status: 'Ouvert',
        amountType: 'fixed',
        amount: 1500
      },
      {
        id: '3',
        name: 'Soutien aux plantations résilientes',
        provider: 'Agence de l\'Eau',
        status: 'Bientôt clôturé',
        amountType: 'percentage',
        amount: 60
      }
    ]);
    
    // États des modals
    const showEligibilityDialog = ref(false);
    const showApplicationDialog = ref(false);
    
    // Chargement des données
    const loadSubsidy = async () => {
      loading.value = true;
      try {
        // En production, cette fonction ferait un appel API
        // const data = await subsidiesService.getSubsidyById(route.params.id);
        // subsidy.value = data;
        
        // Pour la démo, nous utilisons des données simulées
        await new Promise(resolve => setTimeout(resolve, 500));
        
      } catch (error) {
        console.error('Erreur lors du chargement de la subvention:', error);
        toast.add({
          severity: 'error',
          summary: 'Erreur',
          detail: 'Impossible de charger les détails de la subvention',
          life: 3000
        });
      } finally {
        loading.value = false;
      }
    };
    
    const loadParcels = async () => {
      try {
        // En production, cette fonction ferait un appel API
        // const data = await parcelsService.getParcels();
        
        // Pour la démo, nous utilisons des données simulées
        await new Promise(resolve => setTimeout(resolve, 300));
        
        parcelOptions.value = [
          { id: '1', name: 'A123 - Forêt de Champigny' },
          { id: '2', name: 'B456 - Bois des Chênes' },
          { id: '3', name: 'C789 - Parcelle du Ruisseau' },
          { id: '4', name: 'D012 - Forêt de la Vallée' }
        ];
        
        compatibleParcels.value = [
          { id: '1', reference: 'A123', surface: '12.5', compatibility: 3 },
          { id: '2', reference: 'B456', surface: '8.3', compatibility: 2 }
        ];
        
      } catch (error) {
        console.error('Erreur lors du chargement des parcelles:', error);
      }
    };
    
    // Gestion des modals
    const openEligibilityDialog = () => {
      showEligibilityDialog.value = true;
    };
    
    const openApplicationDialog = () => {
      showApplicationDialog.value = true;
    };
    
    // Gestion des résultats d'analyse et de soumission
    const handleAnalysisComplete = (results) => {
      compatibleParcels.value = results.parcels
        .filter(p => p.eligibilityScore >= 2)
        .map(p => ({
          id: p.id,
          reference: p.reference,
          surface: p.surface,
          compatibility: p.eligibilityScore
        }));
      
      toast.add({
        severity: 'success',
        summary: 'Analyse terminée',
        detail: `${compatibleParcels.value.length} parcelles compatibles identifiées`,
        life: 3000
      });
    };
    
    const handleApplicationSubmitted = (result) => {
      toast.add({
        severity: 'success',
        summary: 'Dossier créé',
        detail: `Demande n°${result.applicationId} soumise avec succès`,
        life: 3000
      });
    };
    
    // Initialisation
    onMounted(() => {
      loadSubsidy();
      loadParcels();
    });
    
    return {
      subsidy,
      parcelOptions,
      compatibleParcels,
      similarSubsidies,
      showEligibilityDialog,
      showApplicationDialog,
      openEligibilityDialog,
      openApplicationDialog,
      handleAnalysisComplete,
      handleApplicationSubmitted
    };
  }
});
</script>
