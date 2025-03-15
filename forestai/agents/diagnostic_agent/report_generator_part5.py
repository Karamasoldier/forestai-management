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
    
    def _create_default_diagnostic_template(self) -> str:
        """Crée un modèle HTML par défaut pour les rapports de diagnostic.
        
        Returns:
            Template HTML
        """
        return """<!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Rapport de diagnostic forestier</title>
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
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Rapport de diagnostic forestier</h1>
                <p>Parcelle: {{ diagnostic.parcel_id }}</p>
                <p>Date de génération: {{ generation_date }}</p>
                <p>Identifiant du rapport: {{ report_id }}</p>
            </div>
            
            <div class="section">
                <h2>Résumé du diagnostic</h2>
                
                <div class="metrics">
                    {% if diagnostic.potential and diagnostic.potential.overall_score is defined %}
                    <div class="metric-card">
                        <div class="metric-value">{{ diagnostic.potential.overall_score|format_percent }}</div>
                        <div class="metric-label">Potentiel forestier global</div>
                    </div>
                    {% endif %}
                    
                    {% if diagnostic.parcel_data and diagnostic.parcel_data.area is defined %}
                    <div class="metric-card">
                        <div class="metric-value">{{ diagnostic.parcel_data.area|format_number }} ha</div>
                        <div class="metric-label">Surface</div>
                    </div>
                    {% endif %}
                    
                    {% if diagnostic.climate and diagnostic.climate.summary and diagnostic.climate.summary.risk_level is defined %}
                    <div class="metric-card">
                        <div class="metric-value">{{ diagnostic.climate.summary.risk_level }}</div>
                        <div class="metric-label">Niveau de risque climatique</div>
                    </div>
                    {% endif %}
                    
                    {% if diagnostic.species_recommendations and diagnostic.species_recommendations.recommended_species %}
                    <div class="metric-card">
                        <div class="metric-value">{{ diagnostic.species_recommendations.recommended_species|length }}</div>
                        <div class="metric-label">Espèces recommandées</div>
                    </div>
                    {% endif %}
                </div>
            </div>
            
            {% if graphs.potential %}
            <div class="section">
                <h2>Potentiel forestier</h2>
                <img src="{{ graphs.potential }}" alt="Graphique de potentiel forestier" class="graph">
                
                <table>
                    <tr>
                        <th>Métrique</th>
                        <th>Valeur</th>
                        <th>Interprétation</th>
                    </tr>
                    {% for key, value in diagnostic.potential.items() %}
                        {% if key != 'summary' and value is not mapping %}
                        <tr>
                            <td>{{ key|replace('_', ' ')|title }}</td>
                            <td>{% if value <= 1 and value >= 0 %}{{ value|format_percent }}{% else %}{{ value|format_number }}{% endif %}</td>
                            <td>
                                {% if value > 0.8 %}
                                    Excellent
                                {% elif value > 0.6 %}
                                    Bon
                                {% elif value > 0.4 %}
                                    Moyen
                                {% elif value > 0.2 %}
                                    Faible
                                {% else %}
                                    Très faible
                                {% endif %}
                            </td>
                        </tr>
                        {% endif %}
                    {% endfor %}
                </table>
            </div>
            {% endif %}
            
            {% if diagnostic.species_recommendations and diagnostic.species_recommendations.recommended_species %}
            <div class="section">
                <h2>Recommandations d'espèces</h2>
                
                {% if graphs.species_recommendations %}
                <img src="{{ graphs.species_recommendations }}" alt="Recommandations d'espèces" class="graph">
                {% endif %}
                
                <table>
                    <tr>
                        <th>Espèce</th>
                        <th>Score global</th>
                        <th>Compatibilité climatique</th>
                        <th>Compatibilité sol</th>
                        <th>Commentaire</th>
                    </tr>
                    {% for species in diagnostic.species_recommendations.recommended_species %}
                    <tr>
                        <td>{{ species.species_name }}</td>
                        <td>{{ species.overall_suitability|format_percent }}</td>
                        <td>{{ species.suitability.climate|format_percent }}</td>
                        <td>{{ species.suitability.soil|format_percent }}</td>
                        <td>{{ species.comments }}</td>
                    </tr>
                    {% endfor %}
                </table>
            </div>
            {% endif %}
            
            {% if diagnostic.climate and diagnostic.climate.data %}
            <div class="section">
                <h2>Analyse climatique</h2>
                
                {% if graphs.climate %}
                <img src="{{ graphs.climate }}" alt="Données climatiques" class="graph">
                {% endif %}
                
                {% if diagnostic.climate.summary %}
                <h3>Résumé climatique</h3>
                <p>{{ diagnostic.climate.summary.description }}</p>
                
                <table>
                    <tr>
                        <th>Métrique</th>
                        <th>Valeur</th>
                    </tr>
                    {% for key, value in diagnostic.climate.summary.items() if key != 'description' %}
                    <tr>
                        <td>{{ key|replace('_', ' ')|title }}</td>
                        <td>{{ value }}</td>
                    </tr>
                    {% endfor %}
                </table>
                {% endif %}
            </div>
            {% endif %}
            
            {% if diagnostic.inventory %}
            <div class="section">
                <h2>Analyse de l'inventaire forestier</h2>
                
                <div class="metrics">
                    {% if diagnostic.inventory.basic_metrics and diagnostic.inventory.basic_metrics.total_trees is defined %}
                    <div class="metric-card">
                        <div class="metric-value">{{ diagnostic.inventory.basic_metrics.total_trees }}</div>
                        <div class="metric-label">Nombre total d'arbres</div>
                    </div>
                    {% endif %}
                    
                    {% if diagnostic.inventory.basic_metrics and diagnostic.inventory.basic_metrics.species_count is defined %}
                    <div class="metric-card">
                        <div class="metric-value">{{ diagnostic.inventory.basic_metrics.species_count }}</div>
                        <div class="metric-label">Nombre d'espèces</div>
                    </div>
                    {% endif %}
                    
                    {% if diagnostic.inventory.basic_metrics and diagnostic.inventory.basic_metrics.density and diagnostic.inventory.basic_metrics.density.trees_per_ha is defined %}
                    <div class="metric-card">
                        <div class="metric-value">{{ diagnostic.inventory.basic_metrics.density.trees_per_ha|format_number }}</div>
                        <div class="metric-label">Densité (arbres/ha)</div>
                    </div>
                    {% endif %}
                    
                    {% if diagnostic.inventory.volumes and diagnostic.inventory.volumes.total_volume_m3 is defined %}
                    <div class="metric-card">
                        <div class="metric-value">{{ diagnostic.inventory.volumes.total_volume_m3|format_number }}</div>
                        <div class="metric-label">Volume total (m³)</div>
                    </div>
                    {% endif %}
                </div>
                
                {% if graphs.species_distribution %}
                <h3>Distribution des espèces</h3>
                <img src="{{ graphs.species_distribution }}" alt="Distribution des espèces" class="graph">
                {% endif %}
                
                {% if graphs.volume_by_species %}
                <h3>Volume par espèce</h3>
                <img src="{{ graphs.volume_by_species }}" alt="Volume par espèce" class="graph">
                {% endif %}
                
                {% if diagnostic.inventory.stand_structure %}
                <h3>Structure du peuplement</h3>
                <p><strong>Type de structure:</strong> {{ diagnostic.inventory.stand_structure.diameter_distribution.structure_type }}</p>
                <p>{{ diagnostic.inventory.stand_structure.diameter_distribution.sylvicultural_interpretation }}</p>
                {% endif %}
                
                {% if diagnostic.inventory.diversity %}
                <h3>Indices de diversité</h3>
                <table>
                    <tr>
                        <th>Indice</th>
                        <th>Valeur</th>
                        <th>Interprétation</th>
                    </tr>
                    <tr>
                        <td>Indice de Shannon</td>
                        <td>{{ diagnostic.inventory.diversity.shannon_index|format_number }}</td>
                        <td>{% if diagnostic.inventory.diversity.shannon_index > 2 %}Diversité élevée{% elif diagnostic.inventory.diversity.shannon_index > 1 %}Diversité moyenne{% else %}Diversité faible{% endif %}</td>
                    </tr>
                    <tr>
                        <td>Indice de Simpson</td>
                        <td>{{ diagnostic.inventory.diversity.simpson_index|format_number }}</td>
                        <td>{% if diagnostic.inventory.diversity.simpson_index > 0.7 %}Diversité élevée{% elif diagnostic.inventory.diversity.simpson_index > 0.4 %}Diversité moyenne{% else %}Diversité faible{% endif %}</td>
                    </tr>
                    <tr>
                        <td>Richesse en espèces</td>
                        <td>{{ diagnostic.inventory.diversity.species_richness }}</td>
                        <td>{% if diagnostic.inventory.diversity.species_richness > 5 %}Richesse élevée{% elif diagnostic.inventory.diversity.species_richness > 2 %}Richesse moyenne{% else %}Richesse faible{% endif %}</td>
                    </tr>
                </table>
                {% endif %}
            </div>
            {% endif %}
            
            <div class="footer">
                <p>Rapport généré par ForestAI - Système de gestion forestière intelligente</p>
                <p>{{ generation_date }}</p>
            </div>
        </body>
        </html>
        """
    
    def _create_default_management_plan_template(self) -> str:
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
