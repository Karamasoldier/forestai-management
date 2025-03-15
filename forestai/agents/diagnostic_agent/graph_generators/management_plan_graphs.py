# -*- coding: utf-8 -*-
"""
Module de génération de graphiques pour les rapports de plan de gestion.
"""

import logging
import io
import base64
from typing import Dict, Any, Optional

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Mode non-interactif

logger = logging.getLogger(__name__)

def generate_management_plan_graphs(plan: Dict[str, Any], diagnostic: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """Génère des graphiques pour le rapport de plan de gestion.
    
    Args:
        plan: Données du plan de gestion
        diagnostic: Données du diagnostic associé (optionnel)
        
    Returns:
        Dictionnaire des graphiques en base64
    """
    graphs = {}
    
    try:
        # Graphique des coûts par phase
        if 'estimated_costs' in plan and 'phase_breakdown' in plan['estimated_costs']:
            phase_costs = plan['estimated_costs']['phase_breakdown']
            phases = [phase['phase'] for phase in phase_costs]
            costs = [phase['cost'] for phase in phase_costs]
            
            plt.figure(figsize=(10, 6))
            bars = plt.bar(phases, costs, color='slateblue')
            plt.xlabel('Phases')
            plt.ylabel('Coût (euros)')
            plt.title('Coûts estimés par phase')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            # Ajouter les valeurs au-dessus des barres
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + 1, f'{height:,.0f}€',
                        ha='center', va='bottom', rotation=0)
            
            # Convertir en base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png')
            plt.close()
            buffer.seek(0)
            image_png = buffer.getvalue()
            buffer.close()
            encoded = base64.b64encode(image_png).decode('utf-8')
            graphs['phase_costs'] = f"data:image/png;base64,{encoded}"
        
        # Chronologie du plan de gestion
        if 'phases' in plan and plan['phases'] and 'horizon' in plan:
            phases = plan['phases']
            start_year = plan['horizon'].get('start_year')
            
            if start_year and isinstance(start_year, (int, float)):
                phase_names = [p['name'] for p in phases]
                phase_years = [p['year'] for p in phases]
                
                # Créer une figure pour le diagramme de Gantt simplifié
                fig, ax = plt.subplots(figsize=(12, 6))
                
                # Trier les phases par année
                phases_sorted = sorted(zip(phase_names, phase_years), key=lambda x: x[1])
                names = [p[0] for p in phases_sorted]
                years = [p[1] for p in phases_sorted]
                
                # Créer le graphique
                y_pos = range(len(names))
                ax.barh(y_pos, [1] * len(names), left=years, height=0.5, color='teal')
                
                # Ajouter les étiquettes
                ax.set_yticks(y_pos)
                ax.set_yticklabels(names)
                ax.set_xlabel('Années')
                ax.set_title('Chronologie du plan de gestion')
                
                # Ajuster les limites de l'axe X
                min_year = min(years) if years else start_year
                max_year = max(years) + 3 if years else start_year + 10
                ax.set_xlim(min_year - 0.5, max_year + 0.5)
                
                # Ajouter les années comme labels
                for i, (name, year) in enumerate(zip(names, years)):
                    ax.annotate(f"{year}", xy=(year, i), xytext=(5, 0), 
                                textcoords="offset points", 
                                va='center')
                
                plt.tight_layout()
                
                # Convertir en base64
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png')
                plt.close()
                buffer.seek(0)
                image_png = buffer.getvalue()
                buffer.close()
                encoded = base64.b64encode(image_png).decode('utf-8')
                graphs['timeline'] = f"data:image/png;base64,{encoded}"
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération des graphiques: {str(e)}")
        # Créer une image d'erreur
        plt.figure(figsize=(6, 4))
        plt.text(0.5, 0.5, f"Erreur de génération des graphiques: {str(e)}", 
                 horizontalalignment='center',
                 verticalalignment='center',
                 transform=plt.gca().transAxes)
        plt.axis('off')
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        plt.close()
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        encoded = base64.b64encode(image_png).decode('utf-8')
        graphs['error'] = f"data:image/png;base64,{encoded}"
        
    return graphs