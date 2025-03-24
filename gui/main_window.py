# gui/main_window.py
"""
Fenêtre principale de l'application GUI.
"""

import sys
import logging
import json
from typing import Dict, Any, List, Optional

from PyQt6.QtWidgets import (
    QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QTabWidget, QMenuBar, QMenu, QStatusBar, QMessageBox,
    QDialog, QDialogButtonBox, QLabel, QComboBox, QCheckBox, 
    QFormLayout, QToolBar, QFileDialog
)
from PyQt6.QtCore import Qt, QSettings, QSize
from PyQt6.QtGui import QAction, QIcon

from gui.components import AgentControlPanel, AgentMonitorPanel, ResultViewerDialog
from gui.models import AgentTableModel, TasksTableModel
from gui.agent_api import AgentAPI


class SettingsDialog(QDialog):
    """
    Boîte de dialogue pour les paramètres de l'application.
    """
    
    def __init__(self, settings: QSettings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle("Paramètres")
        self.setMinimumWidth(400)
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # Formulaire des paramètres
        form_layout = QFormLayout()
        
        # Mode de connexion
        self.api_mode = QComboBox()
        self.api_mode.addItem("API REST", "api")
        self.api_mode.addItem("Mode direct", "direct")
        current_mode = self.settings.value("api_mode", "api")
        index = 0 if current_mode == "api" else 1
        self.api_mode.setCurrentIndex(index)
        form_layout.addRow("Mode de connexion:", self.api_mode)
        
        # URL de l'API
        self.api_url = QComboBox()
        self.api_url.setEditable(True)
        current_url = self.settings.value("api_url", "http://localhost:8000")
        self.api_url.addItem(current_url)
        self.api_url.addItem("http://localhost:8000")
        self.api_url.addItem("http://localhost:8080")
        self.api_url.setCurrentText(current_url)
        form_layout.addRow("URL de l'API:", self.api_url)
        
        # Intervalle de rafraîchissement
        self.refresh_interval = QComboBox()
        self.refresh_interval.addItems(["1", "2", "5", "10"])
        current_interval = self.settings.value("refresh_interval", "2")
        index = self.refresh_interval.findText(current_interval)
        self.refresh_interval.setCurrentIndex(index if index >= 0 else 1)
        form_layout.addRow("Intervalle de rafraîchissement (s):", self.refresh_interval)
        
        # Mode verbeux
        self.verbose_mode = QCheckBox()
        self.verbose_mode.setChecked(self.settings.value("verbose_mode", "false") == "true")
        form_layout.addRow("Mode verbeux:", self.verbose_mode)
        
        main_layout.addLayout(form_layout)
        
        # Boutons de dialogue
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)
    
    def save_settings(self):
        """Sauvegarde les paramètres."""
        self.settings.setValue("api_mode", "api" if self.api_mode.currentIndex() == 0 else "direct")
        self.settings.setValue("api_url", self.api_url.currentText())
        self.settings.setValue("refresh_interval", self.refresh_interval.currentText())
        self.settings.setValue("verbose_mode", "true" if self.verbose_mode.isChecked() else "false")


