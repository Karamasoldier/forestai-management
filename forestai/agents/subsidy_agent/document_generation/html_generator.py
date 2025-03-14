"""
Module pour la génération de documents HTML liés aux subventions forestières.
"""
import os
import logging
import re
from typing import Dict, List, Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from forestai.core.utils.logging_config import LoggingConfig


class HTMLGenerator:
    """
    Générateur de documents HTML pour les subventions forestières.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialise le générateur de documents HTML.
        
        Args:
            config: Dictionnaire de configuration
        """
        self.config = config
        self.templates_dir = config.get("templates_dir", "forestai/agents/subsidy_agent/templates")
        self.output_dir = config.get("output_dir", "data/outputs/subsidies")
        self.logo_path = config.get("logo_path", "forestai/agents/subsidy_agent/templates/logo.png")
        
        # Initialiser l'environnement Jinja2 pour les templates
        if os.path.exists(self.templates_dir):
            self.jinja_env = Environment(
                loader=FileSystemLoader(self.templates_dir),
                autoescape=select_autoescape(['html', 'xml'])
            )
        else:
            self.jinja_env = None
        
        # Configuration du logging
        self.logger = LoggingConfig.get_instance().get_logger(
            self.__class__.__name__,
            module=__name__
        )
        self.logger.info("Initialisation du générateur HTML")
    
    def generate_application(self, data: Dict[str, Any], output_path: str) -> str:
        """
        Génère un dossier de demande au format HTML.
        
        Args:
            data: Données pour le template
            output_path: Chemin où enregistrer le document
        
        Returns:
            Chemin du fichier généré
        """
        # Vérifier si l'environnement Jinja est disponible
        if self.jinja_env:
            try:
                template = self.jinja_env.get_template("application_template.html")
                html_content = template.render(**data)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                self.logger.info(f"Dossier de demande HTML généré: {output_path}")
                return output_path
            
            except Exception as e:
                self.logger.error(f"Erreur lors de la génération du HTML: {str(e)}")
                # Générer un HTML basic si le template échoue
                return self._generate_basic_html(data, output_path)
        else:
            # Pas de templates Jinja disponibles, générer un HTML basic
            self.logger.warning("Templates Jinja non disponibles, génération d'un HTML basic")
            return self._generate_basic_html(data, output_path)
    
    def _generate_basic_html(self, data: Dict[str, Any], output_path: str) -> str:
        """
        Génère un HTML basic pour le dossier de demande.
        
        Args:
            data: Données pour le document
            output_path: Chemin où enregistrer le document
        
        Returns:
            Chemin du fichier généré
        """
        subsidy = data["subsidy"]
        parcel = data["parcel"]
        project = data["project"]
        applicant = data["applicant"]
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Dossier de demande - {subsidy['title']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #336699; }}
        h2 {{ color: #336699; margin-top: 20px; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>Dossier de demande de subvention</h1>
    <h2>{subsidy['title']}</h2>
    <p>Document généré le {data['generated_at']}</p>
    
    <h2>Informations sur le demandeur</h2>
    <table>
        <tr><th>Nom</th><td>{applicant.get('name', '')}</td></tr>
        <tr><th>Adresse</th><td>{applicant.get('address', '')}</td></tr>
        <tr><th>Téléphone</th><td>{applicant.get('phone', '')}</td></tr>
        <tr><th>Email</th><td>{applicant.get('email', '')}</td></tr>
        <tr><th>SIRET</th><td>{applicant.get('siret', '')}</td></tr>
    </table>
    
    <h2>Informations sur la parcelle</h2>
    <table>
        <tr><th>Identifiant</th><td>{parcel.get('id', '')}</td></tr>
        <tr><th>Commune</th><td>{parcel.get('commune', '')}</td></tr>
        <tr><th>Section</th><td>{parcel.get('section', '')}</td></tr>
        <tr><th>Surface (ha)</th><td>{parcel.get('surface', 0):.2f}</td></tr>
        <tr><th>Région</th><td>{parcel.get('region', '')}</td></tr>
    </table>
    
    <h2>Informations sur le projet</h2>
    <table>
        <tr><th>Type de projet</th><td>{project.get('type', '')}</td></tr>
        <tr><th>Budget total (€)</th><td>{project.get('budget', 0):.2f}</td></tr>
        <tr><th>Objectifs</th><td>{project.get('objectives', '')}</td></tr>
        <tr><th>Date de début</th><td>{project.get('start_date', '')}</td></tr>
        <tr><th>Durée (mois)</th><td>{project.get('duration', '')}</td></tr>
    </table>
    
    <h2>Informations sur la subvention</h2>
"""
        
        if subsidy.get("description"):
            html += f"    <p><strong>Description:</strong> {subsidy['description']}</p>\n"
        
        html += f"""    <table>
        <tr><th>Source</th><td>{subsidy.get('source', '')}</td></tr>
        <tr><th>Région</th><td>{subsidy.get('region', '')}</td></tr>
        <tr><th>Taux de financement</th><td>{subsidy.get('financing_rate', '')}</td></tr>
        <tr><th>Montant min. (€)</th><td>{subsidy.get('min_amount', '')}</td></tr>
        <tr><th>Montant max. (€)</th><td>{subsidy.get('max_amount', '')}</td></tr>
        <tr><th>Date limite</th><td>{subsidy.get('application_deadline', '')}</td></tr>
    </table>
"""
        
        if subsidy.get("eligibility_criteria"):
            html += "    <h2>Critères d'éligibilité</h2>\n    <ul>\n"
            for criterion in subsidy["eligibility_criteria"]:
                html += f"        <li>{criterion}</li>\n"
            html += "    </ul>\n"
        
        if subsidy.get("contact"):
            html += f"    <p><strong>Contact pour cette subvention:</strong> {subsidy['contact']}</p>\n"
        
        if subsidy.get("url"):
            html += f"    <p><strong>Pour plus d'informations:</strong> <a href=\"{subsidy['url']}\">{subsidy['url']}</a></p>\n"
        
        html += """</body>
</html>"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        self.logger.info(f"Dossier de demande HTML basic généré: {output_path}")
        return output_path
    
    def generate_eligibility_report(self, data: Dict[str, Any], output_path: str) -> str:
        """
        Génère un rapport d'éligibilité au format HTML.
        
        Args:
            data: Données pour le template
            output_path: Chemin où enregistrer le document
        
        Returns:
            Chemin du fichier généré
        """
        # Vérifier si l'environnement Jinja est disponible
        if self.jinja_env and os.path.exists(os.path.join(self.templates_dir, "eligibility_report_template.html")):
            try:
                template = self.jinja_env.get_template("eligibility_report_template.html")
                html_content = template.render(**data)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                self.logger.info(f"Rapport d'éligibilité HTML généré: {output_path}")
                return output_path
            
            except Exception as e:
                self.logger.error(f"Erreur lors de la génération du HTML: {str(e)}")
                # Générer un HTML basic si le template échoue
                return self._generate_basic_eligibility_report(data, output_path)
        else:
            # Pas de templates Jinja disponibles, générer un HTML basic
            self.logger.warning("Templates Jinja non disponibles, génération d'un HTML basic")
            return self._generate_basic_eligibility_report(data, output_path)
    
    def _generate_basic_eligibility_report(self, data: Dict[str, Any], output_path: str) -> str:
        """
        Génère un HTML basic pour le rapport d'éligibilité.
        
        Args:
            data: Données pour le document
            output_path: Chemin où enregistrer le document
        
        Returns:
            Chemin du fichier généré
        """
        parcel = data["parcel"]
        project = data["project"]
        eligible_subsidies = data.get("eligible_subsidies", [])
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Rapport d'éligibilité aux subventions forestières</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #336699; }}
        h2 {{ color: #336699; margin-top: 20px; }}
        h3 {{ color: #336699; margin-top: 15px; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .subsidy-card {{ border: 1px solid #ddd; border-radius: 5px; padding: 15px; margin-bottom: 20px; }}
        .subsidy-title {{ background-color: #f2f2f2; padding: 10px; margin: -15px -15px 15px -15px; border-radius: 5px 5px 0 0; }}
        .score {{ font-weight: bold; color: #2a6496; }}
    </style>
</head>
<body>
    <h1>Rapport d'éligibilité aux subventions forestières</h1>
    <p>Document généré le {data['generated_at']}</p>
    
    <h2>Informations sur la parcelle</h2>
    <table>
        <tr><th>Identifiant</th><td>{parcel.get('id', '')}</td></tr>
        <tr><th>Commune</th><td>{parcel.get('commune', '')}</td></tr>
        <tr><th>Section</th><td>{parcel.get('section', '')}</td></tr>
        <tr><th>Surface (ha)</th><td>{parcel.get('surface', 0):.2f}</td></tr>
        <tr><th>Région</th><td>{parcel.get('region', '')}</td></tr>
    </table>
    
    <h2>Informations sur le projet</h2>
    <table>
        <tr><th>Type de projet</th><td>{project.get('type', '')}</td></tr>
        <tr><th>Budget total (€)</th><td>{project.get('budget', 0):.2f}</td></tr>
        <tr><th>Objectifs</th><td>{project.get('objectives', '')}</td></tr>
    </table>
    
    <h2>Subventions éligibles ({len(eligible_subsidies)})</h2>
"""
        
        if eligible_subsidies:
            # Tableau récapitulatif
            html += """    <table>
        <tr>
            <th>Subvention</th>
            <th>Source</th>
            <th>Score</th>
            <th>Montant estimé</th>
        </tr>
"""
            for idx, subsidy_result in enumerate(eligible_subsidies, 1):
                subsidy = subsidy_result["subsidy"]
                score = subsidy_result["eligibility_score"]
                amount = subsidy_result.get("estimated_amount", {}).get("estimated_amount", 0)
                
                html += f"""        <tr>
            <td>{subsidy["title"]}</td>
            <td>{subsidy.get("source", "")}</td>
            <td>{score:.2f}</td>
            <td>{amount:.2f} €</td>
        </tr>
"""
            html += "    </table>\n\n"
            
            # Détails de chaque subvention
            html += "    <h2>Détails des subventions éligibles</h2>\n\n"
            
            for idx, subsidy_result in enumerate(eligible_subsidies, 1):
                subsidy = subsidy_result["subsidy"]
                score = subsidy_result["eligibility_score"]
                reasons = subsidy_result.get("reasons", "")
                requirements = subsidy_result.get("requirements", [])
                estimated = subsidy_result.get("estimated_amount", {})
                
                html += f"""    <div class="subsidy-card">
        <div class="subsidy-title">
            <h3>{idx}. {subsidy["title"]}</h3>
        </div>
        
        <p><strong>Source:</strong> {subsidy.get("source", "")}</p>
        <p><strong>Score d'éligibilité:</strong> <span class="score">{score:.2f}</span></p>
"""
                
                if subsidy.get("description"):
                    html += f"        <p><strong>Description:</strong> {subsidy['description']}</p>\n"
                
                if estimated:
                    html += f"        <p><strong>Montant estimé:</strong> {estimated.get('estimated_amount', 0):.2f} €</p>\n"
                    if "amount_explanation" in estimated:
                        html += f"        <p><strong>Explication:</strong> {estimated['amount_explanation']}</p>\n"
                
                if reasons:
                    html += f"        <p><strong>Raisons d'éligibilité:</strong> {reasons}</p>\n"
                
                if requirements:
                    html += "        <p><strong>Exigences à respecter:</strong></p>\n        <ul>\n"
                    for req in requirements:
                        html += f"            <li>{req}</li>\n"
                    html += "        </ul>\n"
                
                if subsidy.get("contact"):
                    html += f"        <p><strong>Contact:</strong> {subsidy['contact']}</p>\n"
                
                if subsidy.get("url"):
                    html += f"""        <p><strong>Plus d'informations:</strong> <a href="{subsidy['url']}">{subsidy['url']}</a></p>
"""
                
                html += "    </div>\n\n"
        else:
            html += "    <p>Aucune subvention éligible trouvée pour ce projet.</p>\n"
        
        html += """</body>
</html>"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        self.logger.info(f"Rapport d'éligibilité HTML basic généré: {output_path}")
        return output_path
    
    def generate_subsidies_summary(self, data: Dict[str, Any], output_path: str) -> str:
        """
        Génère une synthèse des subventions disponibles au format HTML.
        
        Args:
            data: Données pour le template
            output_path: Chemin où enregistrer le document
        
        Returns:
            Chemin du fichier généré
        """
        # Vérifier si l'environnement Jinja est disponible
        if self.jinja_env and os.path.exists(os.path.join(self.templates_dir, "subsidies_summary_template.html")):
            try:
                template = self.jinja_env.get_template("subsidies_summary_template.html")
                html_content = template.render(**data)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                self.logger.info(f"Synthèse des subventions HTML générée: {output_path}")
                return output_path
            
            except Exception as e:
                self.logger.error(f"Erreur lors de la génération du HTML: {str(e)}")
                # Générer un HTML basic si le template échoue
                return self._generate_basic_subsidies_summary(data, output_path)
        else:
            # Pas de templates Jinja disponibles, générer un HTML basic
            self.logger.warning("Templates Jinja non disponibles, génération d'un HTML basic")
            return self._generate_basic_subsidies_summary(data, output_path)
    
    def _generate_basic_subsidies_summary(self, data: Dict[str, Any], output_path: str) -> str:
        """
        Génère un HTML basic pour la synthèse des subventions.
        
        Args:
            data: Données pour le document
            output_path: Chemin où enregistrer le document
        
        Returns:
            Chemin du fichier généré
        """
        subsidies = data.get("subsidies", [])
        filters = data.get("filters", {})
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Synthèse des subventions forestières</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #336699; }}
        h2 {{ color: #336699; margin-top: 20px; }}
        h3 {{ color: #336699; margin-top: 15px; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .subsidy-card {{ border: 1px solid #ddd; border-radius: 5px; padding: 15px; margin-bottom: 20px; }}
        .subsidy-title {{ background-color: #f2f2f2; padding: 10px; margin: -15px -15px 15px -15px; border-radius: 5px 5px 0 0; }}
        .filters {{ background-color: #f9f9f9; padding: 10px; border-radius: 5px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <h1>Synthèse des subventions forestières ({len(subsidies)})</h1>
    <p>Document généré le {data['generated_at']}</p>
"""
        
        # Filtres appliqués
        if filters:
            html += """    <div class="filters">
        <h2>Filtres appliqués</h2>
        <ul>
"""
            if "region" in filters:
                html += f"            <li><strong>Région:</strong> {filters['region']}</li>\n"
            if "project_type" in filters:
                html += f"            <li><strong>Type de projet:</strong> {filters['project_type']}</li>\n"
            if "min_amount" in filters:
                html += f"            <li><strong>Montant minimum:</strong> {filters['min_amount']} €</li>\n"
            if "keywords" in filters and filters["keywords"]:
                html += f"            <li><strong>Mots-clés:</strong> {', '.join(filters['keywords'])}</li>\n"
            
            html += """        </ul>
    </div>
"""
        
        # Liste des subventions
        if subsidies:
            # Tableau récapitulatif
            html += """    <h2>Récapitulatif des subventions</h2>
    <table>
        <tr>
            <th>Subvention</th>
            <th>Source</th>
            <th>Région</th>
            <th>Taux</th>
            <th>Montant max.</th>
        </tr>
"""
            for subsidy in subsidies:
                html += f"""        <tr>
            <td>{subsidy["title"]}</td>
            <td>{subsidy.get("source", "")}</td>
            <td>{subsidy.get("region", "")}</td>
            <td>{subsidy.get("financing_rate", "")}</td>
            <td>{f"{subsidy.get('max_amount', '')} €" if subsidy.get('max_amount') else ""}</td>
        </tr>
"""
            html += "    </table>\n\n"
            
            # Détails de chaque subvention
            html += "    <h2>Détails des subventions</h2>\n\n"
            
            for idx, subsidy in enumerate(subsidies, 1):
                html += f"""    <div class="subsidy-card">
        <div class="subsidy-title">
            <h3>{idx}. {subsidy["title"]}</h3>
        </div>
        
        <p><strong>Source:</strong> {subsidy.get("source", "")}</p>
        <p><strong>Région:</strong> {subsidy.get("region", "")}</p>
"""
                
                if subsidy.get("description"):
                    html += f"        <p><strong>Description:</strong> {subsidy['description']}</p>\n"
                
                # Financement
                financing_info = []
                if subsidy.get("financing_rate"):
                    financing_info.append(f"Taux de financement: {subsidy['financing_rate']}")
                if subsidy.get("min_amount"):
                    financing_info.append(f"Montant minimum: {subsidy['min_amount']} €")
                if subsidy.get("max_amount"):
                    financing_info.append(f"Montant maximum: {subsidy['max_amount']} €")
                
                if financing_info:
                    html += "        <p><strong>Financement:</strong></p>\n        <ul>\n"
                    for info in financing_info:
                        html += f"            <li>{info}</li>\n"
                    html += "        </ul>\n"
                
                if subsidy.get("eligible_projects"):
                    html += f"        <p><strong>Projets éligibles:</strong> {subsidy['eligible_projects']}</p>\n"
                
                if subsidy.get("application_deadline"):
                    html += f"        <p><strong>Date limite:</strong> {subsidy['application_deadline']}</p>\n"
                
                if subsidy.get("contact"):
                    html += f"        <p><strong>Contact:</strong> {subsidy['contact']}</p>\n"
                
                if subsidy.get("url"):
                    html += f"""        <p><strong>Plus d'informations:</strong> <a href="{subsidy['url']}">{subsidy['url']}</a></p>
"""
                
                html += "    </div>\n\n"
        else:
            html += "    <p>Aucune subvention disponible correspondant aux critères.</p>\n"
        
        html += """</body>
</html>"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        self.logger.info(f"Synthèse des subventions HTML basic générée: {output_path}")
        return output_path
