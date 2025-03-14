"""
Module définissant le scraper pour les subventions du programme France Relance.
"""
import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base_scraper import BaseScraper


class FranceRelanceScraper(BaseScraper):
    """
    Scraper pour extraire les informations de subventions du programme France Relance.
    
    Ce scraper extrait les subventions forestières disponibles dans le cadre
    du plan France Relance, notamment pour le reboisement et la restauration
    des forêts.
    """
    
    DEFAULT_URL = "https://www.economie.gouv.fr/plan-de-relance/mesures/foret"
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialise le scraper France Relance.
        
        Args:
            config: Dictionnaire de configuration avec les paramètres suivants:
                - url (optional): URL à scraper (par défaut: URL de France Relance)
                - headers (optional): En-têtes HTTP à utiliser pour les requêtes
                - timeout (optional): Délai d'attente pour les requêtes HTTP (en secondes)
        """
        super().__init__(config)
        self.url = config.get("url", self.DEFAULT_URL)
        self.headers = config.get("headers", {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        self.timeout = config.get("timeout", 30)
    
    def fetch_data(self) -> List[Dict[str, Any]]:
        """
        Récupère les données brutes sur les subventions depuis le site France Relance.
        
        Returns:
            Liste de dictionnaires contenant les données brutes des subventions
        
        Raises:
            ConnectionError: Si la connexion au site échoue
            TimeoutError: Si la requête dépasse le délai d'attente
        """
        self.logger.info(f"Récupération des données depuis {self.url}")
        
        try:
            response = requests.get(
                self.url,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # Extraction des données brutes
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Recherche des sections contenant les informations sur les subventions
            subsidy_sections = soup.find_all("div", class_="fr-callout")
            
            raw_data = []
            for section in subsidy_sections:
                title_elem = section.find(["h2", "h3", "h4"])
                title = title_elem.text.strip() if title_elem else "Sans titre"
                
                content = section.get_text(strip=True)
                
                # Extraction de l'URL du lien principal s'il existe
                link = section.find("a")
                url = link.get("href") if link else None
                
                raw_data.append({
                    "title": title,
                    "content": content,
                    "url": url,
                    "html": str(section)
                })
            
            # Si aucune donnée n'est trouvée avec la structure attendue,
            # essayons une approche plus générique
            if not raw_data:
                self.logger.warning("Structure attendue non trouvée, utilisation d'une approche alternative")
                
                # Recherche des articles ou sections principales
                articles = soup.find_all(["article", "section"])
                
                for article in articles:
                    title_elem = article.find(["h1", "h2", "h3"])
                    title = title_elem.text.strip() if title_elem else "Sans titre"
                    
                    content = article.get_text(strip=True)
                    
                    # Extraction de l'URL du lien principal s'il existe
                    link = article.find("a")
                    url = link.get("href") if link else None
                    
                    raw_data.append({
                        "title": title,
                        "content": content,
                        "url": url,
                        "html": str(article)
                    })
            
            self.logger.info(f"{len(raw_data)} sections de subventions potentielles trouvées")
            return raw_data
        
        except requests.ConnectionError as e:
            self.logger.error(f"Erreur de connexion: {str(e)}")
            raise ConnectionError(f"Impossible de se connecter à {self.url}: {str(e)}")
        
        except requests.Timeout as e:
            self.logger.error(f"Délai d'attente dépassé: {str(e)}")
            raise TimeoutError(f"Délai d'attente dépassé pour {self.url}: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des données: {str(e)}", exc_info=True)
            raise
    
    def parse_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Traite les données brutes pour extraire les informations pertinentes sur les subventions.
        
        Args:
            raw_data: Liste de dictionnaires contenant les données brutes des subventions
        
        Returns:
            Liste de dictionnaires contenant les informations structurées des subventions
        """
        self.logger.info("Analyse des données brutes")
        
        parsed_data = []
        
        for item in raw_data:
            title = item["title"]
            content = item["content"]
            url = item["url"]
            
            # Vérification si c'est une subvention forestière
            if not self._is_forestry_related(title, content):
                self.logger.debug(f"Élément ignoré (non lié à la foresterie): {title}")
                continue
            
            # Extraction des informations pertinentes
            subsidy = {
                "title": title,
                "source": "France Relance",
                "url": url,
                "region": "National",  # France Relance est un programme national
                "description": self._extract_description(content),
                "eligible_projects": self._extract_eligible_projects(content),
                "application_deadline": self._extract_deadline(content),
                "min_amount": self._extract_min_amount(content),
                "max_amount": self._extract_max_amount(content),
                "financing_rate": self._extract_financing_rate(content),
                "eligibility_criteria": self._extract_eligibility_criteria(content),
                "contact": self._extract_contact(content),
                "updated_at": datetime.now().isoformat(),
            }
            
            parsed_data.append(subsidy)
        
        self.logger.info(f"{len(parsed_data)} subventions forestières trouvées")
        return parsed_data
    
    def _is_forestry_related(self, title: str, content: str) -> bool:
        """
        Vérifie si le contenu est lié à la foresterie.
        
        Args:
            title: Titre de la section
            content: Contenu textuel de la section
        
        Returns:
            True si le contenu est lié à la foresterie, False sinon
        """
        forestry_keywords = [
            "forêt", "forestier", "forestière", "reboisement", "boisement",
            "sylviculture", "bois", "peuplement", "plantation", "arbre",
            "essence", "adaptabilité", "chêne", "pin", "hêtre", "douglas"
        ]
        
        # Vérifier le titre en priorité
        for keyword in forestry_keywords:
            if keyword.lower() in title.lower():
                return True
        
        # Vérifier le contenu complet
        keyword_count = 0
        for keyword in forestry_keywords:
            if keyword.lower() in content.lower():
                keyword_count += 1
                
        # Si au moins 2 mots-clés forestiers sont présents, considérer comme pertinent
        return keyword_count >= 2
    
    def _extract_description(self, content: str) -> str:
        """
        Extrait la description de la subvention à partir du contenu.
        
        Args:
            content: Contenu textuel complet
        
        Returns:
            Description extraite ou texte vide
        """
        # Pour simplifier, prendre les 300 premiers caractères comme description
        # Une approche plus sophistiquée serait d'utiliser NLP pour extraire un résumé
        if len(content) <= 300:
            return content
        
        # Trouver une phrase complète se terminant avant 300 caractères
        end_pos = content[:300].rfind('.')
        if end_pos > 0:
            return content[:end_pos + 1]
        
        return content[:300] + "..."
    
    def _extract_eligible_projects(self, content: str) -> str:
        """
        Extrait les types de projets éligibles à partir du contenu.
        
        Args:
            content: Contenu textuel complet
        
        Returns:
            Types de projets éligibles ou texte vide
        """
        # Recherche de sections décrivant les projets éligibles
        patterns = [
            r"(?:projets?|actions?)(?:\s+éligibles)[:;]?\s*(.*?)(?:\.\s|\n|$)",
            r"(?:sont|seront)(?:\s+éligibles)[:;]?\s*(.*?)(?:\.\s|\n|$)",
            r"(?:éligibilité)[:;]?\s*(.*?)(?:\.\s|\n|$)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _extract_deadline(self, content: str) -> Optional[str]:
        """
        Extrait la date limite de candidature à partir du contenu.
        
        Args:
            content: Contenu textuel complet
        
        Returns:
            Date limite ou None si non trouvée
        """
        # Recherche de formats de date courants
        date_patterns = [
            r"(?:date limite|jusqu'au|avant le|candidature).*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"(?:date limite|jusqu'au|avant le|candidature).*?(\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{2,4})"
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_min_amount(self, content: str) -> Optional[float]:
        """
        Extrait le montant minimum de la subvention à partir du contenu.
        
        Args:
            content: Contenu textuel complet
        
        Returns:
            Montant minimum ou None si non trouvé
        """
        # Recherche de montants minimaux
        patterns = [
            r"(?:montant\s+minimum|plancher|seuil\s+minimal).*?(\d+(?:[\s,.]\d+)*)\s*(?:€|euros)",
            r"(?:à\s+partir\s+de).*?(\d+(?:[\s,.]\d+)*)\s*(?:€|euros)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                # Nettoyer et convertir le montant
                amount_str = match.group(1).replace(" ", "").replace(",", ".")
                try:
                    return float(amount_str)
                except ValueError:
                    pass
        
        return None
    
    def _extract_max_amount(self, content: str) -> Optional[float]:
        """
        Extrait le montant maximum de la subvention à partir du contenu.
        
        Args:
            content: Contenu textuel complet
        
        Returns:
            Montant maximum ou None si non trouvé
        """
        # Recherche de montants maximaux
        patterns = [
            r"(?:montant\s+maximum|plafond|jusqu'à).*?(\d+(?:[\s,.]\d+)*)\s*(?:€|euros)",
            r"(?:plafonné\s+à).*?(\d+(?:[\s,.]\d+)*)\s*(?:€|euros)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                # Nettoyer et convertir le montant
                amount_str = match.group(1).replace(" ", "").replace(",", ".")
                try:
                    return float(amount_str)
                except ValueError:
                    pass
        
        return None
    
    def _extract_financing_rate(self, content: str) -> Optional[str]:
        """
        Extrait le taux de financement à partir du contenu.
        
        Args:
            content: Contenu textuel complet
        
        Returns:
            Taux de financement ou None si non trouvé
        """
        # Recherche de taux de financement
        patterns = [
            r"(?:taux\s+d[e']aide|taux\s+de\s+financement|financé\s+à\s+hauteur\s+de|subvention\s+de).*?(\d+(?:[\s,.]\d+)*\s*%)",
            r"(?:jusqu'à).*?(\d+(?:[\s,.]\d+)*\s*%)(?:\s+de\s+financement)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_eligibility_criteria(self, content: str) -> List[str]:
        """
        Extrait les critères d'éligibilité à partir du contenu.
        
        Args:
            content: Contenu textuel complet
        
        Returns:
            Liste des critères d'éligibilité
        """
        # Recherche de sections contenant des critères d'éligibilité
        criteria = []
        
        # Recherche de phrases contenant des mots-clés d'éligibilité
        sentences = re.split(r'(?<=[.!?])\s+', content)
        for sentence in sentences:
            if re.search(r'(?:critère|condition|éligible|bénéficiaire|obligation)', sentence, re.IGNORECASE):
                # Nettoyer la phrase
                clean_sentence = sentence.strip()
                if clean_sentence and len(clean_sentence) > 10:  # Éviter les phrases trop courtes
                    criteria.append(clean_sentence)
        
        return criteria
    
    def _extract_contact(self, content: str) -> Optional[str]:
        """
        Extrait les informations de contact à partir du contenu.
        
        Args:
            content: Contenu textuel complet
        
        Returns:
            Informations de contact ou None si non trouvées
        """
        # Recherche d'informations de contact (email, téléphone, site web)
        patterns = [
            r'(?:contact|renseignement|information).*?([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)',  # Email
            r'(?:contact|renseignement|information).*?((?:\+33|0)\s*[1-9](?:[\s.-]*\d{2}){4})',  # Téléphone
            r'(?:contact|renseignement|information).*?(https?://[^\s]+)',  # Site web
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1)
        
        return None