class MainWindow(QMainWindow):
    """
    Fenêtre principale de l'application GUI.
    """
    
    def __init__(self):
        super().__init__()
        
        # Configuration
        self.settings = QSettings("ForestAI", "AgentGUI")
        
        # Initialisation de l'API
        api_mode = self.settings.value("api_mode", "api")
        api_url = self.settings.value("api_url", "http://localhost:8000")
        self.api = AgentAPI(use_api=(api_mode == "api"), api_url=api_url)
        
        # Modèles de données
        self.agents_model = AgentTableModel()
        self.tasks_model = TasksTableModel()
        
        # Initialisation de l'interface
        self.initUI()
        
        # Connexion des signaux de l'API
        self.connect_api_signals()
        
        # Démarrage du polling
        self.api.polling_interval = int(self.settings.value("refresh_interval", "2"))
        self.api.start_polling()
        
        # Configuration du logger
        log_level = logging.DEBUG if self.settings.value("verbose_mode", "false") == "true" else logging.INFO
        logging.getLogger("forestai.gui").setLevel(log_level)
    
    def initUI(self):
        self.setWindowTitle("ForestAI - Interface de test des agents")
        self.setMinimumSize(900, 600)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QHBoxLayout(central_widget)
        
        # Séparateur principal
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Panneau de contrôle
        self.control_panel = AgentControlPanel()
        splitter.addWidget(self.control_panel)
        
        # Panneau de surveillance
        self.monitor_panel = AgentMonitorPanel()
        self.monitor_panel.set_agents_model(self.agents_model)
        self.monitor_panel.set_tasks_model(self.tasks_model)
        splitter.addWidget(self.monitor_panel)
        
        # Ajustement du séparateur
        splitter.setSizes([300, 600])
        main_layout.addWidget(splitter)
        
        # Création de la barre de menus
        self.create_menu_bar()
        
        # Création de la barre d'outils
        self.create_tool_bar()
        
        # Création de la barre de statut
        self.statusBar().showMessage("Prêt")
        
        # Connexion des signaux
        self.connect_signals()
        
        # Chargement des paramètres de la fenêtre
        self.load_window_settings()
    
    def create_menu_bar(self):
        """Crée la barre de menus."""
        menu_bar = self.menuBar()
        
        # Menu Fichier
        file_menu = menu_bar.addMenu("Fichier")
        
        # Action Rafraîchir
        refresh_action = QAction("Rafraîchir", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_data)
        file_menu.addAction(refresh_action)
        
        # Action Exporter les résultats
        export_action = QAction("Exporter les résultats...", self)
        export_action.triggered.connect(self.export_results)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Action Paramètres
        settings_action = QAction("Paramètres...", self)
        settings_action.triggered.connect(self.show_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        # Action Quitter
        exit_action = QAction("Quitter", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menu Agents
        agent_menu = menu_bar.addMenu("Agents")
        
        # Action Démarrer tous
        start_all_action = QAction("Démarrer tous", self)
        start_all_action.triggered.connect(self.start_all_agents)
        agent_menu.addAction(start_all_action)
        
        # Action Arrêter tous
        stop_all_action = QAction("Arrêter tous", self)
        stop_all_action.triggered.connect(self.stop_all_agents)
        agent_menu.addAction(stop_all_action)
        
        # Menu Aide
        help_menu = menu_bar.addMenu("Aide")
        
        # Action À propos
        about_action = QAction("À propos", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_tool_bar(self):
        """Crée la barre d'outils."""
        tool_bar = QToolBar("Barre d'outils principale")
        self.addToolBar(tool_bar)
        
        # Action Rafraîchir
        refresh_action = QAction("Rafraîchir", self)
        refresh_action.triggered.connect(self.refresh_data)
        tool_bar.addAction(refresh_action)
        
        # Action Paramètres
        settings_action = QAction("Paramètres", self)
        settings_action.triggered.connect(self.show_settings)
        tool_bar.addAction(settings_action)
    
    def connect_signals(self):
        """Connecte les signaux des widgets."""
        # Signaux du panneau de contrôle
        self.control_panel.agent_action_triggered.connect(self.execute_agent_action)
        self.control_panel.refresh_requested.connect(self.refresh_data)
        
        # Signaux du panneau de surveillance
        self.monitor_panel.agent_selected.connect(self.on_agent_selected)
    
    def connect_api_signals(self):
        """Connecte les signaux de l'API."""
        self.api.agents_updated.connect(self.update_agents)
        self.api.tasks_updated.connect(self.update_tasks)
        self.api.agent_action_completed.connect(self.on_agent_action_completed)
        self.api.error_occurred.connect(self.on_api_error)
    
    def update_agents(self, agents_data: List[Dict[str, Any]]):
        """
        Met à jour les données des agents.
        
        Args:
            agents_data: Données des agents
        """
        self.agents_model.update_data(agents_data)
        self.control_panel.set_available_agents(agents_data)
    
    def update_tasks(self, tasks_data: List[Dict[str, Any]]):
        """
        Met à jour les données des tâches.
        
        Args:
            tasks_data: Données des tâches
        """
        self.tasks_model.update_data(tasks_data)
    
    def on_agent_selected(self, agent_name: str):
        """
        Gère la sélection d'un agent.
        
        Args:
            agent_name: Nom de l'agent sélectionné
        """
        # Mettre à jour la sélection dans le panneau de contrôle
        index = self.control_panel.agent_combo.findText(agent_name)
        if index >= 0:
            self.control_panel.agent_combo.setCurrentIndex(index)
            
            # Charger les actions disponibles
            actions = self.api.get_agent_actions(agent_name)
            self.control_panel.set_available_actions(actions)
    
    def execute_agent_action(self, agent_name: str, action: str, params: Dict[str, Any]):
        """
        Exécute une action sur un agent.
        
        Args:
            agent_name: Nom de l'agent
            action: Nom de l'action
            params: Paramètres de l'action
        """
        self.statusBar().showMessage(f"Exécution de {action} sur {agent_name}...")
        
        # Appel asynchrone pour ne pas bloquer l'interface
        threading.Thread(
            target=self.api.execute_action,
            args=(agent_name, action, params),
            daemon=True
        ).start()
    
    def on_agent_action_completed(self, agent_name: str, action: str, result: Dict[str, Any]):
        """
        Gère la fin d'exécution d'une action.
        
        Args:
            agent_name: Nom de l'agent
            action: Nom de l'action
            result: Résultat de l'action
        """
        # Mise à jour de la barre de statut
        status = "succès" if result.get("status") != "error" else "échec"
        self.statusBar().showMessage(f"Action {action} sur {agent_name} terminée avec {status}")
        
        # Affichage du résultat
        title = f"Résultat de {action} sur {agent_name}"
        dialog = ResultViewerDialog(title, result, self)
        dialog.exec()
        
        # Rafraîchir les données
        self.refresh_data()
    
    def on_api_error(self, error_message: str):
        """
        Gère les erreurs de l'API.
        
        Args:
            error_message: Message d'erreur
        """
        self.statusBar().showMessage(f"Erreur: {error_message}")
        
        # Affichage d'une boîte de dialogue d'erreur pour les erreurs importantes
        if "connexion" in error_message.lower() or "communication" in error_message.lower():
            QMessageBox.critical(self, "Erreur de connexion", error_message)
    
    def refresh_data(self):
        """Rafraîchit les données des agents et des tâches."""
        self.statusBar().showMessage("Rafraîchissement des données...")
        
        try:
            # Récupération des données des agents
            agents_data = self.api.get_agents()
            self.update_agents(agents_data)
            
            # Récupération des données des tâches
            tasks_data = self.api.get_recent_tasks()
            self.update_tasks(tasks_data)
            
            self.statusBar().showMessage("Données rafraîchies", 2000)
        except Exception as e:
            self.statusBar().showMessage(f"Erreur de rafraîchissement: {str(e)}")
    
    def start_all_agents(self):
        """Démarre tous les agents."""
        self.statusBar().showMessage("Démarrage de tous les agents...")
        
        for row in range(self.agents_model.rowCount()):
            agent_name = self.agents_model.data(self.agents_model.index(row, 0))
            self.execute_agent_action(agent_name, "start", {})
    
    def stop_all_agents(self):
        """Arrête tous les agents."""
        self.statusBar().showMessage("Arrêt de tous les agents...")
        
        for row in range(self.agents_model.rowCount()):
            agent_name = self.agents_model.data(self.agents_model.index(row, 0))
            self.execute_agent_action(agent_name, "stop", {})
    
    def show_settings(self):
        """Affiche la boîte de dialogue des paramètres."""
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            dialog.save_settings()
            
            # Mise à jour des paramètres de l'API
            api_mode = self.settings.value("api_mode", "api")
            api_url = self.settings.value("api_url", "http://localhost:8000")
            refresh_interval = int(self.settings.value("refresh_interval", "2"))
            
            # Recréation de l'API si le mode a changé
            if (api_mode == "api") != self.api.use_api or self.api.api_url != api_url:
                self.api.stop_polling()
                self.api = AgentAPI(use_api=(api_mode == "api"), api_url=api_url)
                self.connect_api_signals()
                self.api.polling_interval = refresh_interval
                self.api.start_polling()
            else:
                self.api.polling_interval = refresh_interval
            
            # Mise à jour du niveau de log
            log_level = logging.DEBUG if self.settings.value("verbose_mode", "false") == "true" else logging.INFO
            logging.getLogger("forestai.gui").setLevel(log_level)
            
            self.statusBar().showMessage("Paramètres mis à jour", 2000)
    
    def show_about(self):
        """Affiche la boîte de dialogue À propos."""
        QMessageBox.about(
            self,
            "À propos de ForestAI - Interface de test des agents",
            "ForestAI - Interface de test des agents\n\n"
            "Version 0.1.0\n\n"
            "Une interface graphique pour tester les agents du système ForestAI.\n\n"
            "© 2025 - ForestAI Team"
        )
    
    def export_results(self):
        """Exporte les résultats vers un fichier JSON."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Exporter les résultats", "", "Fichiers JSON (*.json);;Tous les fichiers (*)"
        )
        
        if filename:
            try:
                # Récupération des données
                agents_data = self.api.get_agents()
                tasks_data = self.api.get_recent_tasks()
                
                # Création du dictionnaire de résultats
                results = {
                    "agents": agents_data,
                    "tasks": tasks_data,
                    "timestamp": time.time()
                }
                
                # Écriture dans le fichier
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                
                self.statusBar().showMessage(f"Résultats exportés vers {filename}", 2000)
            except Exception as e:
                QMessageBox.warning(self, "Erreur d'exportation", f"Erreur lors de l'exportation: {str(e)}")
    
    def load_window_settings(self):
        """Charge les paramètres de la fenêtre."""
        size = self.settings.value("window_size")
        pos = self.settings.value("window_pos")
        
        if size:
            self.resize(size)
        if pos:
            self.move(pos)
    
    def closeEvent(self, event):
        """
        Gère l'événement de fermeture de la fenêtre.
        
        Args:
            event: Événement de fermeture
        """
        # Sauvegarde des paramètres de la fenêtre
        self.settings.setValue("window_size", self.size())
        self.settings.setValue("window_pos", self.pos())
        
        # Arrêt du polling
        self.api.stop_polling()
        
        # Acceptation de l'événement
        event.accept()

# Nécessaire pour éviter un problème de référence circulaire
import threading
import time
