import axios from 'axios';

// Configuration de base d'axios
const api = axios.create({
  baseURL: process.env.VUE_APP_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  timeout: 30000 // 30 secondes
});

// Intercepteur pour ajouter le token d'authentification
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Intercepteur pour gérer les erreurs de réponse
api.interceptors.response.use(
  response => response,
  error => {
    const { response } = error;
    
    // Gestion des erreurs d'authentification (401)
    if (response && response.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/auth/login';
    }
    
    // Gestion des erreurs serveur (500)
    if (response && response.status >= 500) {
      console.error('Erreur serveur:', response.data);
    }
    
    return Promise.reject(error);
  }
);

// Service pour la gestion des parcelles
export const parcelService = {
  // Récupérer la liste des parcelles
  getParcels: (params = {}) => api.get('/geo/search', { params }),
  
  // Récupérer une parcelle par son ID
  getParcel: (id) => api.get(`/geo/analyze`, { params: { parcel_id: id, analyses: 'complete' } }),
  
  // Analyser une parcelle
  analyzeParcel: (id, analyses = ['basic']) => api.post('/geo/analyze', { parcel_id: id, analyses })
};

// Service pour la gestion des subventions
export const subsidyService = {
  // Récupérer la liste des subventions
  getSubsidies: (params = {}) => api.post('/subsidies/search', params),
  
  // Vérifier l'éligibilité d'un projet à une subvention
  checkEligibility: (project, subsidyId) => api.post('/subsidies/eligibility', { project, subsidy_id: subsidyId }),
  
  // Générer un document de demande de subvention
  generateApplication: (project, subsidyId, applicant, formats = ['pdf']) => 
    api.post('/subsidies/application', { project, subsidy_id: subsidyId, applicant, output_formats: formats })
};

// Service pour la gestion des diagnostics
export const diagnosticService = {
  // Récupérer la liste des diagnostics
  getDiagnostics: (params = {}) => api.get('/diagnostics', { params }),
  
  // Récupérer un diagnostic par son ID
  getDiagnostic: (id) => api.get(`/diagnostics/${id}`),
  
  // Créer un nouveau diagnostic
  createDiagnostic: (data) => api.post('/diagnostics', data),
  
  // Mettre à jour un diagnostic
  updateDiagnostic: (id, data) => api.put(`/diagnostics/${id}`, data),
  
  // Supprimer un diagnostic
  deleteDiagnostic: (id) => api.delete(`/diagnostics/${id}`)
};

// Service pour la gestion des rapports
export const reportService = {
  // Récupérer la liste des rapports
  getReports: (params = {}) => api.get('/reports', { params }),
  
  // Récupérer un rapport par son ID
  getReport: (id) => api.get(`/reports/${id}`),
  
  // Générer un nouveau rapport
  generateReport: (data) => api.post('/reports/generate', data),
  
  // Télécharger un rapport
  downloadReport: (id, format = 'pdf') => api.get(`/reports/${id}/download?format=${format}`, {
    responseType: 'blob'
  })
};

export default api;
