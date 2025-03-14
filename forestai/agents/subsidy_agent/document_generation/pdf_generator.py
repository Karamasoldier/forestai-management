"""
Module pour la génération de documents PDF liés aux subventions forestières.
"""
import os
import logging
from typing import Dict, List, Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
import pdfkit
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

from forestai.core.utils.logging_config import LoggingConfig


class PDFGenerator:
    """
    Générateur de documents PDF pour les subventions forestières.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialise le générateur de documents PDF.
        
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
        self.logger.info("Initialisation du générateur PDF")
    
    def generate_application(self, data: Dict[str, Any], output_path: str) -> str:
        """
        Génère un dossier de demande au format PDF.
        
        Args:
            data: Données pour le template
            output_path: Chemin où enregistrer le document
        
        Returns:
            Chemin du fichier généré
        """
        # Vérifier si l'environnement Jinja est disponible
        if self.jinja_env:
            # Générer d'abord le HTML avec Jinja
            try:
                template = self.jinja_env.get_template("application_template.html")
                html_content = template.render(**data)
                
                # Convertir le HTML en PDF avec pdfkit (nécessite wkhtmltopdf)
                try:
                    pdfkit.from_string(html_content, output_path)
                    self.logger.info(f"Dossier de demande PDF généré: {output_path}")
                    return output_path
                except Exception as e:
                    self.logger.error(f"Erreur lors de la conversion HTML->PDF: {str(e)}")
                    # Fallback à ReportLab si pdfkit échoue
                    return self._generate_with_reportlab(data, output_path)
            
            except Exception as e:
                self.logger.error(f"Erreur lors de la génération du template HTML: {str(e)}")
                # Fallback à ReportLab
                return self._generate_with_reportlab(data, output_path)
        else:
            # Pas de templates Jinja disponibles, utiliser ReportLab directement
            self.logger.warning("Templates Jinja non disponibles, utilisation de ReportLab")
            return self._generate_with_reportlab(data, output_path)
    
    def _generate_with_reportlab(self, data: Dict[str, Any], output_path: str) -> str:
        """
        Génère un dossier de demande au format PDF avec ReportLab.
        
        Args:
            data: Données pour le document
            output_path: Chemin où enregistrer le document
        
        Returns:
            Chemin du fichier généré
        """
        self.logger.info("Génération du PDF avec ReportLab")
        
        # Préparer le document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        # Styles personnalisés
        styles.add(ParagraphStyle(
            name='Title',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=12
        ))
        styles.add(ParagraphStyle(
            name='Subtitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=10
        ))
        styles.add(ParagraphStyle(
            name='Normal',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=6
        ))
        
        # Ajouter un logo si disponible
        if data.get("logo_path") and os.path.exists(data["logo_path"]):
            logo = Image(data["logo_path"], width=5*cm, height=2*cm)
            story.append(logo)
            story.append(Spacer(1, 1*cm))
        
        # Titre du document
        subsidy = data["subsidy"]
        story.append(Paragraph(f"Dossier de demande de subvention", styles['Title']))
        story.append(Paragraph(f"{subsidy['title']}", styles['Subtitle']))
        story.append(Spacer(1, 0.5*cm))
        
        # Date de génération
        story.append(Paragraph(f"Document généré le {data['generated_at']}", styles['Normal']))
        story.append(Spacer(1, 1*cm))
        
        # Informations sur le demandeur
        applicant = data["applicant"]
        story.append(Paragraph("Informations sur le demandeur", styles['Subtitle']))
        
        # Tableau des informations du demandeur
        applicant_data = [
            ["Nom", applicant.get("name", "")],
            ["Adresse", applicant.get("address", "")],
            ["Téléphone", applicant.get("phone", "")],
            ["Email", applicant.get("email", "")],
            ["SIRET", applicant.get("siret", "")]
        ]
        
        applicant_table = Table(applicant_data, colWidths=[5*cm, 10*cm])
        applicant_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6)
        ]))
        
        story.append(applicant_table)
        story.append(Spacer(1, 0.5*cm))
        
        # Informations sur la parcelle
        parcel = data["parcel"]
        story.append(Paragraph("Informations sur la parcelle", styles['Subtitle']))
        
        # Tableau des informations de la parcelle
        parcel_data = [
            ["Identifiant", parcel.get("id", "")],
            ["Commune", parcel.get("commune", "")],
            ["Section", parcel.get("section", "")],
            ["Surface (ha)", f"{parcel.get('surface', 0):.2f}"],
            ["Région", parcel.get("region", "")]
        ]
        
        parcel_table = Table(parcel_data, colWidths=[5*cm, 10*cm])
        parcel_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6)
        ]))
        
        story.append(parcel_table)
        story.append(Spacer(1, 0.5*cm))
        
        # Informations sur le projet
        project = data["project"]
        story.append(Paragraph("Informations sur le projet", styles['Subtitle']))
        
        # Tableau des informations du projet
        project_data = [
            ["Type de projet", project.get("type", "")],
            ["Budget total (€)", f"{project.get('budget', 0):.2f}"],
            ["Objectifs", project.get("objectives", "")],
            ["Date de début", project.get("start_date", "")],
            ["Durée (mois)", project.get("duration", "")]
        ]
        
        project_table = Table(project_data, colWidths=[5*cm, 10*cm])
        project_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6)
        ]))
        
        story.append(project_table)
        story.append(Spacer(1, 0.5*cm))
        
        # Informations sur la subvention
        story.append(Paragraph("Informations sur la subvention", styles['Subtitle']))
        
        # Description de la subvention
        if subsidy.get("description"):
            story.append(Paragraph("Description:", styles['Normal']))
            story.append(Paragraph(subsidy["description"], styles['Normal']))
            story.append(Spacer(1, 0.3*cm))
        
        # Tableau des informations de la subvention
        subsidy_data = [
            ["Source", subsidy.get("source", "")],
            ["Région", subsidy.get("region", "")],
            ["Taux de financement", subsidy.get("financing_rate", "")],
            ["Montant min. (€)", str(subsidy.get("min_amount", "")) if subsidy.get("min_amount") else ""],
            ["Montant max. (€)", str(subsidy.get("max_amount", "")) if subsidy.get("max_amount") else ""],
            ["Date limite", subsidy.get("application_deadline", "")]
        ]
        
        subsidy_table = Table(subsidy_data, colWidths=[5*cm, 10*cm])
        subsidy_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6)
        ]))
        
        story.append(subsidy_table)
        story.append(Spacer(1, 0.5*cm))
        
        # Critères d'éligibilité
        if subsidy.get("eligibility_criteria"):
            story.append(Paragraph("Critères d'éligibilité:", styles['Subtitle']))
            for criterion in subsidy["eligibility_criteria"]:
                story.append(Paragraph(f"• {criterion}", styles['Normal']))
            story.append(Spacer(1, 0.5*cm))
        
        # Contact pour la subvention
        if subsidy.get("contact"):
            story.append(Paragraph("Contact pour cette subvention:", styles['Normal']))
            story.append(Paragraph(subsidy["contact"], styles['Normal']))
            story.append(Spacer(1, 0.5*cm))
        
        # URL pour plus d'informations
        if subsidy.get("url"):
            story.append(Paragraph("Pour plus d'informations:", styles['Normal']))
            story.append(Paragraph(subsidy["url"], styles['Normal']))
        
        # Générer le PDF
        doc.build(story)
        
        self.logger.info(f"Dossier de demande PDF généré avec ReportLab: {output_path}")
        return output_path

    def generate_eligibility_report(self, data: Dict[str, Any], output_path: str) -> str:
        """
        Génère un rapport d'éligibilité au format PDF.
        
        Args:
            data: Données pour le template
            output_path: Chemin où enregistrer le document
        
        Returns:
            Chemin du fichier généré
        """
        # Fonction similaire à generate_application mais adaptée aux rapports d'éligibilité
        # Utiliser ReportLab directement pour simplifier
        self.logger.info("Génération du rapport d'éligibilité PDF")
        
        # Préparer le document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        # Styles personnalisés
        styles.add(ParagraphStyle(
            name='Title',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=12
        ))
        styles.add(ParagraphStyle(
            name='Subtitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=10
        ))
        styles.add(ParagraphStyle(
            name='Normal',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=6
        ))
        
        # Ajouter un logo si disponible
        if data.get("logo_path") and os.path.exists(data["logo_path"]):
            logo = Image(data["logo_path"], width=5*cm, height=2*cm)
            story.append(logo)
            story.append(Spacer(1, 1*cm))
        
        # Titre du document
        story.append(Paragraph("Rapport d'éligibilité aux subventions forestières", styles['Title']))
        story.append(Spacer(1, 0.5*cm))
        
        # Date de génération
        story.append(Paragraph(f"Document généré le {data['generated_at']}", styles['Normal']))
        story.append(Spacer(1, 1*cm))
        
        # Informations sur la parcelle
        parcel = data["parcel"]
        story.append(Paragraph("Informations sur la parcelle", styles['Subtitle']))
        
        # Tableau des informations de la parcelle
        parcel_data = [
            ["Identifiant", parcel.get("id", "")],
            ["Commune", parcel.get("commune", "")],
            ["Section", parcel.get("section", "")],
            ["Surface (ha)", f"{parcel.get('surface', 0):.2f}"],
            ["Région", parcel.get("region", "")]
        ]
        
        parcel_table = Table(parcel_data, colWidths=[5*cm, 10*cm])
        parcel_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6)
        ]))
        
        story.append(parcel_table)
        story.append(Spacer(1, 0.5*cm))
        
        # Informations sur le projet
        project = data["project"]
        story.append(Paragraph("Informations sur le projet", styles['Subtitle']))
        
        # Tableau des informations du projet
        project_data = [
            ["Type de projet", project.get("type", "")],
            ["Budget total (€)", f"{project.get('budget', 0):.2f}"],
            ["Objectifs", project.get("objectives", "")]
        ]
        
        project_table = Table(project_data, colWidths=[5*cm, 10*cm])
        project_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6)
        ]))
        
        story.append(project_table)
        story.append(Spacer(1, 0.5*cm))
        
        # Résumé des subventions éligibles
        eligible_subsidies = data.get("eligible_subsidies", [])
        story.append(Paragraph(f"Subventions éligibles ({len(eligible_subsidies)})", styles['Subtitle']))
        
        if eligible_subsidies:
            # Tableau récapitulatif
            headers = ["Subvention", "Source", "Score", "Montant estimé"]
            table_data = [headers]
            
            for idx, subsidy_result in enumerate(eligible_subsidies, 1):
                subsidy = subsidy_result["subsidy"]
                score = subsidy_result["eligibility_score"]
                amount = subsidy_result.get("estimated_amount", {}).get("estimated_amount", 0)
                
                row = [
                    subsidy["title"],
                    subsidy.get("source", ""),
                    f"{score:.2f}",
                    f"{amount:.2f} €"
                ]
                table_data.append(row)
            
            # Créer le tableau
            summary_table = Table(table_data, colWidths=[7*cm, 3*cm, 2*cm, 3*cm])
            summary_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('PADDING', (0, 0), (-1, -1), 6)
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 0.5*cm))
            
            # Détails de chaque subvention
            story.append(Paragraph("Détails des subventions éligibles", styles['Subtitle']))
            
            for idx, subsidy_result in enumerate(eligible_subsidies, 1):
                subsidy = subsidy_result["subsidy"]
                score = subsidy_result["eligibility_score"]
                reasons = subsidy_result.get("reasons", "")
                requirements = subsidy_result.get("requirements", [])
                estimated = subsidy_result.get("estimated_amount", {})
                
                # Titre de la subvention
                story.append(Paragraph(f"{idx}. {subsidy['title']}", styles['Subtitle']))
                story.append(Spacer(1, 0.2*cm))
                
                # Source et score
                story.append(Paragraph(f"Source: {subsidy.get('source', '')}", styles['Normal']))
                story.append(Paragraph(f"Score d'éligibilité: {score:.2f}", styles['Normal']))
                story.append(Spacer(1, 0.2*cm))
                
                # Description
                if subsidy.get("description"):
                    story.append(Paragraph("Description:", styles['Normal']))
                    story.append(Paragraph(subsidy["description"], styles['Normal']))
                    story.append(Spacer(1, 0.2*cm))
                
                # Montant estimé
                if estimated:
                    story.append(Paragraph("Montant estimé:", styles['Normal']))
                    story.append(Paragraph(f"{estimated.get('estimated_amount', 0):.2f} €", styles['Normal']))
                    if "amount_explanation" in estimated:
                        story.append(Paragraph(estimated["amount_explanation"], styles['Normal']))
                    story.append(Spacer(1, 0.2*cm))
                
                # Raisons d'éligibilité
                if reasons:
                    story.append(Paragraph("Raisons d'éligibilité:", styles['Normal']))
                    story.append(Paragraph(reasons, styles['Normal']))
                    story.append(Spacer(1, 0.2*cm))
                
                # Exigences
                if requirements:
                    story.append(Paragraph("Exigences à respecter:", styles['Normal']))
                    for req in requirements:
                        story.append(Paragraph(f"• {req}", styles['Normal']))
                    story.append(Spacer(1, 0.2*cm))
                
                # Informations de contact
                if subsidy.get("contact"):
                    story.append(Paragraph(f"Contact: {subsidy['contact']}", styles['Normal']))
                
                # URL
                if subsidy.get("url"):
                    story.append(Paragraph(f"Plus d'informations: {subsidy['url']}", styles['Normal']))
                
                story.append(Spacer(1, 0.5*cm))
        else:
            story.append(Paragraph("Aucune subvention éligible trouvée pour ce projet.", styles['Normal']))
        
        # Générer le PDF
        doc.build(story)
        
        self.logger.info(f"Rapport d'éligibilité PDF généré: {output_path}")
        return output_path

    def generate_subsidies_summary(self, data: Dict[str, Any], output_path: str) -> str:
        """
        Génère une synthèse des subventions disponibles au format PDF.
        
        Args:
            data: Données pour le template
            output_path: Chemin où enregistrer le document
        
        Returns:
            Chemin du fichier généré
        """
        self.logger.info("Génération de la synthèse des subventions PDF")
        
        # Préparer le document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        # Styles personnalisés
        styles.add(ParagraphStyle(
            name='Title',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=12
        ))
        styles.add(ParagraphStyle(
            name='Subtitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=10
        ))
        styles.add(ParagraphStyle(
            name='Normal',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=6
        ))
        
        # Ajouter un logo si disponible
        if data.get("logo_path") and os.path.exists(data["logo_path"]):
            logo = Image(data["logo_path"], width=5*cm, height=2*cm)
            story.append(logo)
            story.append(Spacer(1, 1*cm))
        
        # Titre du document
        subsidies = data.get("subsidies", [])
        story.append(Paragraph(f"Synthèse des subventions forestières ({len(subsidies)})", styles['Title']))
        story.append(Spacer(1, 0.5*cm))
        
        # Date de génération
        story.append(Paragraph(f"Document généré le {data['generated_at']}", styles['Normal']))
        story.append(Spacer(1, 0.5*cm))
        
        # Filtres appliqués
        filters = data.get("filters", {})
        if filters:
            story.append(Paragraph("Filtres appliqués:", styles['Subtitle']))
            filter_items = []
            if "region" in filters:
                filter_items.append(f"Région: {filters['region']}")
            if "project_type" in filters:
                filter_items.append(f"Type de projet: {filters['project_type']}")
            if "min_amount" in filters:
                filter_items.append(f"Montant minimum: {filters['min_amount']} €")
            if "keywords" in filters and filters["keywords"]:
                filter_items.append(f"Mots-clés: {', '.join(filters['keywords'])}")
            
            for item in filter_items:
                story.append(Paragraph(f"• {item}", styles['Normal']))
            
            story.append(Spacer(1, 0.5*cm))
        
        # Liste des subventions
        if subsidies:
            # Tableau récapitulatif
            headers = ["Subvention", "Source", "Région", "Taux", "Montant max."]
            table_data = [headers]
            
            for subsidy in subsidies:
                row = [
                    subsidy["title"],
                    subsidy.get("source", ""),
                    subsidy.get("region", ""),
                    subsidy.get("financing_rate", ""),
                    f"{subsidy.get('max_amount', '')} €" if subsidy.get('max_amount') else ""
                ]
                table_data.append(row)
            
            # Créer le tableau
            summary_table = Table(table_data, colWidths=[5*cm, 3*cm, 3*cm, 2*cm, 2*cm])
            summary_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('PADDING', (0, 0), (-1, -1), 6)
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 0.5*cm))
            
            # Détails de chaque subvention
            story.append(Paragraph("Détails des subventions", styles['Subtitle']))
            
            for idx, subsidy in enumerate(subsidies, 1):
                # Titre de la subvention
                story.append(Paragraph(f"{idx}. {subsidy['title']}", styles['Subtitle']))
                story.append(Spacer(1, 0.2*cm))
                
                # Source et région
                story.append(Paragraph(f"Source: {subsidy.get('source', '')}", styles['Normal']))
                story.append(Paragraph(f"Région: {subsidy.get('region', '')}", styles['Normal']))
                story.append(Spacer(1, 0.2*cm))
                
                # Description
                if subsidy.get("description"):
                    story.append(Paragraph("Description:", styles['Normal']))
                    story.append(Paragraph(subsidy["description"], styles['Normal']))
                    story.append(Spacer(1, 0.2*cm))
                
                # Financement
                financing_info = []
                if subsidy.get("financing_rate"):
                    financing_info.append(f"Taux de financement: {subsidy['financing_rate']}")
                if subsidy.get("min_amount"):
                    financing_info.append(f"Montant minimum: {subsidy['min_amount']} €")
                if subsidy.get("max_amount"):
                    financing_info.append(f"Montant maximum: {subsidy['max_amount']} €")
                if financing_info:
                    story.append(Paragraph("Financement:", styles['Normal']))
                    for info in financing_info:
                        story.append(Paragraph(f"• {info}", styles['Normal']))
                    story.append(Spacer(1, 0.2*cm))
                
                # Projets éligibles
                if subsidy.get("eligible_projects"):
                    story.append(Paragraph("Projets éligibles:", styles['Normal']))
                    story.append(Paragraph(subsidy["eligible_projects"], styles['Normal']))
                    story.append(Spacer(1, 0.2*cm))
                
                # Date limite
                if subsidy.get("application_deadline"):
                    story.append(Paragraph(f"Date limite: {subsidy['application_deadline']}", styles['Normal']))
                    story.append(Spacer(1, 0.2*cm))
                
                # Contact et URL
                if subsidy.get("contact"):
                    story.append(Paragraph(f"Contact: {subsidy['contact']}", styles['Normal']))
                if subsidy.get("url"):
                    story.append(Paragraph(f"Plus d'informations: {subsidy['url']}", styles['Normal']))
                
                story.append(Spacer(1, 0.5*cm))
        else:
            story.append(Paragraph("Aucune subvention disponible correspondant aux critères.", styles['Normal']))
        
        # Générer le PDF
        doc.build(story)
        
        self.logger.info(f"Synthèse des subventions PDF générée: {output_path}")
        return output_path
