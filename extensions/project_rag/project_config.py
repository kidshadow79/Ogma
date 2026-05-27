"""
project_config.py
-----------------
Gestion de la configuration JSON par projet.
Charge/sauve data/projects/<nom>/project.json
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime


# Chemin racine des projets
PROJECTS_ROOT = Path(__file__).parent.parent.parent / "data" / "projects"

DEFAULT_SETTINGS = {
    "chunk_size_small": 200,      # Tokens pour petit chunk (FAISS search)
    "chunk_size_parent": 800,     # Tokens pour chunk parent (injection LLM)
    "chunk_overlap": 50,          # Overlap entre chunks
    "max_inject_chunks": 3,       # Nombre de chunks injectés par message
    "search_threshold": 0.3,      # Seuil similarité minimum (1/(1+L2_dist) : 0.3 ≈ dist<2.3)
    "cache_ttl": 300,             # TTL semantic cache (secondes)
    "contextual_retrieval": False, # Contextualisation Archiviste (coûteux)
}

DEFAULT_PROJECT = {
    "name": "default",
    "instruction": "",
    "active": False,
    "files": [],
    "settings": DEFAULT_SETTINGS.copy(),
    "created_at": "",
    "updated_at": "",
}


class ProjectConfig:
    """Gestion config JSON d'un projet."""

    def __init__(self, project_name: str = "default"):
        self.project_name = project_name
        self.project_dir = PROJECTS_ROOT / project_name
        self.config_path = self.project_dir / "project.json"
        self.files_dir = self.project_dir / "files"
        self.db_path = self.project_dir / "memory.db"
        self.faiss_path = self.project_dir / "faiss.index"

        # Créer les dossiers si nécessaire
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.files_dir.mkdir(parents=True, exist_ok=True)

        # Charger ou créer la config
        self._config = self._load_or_create()

    def _load_or_create(self) -> Dict[str, Any]:
        """Charge le project.json existant ou en crée un nouveau."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # Migration : ajouter les clés manquantes
                for key, default_val in DEFAULT_PROJECT.items():
                    if key not in config:
                        config[key] = default_val
                for key, default_val in DEFAULT_SETTINGS.items():
                    if key not in config.get("settings", {}):
                        config.setdefault("settings", {})[key] = default_val
                return config
            except Exception as e:
                print(f"[PROJECT-CONFIG] Erreur lecture {self.config_path}: {e}")

        # Création config par défaut
        config = DEFAULT_PROJECT.copy()
        config["name"] = self.project_name
        config["settings"] = DEFAULT_SETTINGS.copy()
        config["created_at"] = datetime.now().isoformat()
        config["updated_at"] = config["created_at"]
        self._save(config)
        return config

    def _save(self, config: Optional[Dict] = None):
        """Sauvegarde la config sur disque."""
        if config is None:
            config = self._config
        config["updated_at"] = datetime.now().isoformat()
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[PROJECT-CONFIG] Erreur sauvegarde: {e}")

    # === Propriétés ===

    @property
    def name(self) -> str:
        return self._config.get("name", self.project_name)

    @property
    def instruction(self) -> str:
        return self._config.get("instruction", "")

    @instruction.setter
    def instruction(self, value: str):
        self._config["instruction"] = value
        self._save()

    @property
    def active(self) -> bool:
        return self._config.get("active", False)

    @active.setter
    def active(self, value: bool):
        self._config["active"] = bool(value)
        self._save()

    @property
    def use_full_cache(self) -> bool:
        return self._config.get("use_full_cache", False)

    @use_full_cache.setter
    def use_full_cache(self, value: bool):
        self._config["use_full_cache"] = bool(value)
        self._save()

    @property
    def files(self) -> List[Dict[str, Any]]:
        return self._config.get("files", [])

    @property
    def settings(self) -> Dict[str, Any]:
        return self._config.get("settings", DEFAULT_SETTINGS.copy())

    # === Gestion fichiers ===

    def add_file_record(self, file_id: str, filename: str, file_type: str,
                        file_size: int, chunk_count: int) -> Dict[str, Any]:
        """Enregistre un fichier dans la config projet."""
        record = {
            "id": file_id,
            "filename": filename,
            "file_type": file_type,
            "file_size": file_size,
            "chunk_count": chunk_count,
            "added_at": datetime.now().isoformat(),
        }
        self._config.setdefault("files", []).append(record)
        self._save()
        print(f"[PROJECT-CONFIG] Fichier ajouté: {filename} ({chunk_count} chunks)")
        return record

    def remove_file_record(self, file_id: str) -> bool:
        """Supprime un fichier de la config projet."""
        files = self._config.get("files", [])
        before = len(files)
        self._config["files"] = [f for f in files if f["id"] != file_id]
        if len(self._config["files"]) < before:
            # Supprimer le fichier physique
            for fpath in self.files_dir.iterdir():
                if fpath.stem.startswith(file_id):
                    try:
                        fpath.unlink()
                    except Exception:
                        pass
            self._save()
            print(f"[PROJECT-CONFIG] Fichier supprimé: {file_id}")
            return True
        return False

    def get_file_record(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Retourne le record d'un fichier par ID."""
        for f in self.files:
            if f["id"] == file_id:
                return f
        return None

    def update_setting(self, key: str, value: Any):
        """Met à jour un paramètre du projet."""
        self._config.setdefault("settings", {})[key] = value
        self._save()

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Récupère un paramètre du projet."""
        return self._config.get("settings", {}).get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """Retourne la config complète comme dict."""
        return self._config.copy()

    def reload(self):
        """Force le rechargement depuis le disque."""
        self._config = self._load_or_create()
