# gui/models.py
"""
Modèles de données pour l'interface graphique.
"""

from PyQt6.QtCore import QAbstractTableModel, Qt, QModelIndex
from typing import List, Dict, Any, Optional


class AgentTableModel(QAbstractTableModel):
    """
    Modèle pour afficher la liste des agents dans un tableau.
    """
    
    def __init__(self, agents_data: List[Dict[str, Any]] = None):
        """
        Initialise le modèle avec les données des agents.
        
        Args:
            agents_data: Liste des données des agents
        """
        super().__init__()
        self._agents_data = agents_data or []
        self._headers = ["Nom", "Type", "Statut", "Tâches en attente"]
    
    def rowCount(self, parent=QModelIndex()) -> int:
        """Renvoie le nombre de lignes."""
        return len(self._agents_data)
    
    def columnCount(self, parent=QModelIndex()) -> int:
        """Renvoie le nombre de colonnes."""
        return len(self._headers)
    
    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        """Renvoie les données à afficher."""
        if not index.isValid() or not (0 <= index.row() < len(self._agents_data)):
            return None
            
        row = index.row()
        col = index.column()
        agent = self._agents_data[row]
        
        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return agent.get("name", "")
            elif col == 1:
                return agent.get("type", "")
            elif col == 2:
                return "Actif" if agent.get("running", False) else "Inactif"
            elif col == 3:
                return str(agent.get("tasks_pending", 0))
        
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col in [2, 3]:
                return Qt.AlignmentFlag.AlignCenter
        
        return None
    
    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole):
        """Renvoie les en-têtes du tableau."""
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._headers[section]
        return None
    
    def update_data(self, agents_data: List[Dict[str, Any]]):
        """
        Met à jour les données du modèle.
        
        Args:
            agents_data: Nouvelles données des agents
        """
        self.beginResetModel()
        self._agents_data = agents_data
        self.endResetModel()


class TasksTableModel(QAbstractTableModel):
    """
    Modèle pour afficher les tâches des agents dans un tableau.
    """
    
    def __init__(self, tasks_data: List[Dict[str, Any]] = None):
        """
        Initialise le modèle avec les données des tâches.
        
        Args:
            tasks_data: Liste des données des tâches
        """
        super().__init__()
        self._tasks_data = tasks_data or []
        self._headers = ["ID", "Agent", "Action", "Statut", "Date de création"]
    
    def rowCount(self, parent=QModelIndex()) -> int:
        """Renvoie le nombre de lignes."""
        return len(self._tasks_data)
    
    def columnCount(self, parent=QModelIndex()) -> int:
        """Renvoie le nombre de colonnes."""
        return len(self._headers)
    
    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        """Renvoie les données à afficher."""
        if not index.isValid() or not (0 <= index.row() < len(self._tasks_data)):
            return None
            
        row = index.row()
        col = index.column()
        task = self._tasks_data[row]
        
        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return task.get("id", "")
            elif col == 1:
                return task.get("agent_name", "")
            elif col == 2:
                return task.get("action", "")
            elif col == 3:
                return task.get("status", "")
            elif col == 4:
                return task.get("created_at", "")
        
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col in [3, 4]:
                return Qt.AlignmentFlag.AlignCenter
        
        return None
    
    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole):
        """Renvoie les en-têtes du tableau."""
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._headers[section]
        return None
    
    def update_data(self, tasks_data: List[Dict[str, Any]]):
        """
        Met à jour les données du modèle.
        
        Args:
            tasks_data: Nouvelles données des tâches
        """
        self.beginResetModel()
        self._tasks_data = tasks_data
        self.endResetModel()
