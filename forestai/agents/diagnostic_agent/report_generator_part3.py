    def generate_management_plan_report_pdf(self, plan: Dict[str, Any], diagnostic: Optional[Dict[str, Any]] = None) -> bytes:
        """Génère un rapport de plan de gestion au format PDF.
        
        Args:
            plan: Données du plan de gestion
            diagnostic: Données du diagnostic associé (optionnel)
            
        Returns:
            Contenu PDF en bytes
        """
        try:
            # Générer d'abord le HTML
            html = self.generate_management_plan_report_html(plan, diagnostic)
            
            # Convertir HTML en PDF avec WeasyPrint
            import weasyprint
            pdf = weasyprint.HTML(string=html).write_pdf()
            
            return pdf
            
        except ImportError:
            logger.warning("WeasyPrint non disponible, tentative avec pdfkit")
            try:
                # Essayer avec pdfkit comme alternative
                import pdfkit
                html = self.generate_management_plan_report_html(plan, diagnostic)
                pdf = pdfkit.from_string(html, False)
                return pdf
                
            except ImportError:
                logger.error("Ni WeasyPrint ni pdfkit ne sont disponibles")
                # Retourner une erreur en PDF généré avec reportlab
                from reportlab.pdfgen import canvas
                from reportlab.lib.pagesizes import A4
                from io import BytesIO
                
                buffer = BytesIO()
                c = canvas.Canvas(buffer, pagesize=A4)
                c.drawString(100, 800, "Erreur de génération du rapport")
                c.drawString(100, 780, "Aucune librairie de conversion HTML vers PDF n'est disponible")
                c.drawString(100, 760, "Veuillez installer WeasyPrint ou pdfkit")
                c.save()
                pdf = buffer.getvalue()
                buffer.close()
                return pdf
                
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport PDF: {str(e)}")
            # Générer un PDF d'erreur avec reportlab
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4
            from io import BytesIO
            
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            c.drawString(100, 800, "Erreur de génération du rapport")
            c.drawString(100, 780, f"Erreur: {str(e)}")
            c.save()
            pdf = buffer.getvalue()
            buffer.close()
            return pdf
    
    def _generate_diagnostic_graphs(self, diagnostic: Dict[str, Any]) -> Dict[str, str]:
        """Génère des graphiques pour le rapport de diagnostic.
        
        Args:
            diagnostic: Données du diagnostic
            
        Returns:
            Dictionnaire des graphiques en base64
        """
        graphs = {}
        
        try:
            # Graphique de recommandation d'espèces
            if 'species_recommendations' in diagnostic and 'recommended_species' in diagnostic['species_recommendations']:
                species_data = diagnostic['species_recommendations']['recommended_species']
                if species_data and len(species_data) > 0:
                    species_names = [item['species_name'] for item in species_data[:5]]  # Top 5 species
                    suitability_scores = [item['overall_suitability'] * 100 for item in species_data[:5]]
                    
                    plt.figure(figsize=(10, 6))
                    bars = plt.bar(species_names, suitability_scores, color='forestgreen')
                    plt.xlabel('Espèces')
                    plt.ylabel('Score d\'adéquation (%)')
                    plt.title('Espèces recommandées pour la parcelle')
                    plt.xticks(rotation=45, ha='right')
                    plt.tight_layout()
                    
                    # Ajouter les valeurs au-dessus des barres
                    for bar in bars:
                        height = bar.get_height()
                        plt.text(bar.get_x() + bar.get_width()/2., height + 1, f'{height:.1f}%',
                                ha='center', va='bottom', rotation=0)
                    
                    # Convertir en base64
                    buffer = io.BytesIO()
                    plt.savefig(buffer, format='png')
                    plt.close()
                    buffer.seek(0)
                    image_png = buffer.getvalue()
                    buffer.close()
                    encoded = base64.b64encode(image_png).decode('utf-8')
                    graphs['species_recommendations'] = f"data:image/png;base64,{encoded}"
            
            # Graphique de potentiel forestier
            if 'potential' in diagnostic and isinstance(diagnostic['potential'], dict):
                potential_data = diagnostic['potential']
                metrics = []
                values = []
                
                for key, value in potential_data.items():
                    if isinstance(value, (int, float)) and 'score' in key.lower():
                        metrics.append(key.replace('_', ' ').title())
                        values.append(value * 100 if value <= 1 else value)  # Convertir en % si nécessaire
                
                if metrics and values:
                    plt.figure(figsize=(10, 6))
                    bars = plt.bar(metrics, values, color='cornflowerblue')
                    plt.xlabel('Métriques')
                    plt.ylabel('Score (%)')
                    plt.title('Potentiel forestier de la parcelle')
                    plt.xticks(rotation=45, ha='right')
                    plt.tight_layout()
                    
                    # Ajouter les valeurs au-dessus des barres
                    for bar in bars:
                        height = bar.get_height()
                        plt.text(bar.get_x() + bar.get_width()/2., height + 1, f'{height:.1f}%',
                                ha='center', va='bottom', rotation=0)
                    
                    # Convertir en base64
                    buffer = io.BytesIO()
                    plt.savefig(buffer, format='png')
                    plt.close()
                    buffer.seek(0)
                    image_png = buffer.getvalue()
                    buffer.close()
                    encoded = base64.b64encode(image_png).decode('utf-8')
                    graphs['potential'] = f"data:image/png;base64,{encoded}"
            
            # Graphique de climat (si disponible)
            if 'climate' in diagnostic and 'data' in diagnostic['climate']:
                climate_data = diagnostic['climate']['data']
                if isinstance(climate_data, dict):
                    # Extraire des données climatiques pour plotting
                    if 'temperature' in climate_data and 'precipitation' in climate_data:
                        temp_data = climate_data['temperature']
                        precip_data = climate_data['precipitation']
                        
                        if isinstance(temp_data, dict) and isinstance(precip_data, dict) and 'monthly' in temp_data and 'monthly' in precip_data:
                            months = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sep", "Oct", "Nov", "Déc"]
                            temps = temp_data['monthly']
                            precips = precip_data['monthly']
                            
                            fig, ax1 = plt.subplots(figsize=(10, 6))
                            
                            # Températures
                            ax1.set_xlabel('Mois')
                            ax1.set_ylabel('Température (°C)', color='tab:red')
                            ax1.plot(months, temps, color='tab:red', marker='o')
                            ax1.tick_params(axis='y', labelcolor='tab:red')
                            
                            # Précipitations sur l'axe secondaire
                            ax2 = ax1.twinx()
                            ax2.set_ylabel('Précipitations (mm)', color='tab:blue')
                            ax2.bar(months, precips, color='tab:blue', alpha=0.5)
                            ax2.tick_params(axis='y', labelcolor='tab:blue')
                            
                            plt.title('Climat mensuel moyen')
                            plt.xticks(rotation=45)
                            plt.tight_layout()
                            
                            # Convertir en base64
                            buffer = io.BytesIO()
                            plt.savefig(buffer, format='png')
                            plt.close()
                            buffer.seek(0)
                            image_png = buffer.getvalue()
                            buffer.close()
                            encoded = base64.b64encode(image_png).decode('utf-8')
                            graphs['climate'] = f"data:image/png;base64,{encoded}"