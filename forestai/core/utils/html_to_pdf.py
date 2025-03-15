# -*- coding: utf-8 -*-
"""
Module de conversion HTML vers PDF.

Ce module fournit des fonctionnalités pour convertir du contenu HTML en PDF,
en utilisant plusieurs backends selon les disponibilités.
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Optional, Union, BytesIO

logger = logging.getLogger(__name__)

def html_to_pdf(html_content: str, options: Optional[dict] = None) -> bytes:
    """
    Convertit du contenu HTML en PDF.
    
    Cette fonction essaie plusieurs backends dans l'ordre suivant:
    1. WeasyPrint (pure Python mais avec moins de fonctionnalités)
    2. pdfkit/wkhtmltopdf (meilleur rendu mais dépendances système)
    
    Args:
        html_content: Contenu HTML à convertir
        options: Options de conversion spécifiques
        
    Returns:
        Contenu PDF en bytes
        
    Raises:
        RuntimeError: Si aucun backend n'est disponible ou si la conversion échoue
    """
    options = options or {}
    
    # Essayer WeasyPrint d'abord (installation Python pure)
    try:
        return _html_to_pdf_weasyprint(html_content, options)
    except Exception as e:
        logger.warning(f"Conversion HTML->PDF avec WeasyPrint a échoué: {str(e)}")
    
    # Essayer pdfkit/wkhtmltopdf ensuite
    try:
        return _html_to_pdf_pdfkit(html_content, options)
    except Exception as e:
        logger.warning(f"Conversion HTML->PDF avec pdfkit a échoué: {str(e)}")
    
    # Si tout a échoué, lever une exception
    raise RuntimeError("Impossible de convertir le HTML en PDF. Aucun backend disponible.")

def _html_to_pdf_weasyprint(html_content: str, options: dict) -> bytes:
    """
    Convertit du HTML en PDF en utilisant WeasyPrint.
    
    Args:
        html_content: Contenu HTML
        options: Options de conversion
        
    Returns:
        Contenu PDF en bytes
    """
    try:
        from weasyprint import HTML, CSS
        
        # Options spécifiques à WeasyPrint
        stylesheets = []
        if 'css' in options:
            if isinstance(options['css'], str):
                stylesheets.append(CSS(string=options['css']))
            elif isinstance(options['css'], list):
                for css in options['css']:
                    if os.path.isfile(css):
                        stylesheets.append(CSS(filename=css))
                    else:
                        stylesheets.append(CSS(string=css))
        
        # Créer un BytesIO pour stocker le PDF
        pdf_buffer = BytesIO()
        
        # Convertir le HTML en PDF
        HTML(string=html_content).write_pdf(
            pdf_buffer,
            stylesheets=stylesheets
        )
        
        # Récupérer le contenu du buffer
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()
    
    except ImportError:
        raise RuntimeError("WeasyPrint n'est pas installé.")

def _html_to_pdf_pdfkit(html_content: str, options: dict) -> bytes:
    """
    Convertit du HTML en PDF en utilisant pdfkit/wkhtmltopdf.
    
    Args:
        html_content: Contenu HTML
        options: Options de conversion
        
    Returns:
        Contenu PDF en bytes
    """
    try:
        import pdfkit
        
        # Options par défaut pour pdfkit
        pdfkit_options = {
            'encoding': 'UTF-8',
            'page-size': 'A4',
            'margin-top': '20mm',
            'margin-bottom': '20mm',
            'margin-left': '20mm',
            'margin-right': '20mm',
            'quiet': True
        }
        
        # Fusionner avec les options fournies
        if 'pdfkit_options' in options:
            pdfkit_options.update(options['pdfkit_options'])
        
        # Configuration spécifique si wkhtmltopdf n'est pas dans le PATH
        config = None
        if 'wkhtmltopdf_path' in options:
            from pdfkit.configuration import Configuration
            config = Configuration(wkhtmltopdf=options['wkhtmltopdf_path'])
        
        # Convertir le HTML en PDF
        pdf_content = pdfkit.from_string(
            html_content,
            False,  # Ne pas sauvegarder dans un fichier
            options=pdfkit_options,
            configuration=config
        )
        
        return pdf_content
    
    except ImportError:
        raise RuntimeError("pdfkit n'est pas installé.")
