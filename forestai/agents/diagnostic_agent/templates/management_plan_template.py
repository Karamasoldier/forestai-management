# -*- coding: utf-8 -*-
"""
Module contenant le template HTML par défaut pour les rapports de plan de gestion.
"""

def create_default_management_plan_template() -> str:
    """Crée un modèle HTML par défaut pour les rapports de plan de gestion.
    
    Returns:
        Template HTML
    """
    return """<!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Plan de gestion forestière</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; color: #333; }
            h1, h2, h3 { color: #2c5e1a; }
            .header { text-align: center; margin-bottom: 30px; padding-bottom: 10px; border-bottom: 2px solid #2c5e1a; }
            .section { margin-bottom: 30px; }
            table { width: 100%; border-collapse: collapse; margin: 20px 0; }
            th, td { padding: 12px 15px; border-bottom: 1px solid #ddd; text-align: left; }
            th { background-color: #f2f7f2; }
            tr:hover { background-color: #f5f5f5; }
            .graph { max-width: 100%; margin: 20px 0; }
            .footer { margin-top: 50px; text-align: center; font-size: 0.8em; color: #666; }
            .metrics { display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 20px; }
            .metric-card { flex: 1; min-width: 200px; border: 1px solid #ddd; border-radius: 5px; padding: 15px; background-color: #f9f9f9; }
            .metric-value { font-size: 1.8em; font-weight: bold; color: #2c5e1a; }
            .metric-label { font-size: 0.9em; color: #666; }
            .phase-card { border: 1px solid #ddd; border-radius: 5px; margin-bottom: 20px; background-color: #f9f9f9; }
            .phase-header { background-color: #2c5e1a; color: white; padding: 10px 15px; border-radius: 5px 5px 0 0; }
            .phase-content { padding: 15px; }
            .phase-actions { margin: 10px 0; }
            .action-item { margin-bottom: 5px; }
            .timeline { margin: 30px 0; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Plan de gestion forestière</h1>
            <p>Parcelle: {{ plan.parcel_id }}</p>
            <p>Horizon: {{ plan.horizon.start_year }} - {{ plan.horizon.end_year }} ({{ plan.horizon.duration_years }} ans)</p>
            <p>Date de génération: {{ generation_date }}</p>
            <p>Identifiant du rapport: {{ report_id }}</p>
        </div>
        
        <div class="section">
            <h2>Résumé du plan</h2>
            {% if plan.summary %}
            <p>{{ plan.summary }}</p>
            {% endif %}
            
            <div class="metrics">
                <div class="metric-card">
                    <div class="metric-value">{{ plan.horizon.duration_years }} ans</div>
                    <div class="metric-label">Durée du plan</div>
                </div>
                
                {% if plan.phases %}
                <div class="metric-card">
                    <div class="metric-value">{{ plan.phases|length }}</div>
                    <div class="metric-label">Nombre de phases</div>
                </div>
                {% endif %}
                
                {% if plan.estimated_costs and plan.estimated_costs.total is defined %}
                <div class="metric-card">
                    <div class="metric-value">{{ plan.estimated_costs.total|format_number }}€</div>
                    <div class="metric-label">Coût total estimé</div>
                </div>
                {% endif %}
                
                {% if plan.goals %}
                <div class="metric-card">
                    <div class="metric-value">{{ plan.goals|length }}</div>
                    <div class="metric-label">Objectifs</div>
                </div>
                {% endif %}
            </div>
            
            {% if plan.goals %}
            <h3>Objectifs</h3>
            <ul>
                {% for goal in plan.goals %}
                <li>{{ goal|title }}</li>
                {% endfor %}
            </ul>
            {% endif %}
        </div>
        
        {% if graphs.timeline %}
        <div class="section timeline">
            <h2>Chronologie du plan</h2>
            <img src="{{ graphs.timeline }}" alt="Chronologie du plan" class="graph">
        </div>
        {% endif %}
        
        {% if plan.phases %}
        <div class="section">
            <h2>Phases du plan</h2>
            
            {% for phase in plan.phases %}
            <div class="phase-card">
                <div class="phase-header">
                    <h3>{{ phase.name }} ({{ phase.year }})</h3>
                </div>
                <div class="phase-content">
                    {% if phase.actions %}
                    <div class="phase-actions">
                        <h4>Actions</h4>
                        <ul>
                            {% for action in phase.actions %}
                            <li class="action-item">{{ action }}</li>
                            {% endfor %}
                        </ul>
                    </div>
                    {% endif %}
                    
                    {% if phase.expected_outcomes %}
                    <div class="phase-outcome">
                        <h4>Résultats attendus</h4>
                        <p>{{ phase.expected_outcomes }}</p>
                    </div>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>
        {% endif %}
        
        {% if plan.recommended_species %}
        <div class="section">
            <h2>Espèces recommandées</h2>
            
            <table>
                <tr>
                    <th>Espèce</th>
                    <th>Score global</th>
                    <th>Production</th>
                    <th>Résilience</th>
                    <th>Commentaire</th>
                </tr>
                {% for species in plan.recommended_species %}
                <tr>
                    <td>{{ species.species_name }}</td>
                    <td>{{ species.overall_suitability|format_percent }}</td>
                    <td>{{ species.suitability.production|format_percent }}</td>
                    <td>{{ species.suitability.resilience|format_percent }}</td>
                    <td>{{ species.comments }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
        {% endif %}
        
        {% if plan.estimated_costs %}
        <div class="section">
            <h2>Coûts estimés</h2>
            
            {% if graphs.phase_costs %}
            <img src="{{ graphs.phase_costs }}" alt="Coûts par phase" class="graph">
            {% endif %}
            
            <table>
                <tr>
                    <th>Phase</th>
                    <th>Coût estimé</th>
                    <th>Détails</th>
                </tr>
                {% for phase in plan.estimated_costs.phase_breakdown %}
                <tr>
                    <td>{{ phase.phase }}</td>
                    <td>{{ phase.cost|format_number }}€</td>
                    <td>{{ phase.details }}</td>
                </tr>
                {% endfor %}
                <tr>
                    <th>Total</th>
                    <th>{{ plan.estimated_costs.total|format_number }}€</th>
                    <td></td>
                </tr>
            </table>
            
            {% if plan.estimated_costs.disclaimer %}
            <p><em>{{ plan.estimated_costs.disclaimer }}</em></p>
            {% endif %}
        </div>
        {% endif %}
        
        {% if plan.monitoring_plan %}
        <div class="section">
            <h2>Plan de suivi</h2>
            
            <p><strong>Fréquence:</strong> {{ plan.monitoring_plan.frequency }}</p>
            
            {% if plan.monitoring_plan.indicators %}
            <h3>Indicateurs</h3>
            <ul>
                {% for indicator in plan.monitoring_plan.indicators %}
                <li>{{ indicator }}</li>
                {% endfor %}
            </ul>
            {% endif %}
        </div>
        {% endif %}
        
        {% if plan.climate_considerations %}
        <div class="section">
            <h2>Considérations climatiques</h2>
            
            {% if plan.climate_considerations.current %}
            <h3>Climat actuel</h3>
            <p>{{ plan.climate_considerations.current.description }}</p>
            {% endif %}
            
            {% if plan.climate_considerations.future %}
            <h3>Climat futur</h3>
            <p>{{ plan.climate_considerations.future.description }}</p>
            {% endif %}
        </div>
        {% endif %}
        
        <div class="footer">
            <p>Plan de gestion généré par ForestAI - Système de gestion forestière intelligente</p>
            <p>{{ generation_date }}</p>
        </div>
    </body>
    </html>
    """
