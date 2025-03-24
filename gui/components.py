# gui/components.py
"""
Composants d'interface utilisateur réutilisables.
"""

import json
from typing import Dict, Any, List, Optional, Callable
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QComboBox, QTextEdit, QLineEdit, QFormLayout, QTableView,
    QGroupBox, QSplitter, QHeaderView, QTabWidget, QDialog,
    QDialogButtonBox, QMessageBox, QCheckBox, QSpacerItem,
    QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize


class AgentControlPanel(QWidget):
    """
    Panneau de contrôle pour les agents.
    """
    
    agent_action_triggered = pyqtSignal(str, str, dict)
    refresh_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
    
    def initUI(self):
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # Groupe pour la sélection d'agent
        agent_group = QGroupBox("Sélection de l'agent")
        agent_layout = QVBoxLayout(agent_group)
        
        # ComboBox pour la liste des agents
        self.agent_combo = QComboBox()
        agent_layout.addWidget(self.agent_combo)
        
        # Ajout des boutons d'actions génériques
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Démarrer")
        self.stop_btn = QPushButton("Arrêter")
        self.refresh_btn = QPushButton("Rafraîchir")
        
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addWidget(self.refresh_btn)
        
        agent_layout.addLayout(btn_layout)
        main_layout.addWidget(agent_group)
        
        # Groupe pour l'exécution d'actions
        actions_group = QGroupBox("Exécution d'action")
        actions_layout = QVBoxLayout(actions_group)
        
        # Sélection de l'action
        form_layout = QFormLayout()
        self.action_combo = QComboBox()
        form_layout.addRow("Action:", self.action_combo)
        
        # Paramètres de l'action
        self.params_edit = QTextEdit()
        self.params_edit.setPlaceholderText("{\n  \"param1\": \"valeur1\",\n  \"param2\": \"valeur2\"\n}")
        form_layout.addRow("Paramètres (JSON):", self.params_edit)
        
        actions_layout.addLayout(form_layout)
        
        # Bouton d'exécution
        self.execute_btn = QPushButton("Exécuter")
        actions_layout.addWidget(self.execute_btn)
        
        main_layout.addWidget(actions_group)
        
        # Espacement vertical pour pousser les widgets vers le haut
        spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        main_layout.addItem(spacer)
        
        # Connexion des signaux
        self.start_btn.clicked.connect(self.on_start_clicked)
        self.stop_btn.clicked.connect(self.on_stop_clicked)
        self.refresh_btn.clicked.connect(self.refresh_requested.emit)
        self.execute_btn.clicked.connect(self.on_execute_clicked)
    
    def set_available_agents(self, agents: List[Dict[str, Any]]):
        """
        Met à jour la liste des agents disponibles.
        
        Args:
            agents: Liste des agents disponibles
        """
        self.agent_combo.clear()
        for agent in agents:
            self.agent_combo.addItem(agent["name"], agent)
    
    def set_available_actions(self, actions: List[str]):
        """
        Met à jour la liste des actions disponibles.
        
        Args:
            actions: Liste des actions disponibles
        """
        self.action_combo.clear()
        for action in actions:
            self.action_combo.addItem(action)
    
    def on_start_clicked(self):
        """Gère le clic sur le bouton Démarrer."""
        agent_name = self.agent_combo.currentText()
        self.agent_action_triggered.emit(agent_name, "start", {})
    
    def on_stop_clicked(self):
        """Gère le clic sur le bouton Arrêter."""
        agent_name = self.agent_combo.currentText()
        self.agent_action_triggered.emit(agent_name, "stop", {})
    
    def on_execute_clicked(self):
        """Gère le clic sur le bouton Exécuter."""
        agent_name = self.agent_combo.currentText()
        action_name = self.action_combo.currentText()
        
        # Validation des paramètres JSON
        try:
            params_str = self.params_edit.toPlainText()
            params = json.loads(params_str) if params_str.strip() else {}
            self.agent_action_triggered.emit(agent_name, action_name, params)
        except json.JSONDecodeError:
            QMessageBox.warning(self, "Erreur", "Les paramètres ne sont pas au format JSON valide.")


class AgentMonitorPanel(QWidget):
    """
    Panneau de surveillance des agents.
    """
    
    agent_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
    
    def initUI(self):
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # Table des agents
        self.agents_table = QTableView()
        self.agents_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.agents_table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.agents_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        main_layout.addWidget(QLabel("<b>Agents actifs</b>"))
        main_layout.addWidget(self.agents_table)
        
        # Table des tâches
        self.tasks_table = QTableView()
        self.tasks_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.tasks_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        main_layout.addWidget(QLabel("<b>Tâches récentes</b>"))
        main_layout.addWidget(self.tasks_table)
        
        # Connecter les signaux
        self.agents_table.clicked.connect(self.on_agent_selected)
    
    def set_agents_model(self, model):
        """
        Définit le modèle de données pour la table des agents.
        
        Args:
            model: Modèle de données
        """
        self.agents_table.setModel(model)
    
    def set_tasks_model(self, model):
        """
        Définit le modèle de données pour la table des tâches.
        
        Args:
            model: Modèle de données
        """
        self.tasks_table.setModel(model)
    
    def on_agent_selected(self, index):
        """
        Gère la sélection d'un agent dans la table.
        
        Args:
            index: Index de l'élément sélectionné
        """
        if index.isValid():
            agent_name = self.agents_table.model().data(
                self.agents_table.model().index(index.row(), 0)
            )
            self.agent_selected.emit(agent_name)


class AgentConfigDialog(QDialog):
    """
    Boîte de dialogue pour la configuration d'un agent.
    """
    
    def __init__(self, agent_name: str, config: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.agent_name = agent_name
        self.config = config
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle(f"Configuration de {self.agent_name}")
        self.setMinimumWidth(400)
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # Formulaire de configuration
        form_layout = QFormLayout()
        self.config_widgets = {}
        
        for key, value in self.config.items():
            if isinstance(value, bool):
                widget = QCheckBox()
                widget.setChecked(value)
            else:
                widget = QLineEdit()
                widget.setText(str(value))
                
            form_layout.addRow(key, widget)
            self.config_widgets[key] = widget
        
        main_layout.addLayout(form_layout)
        
        # Boutons de dialogue
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)
    
    def get_config(self) -> Dict[str, Any]:
        """
        Récupère la configuration modifiée.
        
        Returns:
            Dictionnaire de configuration
        """
        result = {}
        for key, widget in self.config_widgets.items():
            if isinstance(widget, QCheckBox):
                result[key] = widget.isChecked()
            else:
                result[key] = widget.text()
                
        return result


class ResultViewerDialog(QDialog):
    """
    Boîte de dialogue pour afficher les résultats d'une action.
    """
    
    def __init__(self, title: str, result: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.title = title
        self.result = result
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setMinimumSize(600, 400)
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # Zone de texte pour les résultats
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setPlainText(json.dumps(self.result, indent=2, ensure_ascii=False))
        
        main_layout.addWidget(self.result_text)
        
        # Bouton de fermeture
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)
