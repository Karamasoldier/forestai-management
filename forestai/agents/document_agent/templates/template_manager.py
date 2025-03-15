# -*- coding: utf-8 -*-
"""
Gestionnaire de templates pour le DocumentAgent.

Ce module fournit les fonctionnalités pour charger, valider et rendre
des templates de documents forestiers.
"""

import os
import json
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from jinja2 import Environment, FileSystemLoader, select_autoescape, Template

from forestai.agents.document_agent.models.document_models import (
    DocumentType, 
    DocumentFormat, 
    TemplateDefinition,
    TemplateVariable
)

logger = logging.getLogger(__name__)

class TemplateManager:
    """
    Gestionnaire de templates pour les documents forestiers.
    
    Cette classe s'occupe du chargement, de la validation et du rendu des templates
    utilisés pour générer des documents administratifs forestiers.
    """
    
    def __init__(self, templates_dir: Optional[str] = None):
        """
        Initialise le gestionnaire de templates.
        
        Args:
            templates_dir: Répertoire contenant les templates (par défaut: templates/)
        """
        # Définir le répertoire des templates
        if templates_dir is None:
            # Utiliser un répertoire par défaut relatif à l'emplacement actuel
            templates_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), 
                "template_files"
            )
        
        self.templates_dir = Path(templates_dir)
        if not self.templates_dir.exists():
            logger.info(f"Création du répertoire de templates: {self.templates_dir}")
            self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Définir les sous-répertoires par type de document
        self.contract_dir = self.templates_dir / "contracts"
        self.specification_dir = self.templates_dir / "specifications"
        self.management_plan_dir = self.templates_dir / "management_plans"
        self.administrative_dir = self.templates_dir / "administrative"
        self.custom_dir = self.templates_dir / "custom"
        
        # Créer les sous-répertoires s'ils n'existent pas
        for directory in [self.contract_dir, self.specification_dir, 
                         self.management_plan_dir, self.administrative_dir,
                         self.custom_dir]:
            directory.mkdir(exist_ok=True)
        
        # Initialiser l'environnement Jinja2
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Ajouter des filtres personnalisés
        self._add_custom_filters()
        
        # Charger les définitions des templates
        self.templates = self._load_template_definitions()
        
        logger.info(f"TemplateManager initialisé avec {len(self.templates)} templates dans {self.templates_dir}")
    
    def _add_custom_filters(self):
        """Ajoute des filtres personnalisés à l'environnement Jinja2."""
        
        # Filtre pour formater les dates
        def format_date(date, format_str="%d/%m/%Y"):
            """Formate une date selon le format spécifié."""
            if hasattr(date, 'strftime'):
                return date.strftime(format_str)
            return date
        
        # Filtre pour formater les nombres
        def format_number(number, decimal_places=2, thousands_sep=" "):
            """Formate un nombre avec séparateur de milliers et décimales."""
            try:
                return f"{float(number):,.{decimal_places}f}".replace(",", thousands_sep)
            except (ValueError, TypeError):
                return number
        
        # Filtre pour formater les surfaces
        def format_area(area_ha, decimal_places=2):
            """Formate une surface en hectares."""
            try:
                area = float(area_ha)
                if area < 0.01:
                    # Convertir en m²
                    return f"{area * 10000:.0f} m²"
                else:
                    return f"{area:,.{decimal_places}f} ha".replace(",", " ")
            except (ValueError, TypeError):
                return area_ha
        
        # Enregistrer les filtres
        self.jinja_env.filters['format_date'] = format_date
        self.jinja_env.filters['format_number'] = format_number
        self.jinja_env.filters['format_area'] = format_area
    
    def _load_template_definitions(self) -> Dict[str, TemplateDefinition]:
        """
        Charge les définitions de tous les templates disponibles.
        
        Returns:
            Dictionnaire des définitions de templates indexé par ID
        """
        templates = {}
        
        # Parcourir tous les répertoires de templates
        for doc_type_dir in [self.contract_dir, self.specification_dir, 
                            self.management_plan_dir, self.administrative_dir,
                            self.custom_dir]:
            
            # Chercher les fichiers de définition de template (YAML ou JSON)
            for def_file in doc_type_dir.glob("**/*.yaml"):
                try:
                    with open(def_file, 'r', encoding='utf-8') as f:
                        definition = yaml.safe_load(f)
                    
                    # Créer un objet TemplateDefinition
                    template_def = TemplateDefinition(**definition)
                    templates[template_def.template_id] = template_def
                    
                except Exception as e:
                    logger.warning(f"Erreur lors du chargement de la définition {def_file}: {str(e)}")
            
            # Chercher également les fichiers JSON
            for def_file in doc_type_dir.glob("**/*.json"):
                try:
                    with open(def_file, 'r', encoding='utf-8') as f:
                        definition = json.load(f)
                    
                    # Créer un objet TemplateDefinition
                    template_def = TemplateDefinition(**definition)
                    templates[template_def.template_id] = template_def
                    
                except Exception as e:
                    logger.warning(f"Erreur lors du chargement de la définition {def_file}: {str(e)}")
        
        return templates
    
    def get_template(self, template_id: str) -> Optional[Template]:
        """
        Récupère un template Jinja2 par son identifiant.
        
        Args:
            template_id: Identifiant du template
            
        Returns:
            Template Jinja2 ou None si non trouvé
        """
        if template_id not in self.templates:
            logger.warning(f"Template '{template_id}' non trouvé")
            return None
        
        template_def = self.templates[template_id]
        template_path = self._get_template_path(template_def)
        
        if not template_path:
            logger.warning(f"Fichier de template pour '{template_id}' non trouvé")
            return None
        
        try:
            # Utiliser le chemin relatif pour charger le template
            relative_path = str(template_path.relative_to(self.templates_dir))
            return self.jinja_env.get_template(relative_path)
        except Exception as e:
            logger.error(f"Erreur lors du chargement du template '{template_id}': {str(e)}")
            return None
    
    def _get_template_path(self, template_def: TemplateDefinition) -> Optional[Path]:
        """
        Détermine le chemin du fichier de template à partir de sa définition.
        
        Args:
            template_def: Définition du template
            
        Returns:
            Path du fichier de template ou None si non trouvé
        """
        # Déterminer le répertoire en fonction du type de document
        doc_type_dir = {
            DocumentType.CONTRACT: self.contract_dir,
            DocumentType.SPECIFICATION: self.specification_dir,
            DocumentType.MANAGEMENT_PLAN: self.management_plan_dir,
            DocumentType.ADMINISTRATIVE: self.administrative_dir,
            DocumentType.CUSTOM: self.custom_dir
        }.get(template_def.document_type, self.custom_dir)
        
        # Chercher le fichier de template HTML
        template_file = doc_type_dir / f"{template_def.template_id}.html"
        if template_file.exists():
            return template_file
        
        # Chercher le fichier de template DOCX
        template_file = doc_type_dir / f"{template_def.template_id}.docx.xml"
        if template_file.exists():
            return template_file
        
        # Chercher d'autres formats possibles
        for ext in ['txt', 'md', 'tex']:
            template_file = doc_type_dir / f"{template_def.template_id}.{ext}"
            if template_file.exists():
                return template_file
        
        return None
    
    def render_template(self, template_id: str, data: Dict[str, Any]) -> Optional[str]:
        """
        Rend un template avec les données fournies.
        
        Args:
            template_id: Identifiant du template
            data: Données à injecter dans le template
            
        Returns:
            Contenu du template rendu ou None en cas d'erreur
        """
        template = self.get_template(template_id)
        if not template:
            return None
        
        try:
            return template.render(**data)
        except Exception as e:
            logger.error(f"Erreur lors du rendu du template '{template_id}': {str(e)}")
            return None
    
    def validate_template_data(self, template_id: str, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Valide les données fournies pour un template.
        
        Args:
            template_id: Identifiant du template
            data: Données à valider
            
        Returns:
            Dictionnaire des erreurs par variable
        """
        if template_id not in self.templates:
            return {"_global": [f"Template '{template_id}' non trouvé"]}
        
        template_def = self.templates[template_id]
        errors = {}
        
        # Vérifier les variables requises
        for var in template_def.variables:
            if var.required and var.name not in data:
                if "_missing" not in errors:
                    errors["_missing"] = []
                errors["_missing"].append(f"Variable requise '{var.name}' manquante")
            
            # Vérifier le type si la variable est présente
            if var.name in data and data[var.name] is not None:
                value = data[var.name]
                
                # Vérification type primitive
                if var.type == "string" and not isinstance(value, str):
                    if var.name not in errors:
                        errors[var.name] = []
                    errors[var.name].append(f"Doit être une chaîne de caractères")
                
                elif var.type == "number" and not isinstance(value, (int, float)):
                    if var.name not in errors:
                        errors[var.name] = []
                    errors[var.name].append(f"Doit être un nombre")
                
                elif var.type == "boolean" and not isinstance(value, bool):
                    if var.name not in errors:
                        errors[var.name] = []
                    errors[var.name].append(f"Doit être un booléen")
                
                elif var.type == "array" and not isinstance(value, list):
                    if var.name not in errors:
                        errors[var.name] = []
                    errors[var.name].append(f"Doit être une liste")
                
                elif var.type == "object" and not isinstance(value, dict):
                    if var.name not in errors:
                        errors[var.name] = []
                    errors[var.name].append(f"Doit être un objet")
                
                # Vérifier les contraintes spécifiques
                if "constraints" in var.constraints:
                    for constraint, constraint_value in var.constraints.items():
                        if constraint == "min" and isinstance(value, (int, float)) and value < constraint_value:
                            if var.name not in errors:
                                errors[var.name] = []
                            errors[var.name].append(f"Doit être supérieur à {constraint_value}")
                        
                        elif constraint == "max" and isinstance(value, (int, float)) and value > constraint_value:
                            if var.name not in errors:
                                errors[var.name] = []
                            errors[var.name].append(f"Doit être inférieur à {constraint_value}")
                        
                        elif constraint == "minLength" and isinstance(value, str) and len(value) < constraint_value:
                            if var.name not in errors:
                                errors[var.name] = []
                            errors[var.name].append(f"Doit avoir au moins {constraint_value} caractères")
                        
                        elif constraint == "maxLength" and isinstance(value, str) and len(value) > constraint_value:
                            if var.name not in errors:
                                errors[var.name] = []
                            errors[var.name].append(f"Doit avoir au plus {constraint_value} caractères")
                        
                        elif constraint == "pattern" and isinstance(value, str) and not re.match(constraint_value, value):
                            if var.name not in errors:
                                errors[var.name] = []
                            errors[var.name].append(f"Ne correspond pas au format attendu")
                        
                        elif constraint == "enum" and value not in constraint_value:
                            if var.name not in errors:
                                errors[var.name] = []
                            errors[var.name].append(f"Doit être l'une des valeurs suivantes: {', '.join(map(str, constraint_value))}")
        
        return errors
    
    def get_available_templates(self, document_type: Optional[DocumentType] = None) -> List[TemplateDefinition]:
        """
        Récupère la liste des templates disponibles, filtré optionnellement par type.
        
        Args:
            document_type: Type de document pour filtrer les templates
            
        Returns:
            Liste des définitions de templates
        """
        if document_type:
            return [t for t in self.templates.values() if t.document_type == document_type]
        else:
            return list(self.templates.values())
    
    def create_template_skeleton(self, template_id: str, document_type: DocumentType, 
                               name: str, description: str) -> bool:
        """
        Crée un squelette de template avec les fichiers nécessaires.
        
        Args:
            template_id: Identifiant unique du template
            document_type: Type de document
            name: Nom du template
            description: Description du template
            
        Returns:
            True si le squelette a été créé avec succès, False sinon
        """
        # Déterminer le répertoire cible
        doc_type_dir = {
            DocumentType.CONTRACT: self.contract_dir,
            DocumentType.SPECIFICATION: self.specification_dir,
            DocumentType.MANAGEMENT_PLAN: self.management_plan_dir,
            DocumentType.ADMINISTRATIVE: self.administrative_dir,
            DocumentType.CUSTOM: self.custom_dir
        }.get(document_type, self.custom_dir)
        
        # Vérifier si le template existe déjà
        if template_id in self.templates:
            logger.warning(f"Un template avec l'ID '{template_id}' existe déjà")
            return False
        
        try:
            # Créer la définition du template
            template_def = TemplateDefinition(
                template_id=template_id,
                name=name,
                document_type=document_type,
                description=description,
                variables=[],
                supported_formats=[DocumentFormat.HTML, DocumentFormat.PDF]
            )
            
            # Écrire le fichier de définition
            definition_file = doc_type_dir / f"{template_id}.yaml"
            with open(definition_file, 'w', encoding='utf-8') as f:
                yaml.dump(template_def.dict(), f, default_flow_style=False, sort_keys=False)
            
            # Créer un fichier de template HTML vide
            template_file = doc_type_dir / f"{template_id}.html"
            with open(template_file, 'w', encoding='utf-8') as f:
                f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20mm; }}
        h1 {{ color: #2c5e1a; }}
        .header {{ border-bottom: 1px solid #2c5e1a; padding-bottom: 10px; margin-bottom: 20px; }}
        .footer {{ border-top: 1px solid #2c5e1a; padding-top: 10px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{name}</h1>
        <p>{{ date | format_date }}</p>
    </div>
    
    <div class="content">
        <!-- Contenu du template ici -->
        <p>Ce document a été généré automatiquement par ForestAI.</p>
    </div>
    
    <div class="footer">
        <p>Document généré le {{ date | format_date }}</p>
    </div>
</body>
</html>""")
            
            # Actualiser la liste des templates
            self.templates[template_id] = template_def
            
            logger.info(f"Squelette de template '{template_id}' créé avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du squelette de template '{template_id}': {str(e)}")
            return False
