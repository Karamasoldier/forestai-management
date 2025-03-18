<template>
  <div class="subsidy-detail-view">
    <div class="mb-4">
      <router-link to="/subsidies" class="btn btn-outline-secondary">
        <i class="bi bi-arrow-left me-2"></i> Retour aux subventions
      </router-link>
    </div>
    
    <div v-if="loading" class="text-center py-5">
      <LoadingSpinner message="Chargement des détails de la subvention..." />
    </div>
    
    <div v-else-if="error" class="alert alert-danger" role="alert">
      {{ error }}
    </div>
    
    <div v-else-if="subsidy">
      <!-- En-tête -->
      <SubsidyHeader :subsidy="subsidy" />
      
      <!-- Détails de la subvention -->
      <div class="row">
        <div class="col-md-8">
          <SubsidyDetails :subsidy="subsidy" />
          <SubsidyApplicationProcess :subsidy="subsidy" />
        </div>
        
        <div class="col-md-4">
          <SubsidyProvider :subsidy="subsidy" />
          <SubsidyActions 
            @check-eligibility="checkEligibility" 
            @generate-application="generateApplication" 
            @download-information="downloadInformation" 
          />
          <SubsidyDates :subsidy="subsidy" />
        </div>
      </div>
    </div>
    
    <div v-else class="alert alert-warning" role="alert">
      Subvention non trouvée ou indisponible.
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { subsidyService } from '@/services/api'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import SubsidyHeader from '@/components/subsidies/SubsidyHeader.vue'
import SubsidyDetails from '@/components/subsidies/SubsidyDetails.vue'
import SubsidyApplicationProcess from '@/components/subsidies/SubsidyApplicationProcess.vue'
import SubsidyProvider from '@/components/subsidies/SubsidyProvider.vue'
import SubsidyActions from '@/components/subsidies/SubsidyActions.vue'
import SubsidyDates from '@/components/subsidies/SubsidyDates.vue'

export default {
  name: 'SubsidyDetailView',
  components: {
    LoadingSpinner,
    SubsidyHeader,
    SubsidyDetails,
    SubsidyApplicationProcess,
    SubsidyProvider,
    SubsidyActions,
    SubsidyDates
  },
  setup() {
    const route = useRoute()
    const subsidy = ref(null)
    const loading = ref(false)
    const error = ref(null)
    
    const fetchSubsidyDetails = async () => {
      const subsidyId = route.params.id
      if (!subsidyId) {
        error.value = 'Identifiant de subvention manquant.'
        return
      }
      
      loading.value = true
      error.value = null
      
      try {
        // Appel à l'API pour récupérer les détails de la subvention
        // const response = await subsidyService.getSubsidyDetails(subsidyId)
        // subsidy.value = response.data.result
        
        // Pour la démo - données factices
        await new Promise(resolve => setTimeout(resolve, 800))
        
        subsidy.value = {
          id: subsidyId,
          title: 'Aide au reboisement post-tempête',
          description: 'Subvention pour reboiser les parcelles endommagées par les événements climatiques majeurs.',
          type: 'reboisement',
          region: 'Occitanie',
          provider: 'Conseil Régional d\'Occitanie',
          provider_address: '22 boulevard du Maréchal Juin, 31400 Toulouse',
          provider_contact: 'contact-foret@laregion.fr',
          provider_website: 'https://www.laregion.fr',
          amount_type: 'percentage',
          percentage: 60,
          max_amount: 7500,
          publication_date: '15/01/2025',
          deadline: '30/06/2025',
          response_date: '31/08/2025',
          eligibility_conditions: [
            'Parcelles situées en Occitanie',
            'Dommages liés à un événement climatique survenu après le 01/01/2023',
            'Surface minimale: 1 hectare',
            'Propriétaire privé ou collectivité',
            'Engagement d\'entretien sur 5 ans minimum'
          ],
          eligible_expenses: [
            'Préparation du terrain',
            'Achat de plants',
            'Opérations de plantation',
            'Protections contre le gibier',
            'Premiers entretiens (jusqu\'\u00e0 3 ans après plantation)'
          ],
          non_eligible_expenses: [
            'Travaux réalisés en régie (par le propriétaire)',
            'Entretiens au-delà de 3 ans',
            'TVA pour les propriétaires assujettis'
          ],
          application_steps: [
            'Déposer un dossier de demande avant la date limite',
            'Joindre les pièces justificatives requises',
            'Attendre la notification d\'attribution',
            'Réaliser les travaux dans les 2 ans suivant la notification',
            'Transmettre les factures acquittées pour paiement'
          ],
          required_documents: [
            'Formulaire de demande complété',
            'Relevé d\'identité bancaire',
            'Titre de propriété ou matrice cadastrale',
            'Constat de dégâts par un expert forestier',
            'Devis des travaux envisagés',
            'Plan de localisation des parcelles'
          ],
          additional_info: 'Cette aide peut être cumulée avec le crédit d\'impôt pour investissement forestier, mais pas avec d\'autres subventions publiques pour les mêmes travaux.'
        }
      } catch (err) {
        console.error('Error fetching subsidy details:', err)
        error.value = 'Impossible de récupérer les détails de la subvention.'
      } finally {
        loading.value = false
      }
    }
    
    const checkEligibility = () => {
      // Implémentation à ajouter
      console.log('Vérification de l\'\u00e9ligibilité')
    }
    
    const generateApplication = () => {
      // Implémentation à ajouter
      console.log('Génération de la demande')
    }
    
    const downloadInformation = () => {
      // Implémentation à ajouter
      console.log('Téléchargement de la fiche d\'information')
    }
    
    onMounted(() => {
      fetchSubsidyDetails()
    })
    
    return {
      subsidy,
      loading,
      error,
      checkEligibility,
      generateApplication,
      downloadInformation
    }
  }
}
</script>
