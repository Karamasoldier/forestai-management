#!/usr/bin/env python3
"""
Agent de réglementation forestière (ReglementationAgent) pour l'analyse juridique 
et la conformité des projets forestiers avec le Code Forestier et autres réglementations.
"""

import os
import logging
import json
from pathlib import Path
import pandas as pd
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union

from forestai.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

class ReglementationAgent(BaseAgent):
    """
    Agent responsable de l'analyse juridique et réglementaire des projets forestiers.
    Spécialisé dans le Code Forestier et autres réglementations applicables à la gestion forestière.
    """
    
    def __init__(self, config):
        """
        Initialise l'agent de réglementation forestière.
        
        Args:
            config (dict): Configuration de l'agent
        """
        super().__init__(config)
        
        # Charger la base de connaissances réglementaires
        self.knowledge_base_path = os.path.join(
            config.get("data_path", "./data"), 
            "reglementation"
        )
        
        # S'assurer que le dossier existe
        os.makedirs(self.knowledge_base_path, exist_ok=True)
        
        # Initialiser les bases de données réglementaires
        self.code_forestier = self._load_code_forestier()
        self.regional_rules = self._load_regional_rules()
        self.jurisprudence = self._load_jurisprudence()
        
        # Variables d'état
        self.current_region = None
        self.current_department = None
        self.current_project = None
        
        logger.info("ReglementationAgent initialisé")
    
    def run(self):
        """Exécute l'agent de réglementation avec les paramètres par défaut"""
        logger.info("Démarrage de l'agent de réglementation forestière")
        return {"status": "success", "message": "Agent de réglementation forestière démarré"}
    
    def check_compliance(self, parcels=None, project_type=None, region=None, department=None, project_details=None):
        """
        Vérifie la conformité réglementaire d'un projet forestier.
        
        Args:
            parcels (list): Liste d'identifiants de parcelles
            project_type (str): Type de projet (boisement, coupe, défrichement...)
            region (str, optional): Région concernée
            department (str, optional): Département concerné
            project_details (dict, optional): Détails supplémentaires sur le projet
            
        Returns:
            dict: Résultat de l'analyse de conformité
        """
        logger.info(f"Vérification de conformité pour projet de type {project_type}")
        
        # Mettre à jour l'état
        self.current_region = region
        self.current_department = department
        self.current_project = {
            "type": project_type,
            "parcels": parcels,
            "details": project_details or {}
        }
        
        # Recueillir les règles applicables
        applicable_rules = self._get_applicable_rules(
            project_type=project_type,
            region=region,
            department=department
        )
        
        # Vérifier la conformité avec chaque règle
        compliance_results = []
        for rule in applicable_rules:
            result = self._check_rule_compliance(rule, parcels, project_details)
            compliance_results.append(result)
        
        # Analyser les résultats et générer des recommandations
        compliant = all(result["compliant"] for result in compliance_results)
        
        # Générer un résumé
        summary = {
            "project_type": project_type,
            "region": region,
            "department": department,
            "overall_compliance": "conforme" if compliant else "non conforme",
            "rules_count": len(applicable_rules),
            "compliant_rules": sum(1 for r in compliance_results if r["compliant"]),
            "non_compliant_rules": sum(1 for r in compliance_results if not r["compliant"]),
            "recommendations": self._generate_recommendations(compliance_results)
        }
        
        return {
            "status": "success",
            "compliance": compliant,
            "summary": summary,
            "details": compliance_results
        }
    
    def generate_legal_brief(self, project_type, location=None, area_ha=None, details=None):
        """
        Génère une fiche juridique pour un type de projet forestier.
        
        Args:
            project_type (str): Type de projet (boisement, coupe, défrichement...)
            location (str, optional): Localisation (région, département)
            area_ha (float, optional): Surface en hectares
            details (dict, optional): Détails supplémentaires sur le projet
            
        Returns:
            dict: Fiche juridique
        """
        logger.info(f"Génération d'une fiche juridique pour {project_type}")
        
        # Déterminer la région et le département à partir de la localisation
        region, department = self._parse_location(location) if location else (None, None)
        
        # Recueillir les règles applicables
        applicable_rules = self._get_applicable_rules(
            project_type=project_type,
            region=region,
            department=department
        )
        
        # Filtrer les règles par pertinence
        if area_ha is not None:
            applicable_rules = [
                rule for rule in applicable_rules
                if "min_area" not in rule or rule["min_area"] <= area_ha
            ]
        
        # Organiser les règles par catégorie
        categorized_rules = {}
        for rule in applicable_rules:
            category = rule.get("category", "Autre")
            if category not in categorized_rules:
                categorized_rules[category] = []
            categorized_rules[category].append(rule)
        
        # Générer la fiche juridique
        legal_brief = {
            "title": f"Fiche juridique - {project_type.capitalize()}",
            "project_type": project_type,
            "location": {
                "region": region,
                "department": department
            },
            "area_ha": area_ha,
            "generation_date": datetime.now().strftime("%Y-%m-%d"),
            "categories": []
        }
        
        # Ajouter les règles par catégorie
        for category, rules in categorized_rules.items():
            category_brief = {
                "name": category,
                "rules": []
            }
            
            for rule in rules:
                category_brief["rules"].append({
                    "title": rule.get("title", ""),
                    "description": rule.get("description", ""),
                    "reference": rule.get("reference", ""),
                    "required_actions": rule.get("required_actions", []),
                    "exceptions": rule.get("exceptions", [])
                })
            
            legal_brief["categories"].append(category_brief)
        
        # Ajouter une synthèse 
        legal_brief["summary"] = self._generate_brief_summary(legal_brief, project_type, area_ha)
        
        return {
            "status": "success",
            "legal_brief": legal_brief
        }
    
    def get_regional_rules(self, region=None, department=None, rule_type=None):
        """
        Obtient les règles spécifiques à une région ou un département.
        
        Args:
            region (str, optional): Nom de la région
            department (str, optional): Code ou nom du département
            rule_type (str, optional): Type de règle (coupe, défrichement, etc.)
            
        Returns:
            dict: Règles régionales
        """
        logger.info(f"Recherche de règles régionales pour {region or ''} {department or ''}")
        
        # Filtrer les règles régionales
        filtered_rules = self.regional_rules
        
        if region:
            filtered_rules = [r for r in filtered_rules if r.get("region") == region]
        
        if department:
            filtered_rules = [r for r in filtered_rules if r.get("department") == department]
        
        if rule_type:
            filtered_rules = [r for r in filtered_rules if r.get("type") == rule_type]
        
        # Organiser les règles par catégorie
        result = {}
        for rule in filtered_rules:
            category = rule.get("category", "Autre")
            if category not in result:
                result[category] = []
            result[category].append(rule)
        
        return {
            "status": "success",
            "count": len(filtered_rules),
            "rules": result
        }
    
    def search_code_forestier(self, query, article=None):
        """
        Recherche dans le Code Forestier.
        
        Args:
            query (str): Terme de recherche
            article (str, optional): Numéro d'article spécifique
            
        Returns:
            dict: Résultats de la recherche
        """
        logger.info(f"Recherche dans le Code Forestier: {query}")
        
        results = []
        
        # Si un article spécifique est demandé
        if article:
            for art in self.code_forestier:
                if art.get("id") == article:
                    results.append(art)
                    break
        else:
            # Recherche par mot-clé
            query_lower = query.lower()
            for art in self.code_forestier:
                # Recherche dans le titre
                if query_lower in art.get("title", "").lower():
                    results.append(art)
                    continue
                
                # Recherche dans le contenu
                if query_lower in art.get("content", "").lower():
                    results.append(art)
                    continue
        
        return {
            "status": "success",
            "count": len(results),
            "results": results
        }
    
    # Méthodes privées
    
    def _load_code_forestier(self):
        """Charge la base de données du Code Forestier"""
        code_path = os.path.join(self.knowledge_base_path, "code_forestier.json")
        
        # Si le fichier n'existe pas, créer une structure vide
        if not os.path.exists(code_path):
            # Dans une vraie implémentation, on pourrait prévoir un mécanisme 
            # pour télécharger ou mettre à jour automatiquement le Code Forestier
            logger.warning("Base de données du Code Forestier non trouvée, création d'une structure vide")
            return []
        
        try:
            with open(code_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erreur lors du chargement du Code Forestier: {e}")
            return []
    
    def _load_regional_rules(self):
        """Charge la base de données des règles régionales"""
        regional_path = os.path.join(self.knowledge_base_path, "regional_rules.json")
        
        if not os.path.exists(regional_path):
            logger.warning("Base de données des règles régionales non trouvée, création d'une structure vide")
            return []
        
        try:
            with open(regional_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erreur lors du chargement des règles régionales: {e}")
            return []
    
    def _load_jurisprudence(self):
        """Charge la base de données de jurisprudence"""
        jurisprudence_path = os.path.join(self.knowledge_base_path, "jurisprudence.json")
        
        if not os.path.exists(jurisprudence_path):
            logger.warning("Base de données de jurisprudence non trouvée, création d'une structure vide")
            return []
        
        try:
            with open(jurisprudence_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la jurisprudence: {e}")
            return []
    
    def _get_applicable_rules(self, project_type, region=None, department=None):
        """
        Détermine les règles applicables à un projet.
        
        Args:
            project_type (str): Type de projet
            region (str, optional): Région
            department (str, optional): Département
            
        Returns:
            list: Liste des règles applicables
        """
        # Règles nationales (Code Forestier)
        applicable_rules = []
        
        # 1. Extraire les règles nationales du Code Forestier
        for article in self.code_forestier:
            if project_type.lower() in article.get("keywords", []):
                rule = {
                    "title": article.get("title", ""),
                    "description": article.get("content", ""),
                    "reference": f"Code Forestier, article {article.get('id', '')}",
                    "level": "national",
                    "category": "Code Forestier"
                }
                applicable_rules.append(rule)
        
        # 2. Ajouter les règles régionales si applicable
        if region or department:
            for reg_rule in self.regional_rules:
                # Vérifier si la règle correspond à la région/département
                region_match = not region or reg_rule.get("region") == region
                dept_match = not department or reg_rule.get("department") == department
                
                # Vérifier si la règle correspond au type de projet
                project_match = reg_rule.get("project_type") == project_type
                
                if region_match and dept_match and project_match:
                    applicable_rules.append(reg_rule)
        
        return applicable_rules
    
    def _check_rule_compliance(self, rule, parcels=None, project_details=None):
        """
        Vérifie la conformité d'un projet avec une règle spécifique.
        
        Args:
            rule (dict): La règle à vérifier
            parcels (list): Liste des parcelles concernées
            project_details (dict): Détails du projet
            
        Returns:
            dict: Résultat de l'analyse de conformité pour cette règle
        """
        # Dans une implémentation réelle, cette fonction contiendrait 
        # une logique complexe pour évaluer la conformité
        
        # Pour cet exemple, nous utilisons une logique simplifiée
        compliant = True
        issues = []
        
        # Vérification basique basée sur les seuils de surface
        if project_details and "area_ha" in project_details:
            area = project_details["area_ha"]
            
            # Exemple: vérification de seuil minimal
            if "min_area" in rule and area < rule["min_area"]:
                compliant = False
                issues.append(f"Surface de {area} ha inférieure au minimum requis de {rule['min_area']} ha")
            
            # Exemple: vérification de seuil maximal
            if "max_area" in rule and area > rule["max_area"]:
                compliant = False
                issues.append(f"Surface de {area} ha supérieure au maximum permis de {rule['max_area']} ha")
        
        # Vérification des exigences administratives
        if "required_documents" in rule and project_details:
            for doc in rule["required_documents"]:
                if "documents" not in project_details or doc not in project_details["documents"]:
                    compliant = False
                    issues.append(f"Document requis manquant: {doc}")
        
        return {
            "rule": rule,
            "compliant": compliant,
            "issues": issues
        }
    
    def _generate_recommendations(self, compliance_results):
        """
        Génère des recommandations basées sur les résultats de conformité.
        
        Args:
            compliance_results (list): Résultats de l'analyse de conformité
            
        Returns:
            list: Recommandations pour atteindre la conformité
        """
        recommendations = []
        
        # Identifier les problèmes de conformité et générer des recommandations
        for result in compliance_results:
            if not result["compliant"]:
                rule = result["rule"]
                
                # Générer une recommandation pour chaque problème
                for issue in result["issues"]:
                    # Exemples de recommandations
                    if "surface" in issue.lower():
                        recommendations.append(f"Ajuster la surface du projet pour respecter les limites de {rule.get('title')}")
                    
                    elif "document" in issue.lower():
                        recommendations.append(f"Fournir le document manquant: {issue.split(': ')[1]}")
                    
                    else:
                        recommendations.append(f"Résoudre le problème: {issue} (Référence: {rule.get('reference')})")
        
        return recommendations
    
    def _parse_location(self, location):
        """
        Analyse une chaîne de localisation pour en extraire la région et le département.
        
        Args:
            location (str): Chaîne décrivant la localisation
            
        Returns:
            tuple: (région, département) ou (None, None) si non identifiables
        """
        if not location:
            return None, None
        
        # Liste des régions françaises
        regions = [
            "Auvergne-Rhône-Alpes", "Bourgogne-Franche-Comté", "Bretagne",
            "Centre-Val de Loire", "Corse", "Grand Est", "Hauts-de-France",
            "Île-de-France", "Normandie", "Nouvelle-Aquitaine", "Occitanie",
            "Pays de la Loire", "Provence-Alpes-Côte d'Azur"
        ]
        
        # Recherche de la région dans la chaîne de localisation
        region_found = None
        for region in regions:
            if region.lower() in location.lower():
                region_found = region
                break
        
        # Recherche d'un code de département (format: 2 chiffres ou 2A/2B pour la Corse)
        dept_match = re.search(r'\b(?:\d{2}|2[AB])\b', location)
        dept_found = dept_match.group(0) if dept_match else None
        
        return region_found, dept_found
    
    def _generate_brief_summary(self, legal_brief, project_type, area_ha=None):
        """
        Génère un résumé synthétique pour la fiche juridique.
        
        Args:
            legal_brief (dict): Contenu de la fiche juridique
            project_type (str): Type de projet
            area_ha (float, optional): Surface en hectares
            
        Returns:
            str: Résumé de la fiche
        """
        # Déterminer les principales obligations
        obligations = []
        
        # Compteur des règles par catégorie
        category_counts = {}
        
        for category in legal_brief["categories"]:
            category_name = category["name"]
            category_counts[category_name] = len(category["rules"])
            
            # Identifier les obligations les plus importantes
            for rule in category["rules"]:
                if "required_actions" in rule and rule["required_actions"]:
                    obligations.extend(rule["required_actions"])
        
        # Limiter le nombre d'obligations à afficher
        top_obligations = obligations[:5] if len(obligations) > 5 else obligations
        
        # Construire le résumé
        summary = f"Ce projet de {project_type}"
        if area_ha:
            summary += f" sur {area_ha} hectares"
        
        summary += f" est soumis à {sum(category_counts.values())} règles réparties en {len(category_counts)} catégories. "
        
        if top_obligations:
            summary += "Principales obligations : "
            summary += ", ".join(top_obligations)
        else:
            summary += "Consultez les détails pour connaître les obligations spécifiques."
        
        return summary