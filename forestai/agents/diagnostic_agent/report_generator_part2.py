    def generate_diagnostic_report_pdf(self, diagnostic: Dict[str, Any], parcel_data: Optional[Dict[str, Any]] = None) -> bytes:
        """Génère un rapport de diagnostic forestier au format PDF.
        
        Args:
            diagnostic: Données du diagnostic forestier
            parcel_data: Données supplémentaires sur la parcelle (optionnel)
            
        Returns:
            Contenu PDF en bytes
        """
        try:
            # Générer d'abord le HTML
            html = self.generate_diagnostic_report_html(diagnostic, parcel_data)
            
            # Convertir HTML en PDF avec WeasyPrint
            import weasyprint
            pdf = weasyprint.HTML(string=html).write_pdf()
            
            return pdf
            
        except ImportError:
            logger.warning("WeasyPrint non disponible, tentative avec pdfkit")
            try:
                # Essayer avec pdfkit comme alternative
                import pdfkit
                html = self.generate_diagnostic_report_html(diagnostic, parcel_data)
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
    
    def generate_management_plan_report_html(self, plan: Dict[str, Any], diagnostic: Optional[Dict[str, Any]] = None) -> str:
        """Génère un rapport de plan de gestion au format HTML.
        
        Args:
            plan: Données du plan de gestion
            diagnostic: Données du diagnostic associé (optionnel)
            
        Returns:
            Rapport HTML
        """
        try:
            # Charger le modèle
            template = self.jinja_env.get_template('management_plan_report.html')
            if template is None:
                # Si le modèle n'existe pas, créer un modèle par défaut
                template_str = self._create_default_management_plan_template()
                template = self.jinja_env.from_string(template_str)
            
            # Générer des graphiques
            graphs = self._generate_management_plan_graphs(plan, diagnostic)
            
            # Préparer le contexte
            context = {
                'plan': plan,
                'diagnostic': diagnostic or {},
                'graphs': graphs,
                'generation_date': datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
                'report_id': f"PLAN-{plan.get('parcel_id', 'UNKNOWN')}-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            }
            
            # Générer le HTML
            html = template.render(**context)
            
            return html
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport HTML: {str(e)}")
            # Générer un rapport d'erreur simple
            error_html = f"""<html>
            <head><title>Erreur de génération du rapport</title></head>
            <body>
                <h1>Erreur lors de la génération du rapport</h1>
                <p>Une erreur est survenue: {str(e)}</p>
                <h2>Données du plan de gestion brutes:</h2>
                <pre>{json.dumps(plan, indent=2)}</pre>
            </body>
            </html>"""
            return error_html