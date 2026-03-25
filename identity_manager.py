"""
OGMA Identity Manager v1.0
===========================
Gestion dynamique des identités utilisateur/IA pour un système multi-user.

REMPLACE : Toutes les références codées en dur "Yohan" et "Luna"
PERMET : Configuration flexible pour différents utilisateurs et IA
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

class IdentityManager:
    """
    Gestionnaire des identités utilisateur/IA pour OGMA
    
    Structure des données:
    {
        "current_profile": "profile_1",
        "profiles": {
            "profile_1": {
                "user_name": "Utilisateur",
                "ai_name": "Assistant", 
                "ai_description": "IA conversationnelle",
                "relationship_type": "collaborative",
                "relationship_context": "Tu dialogues avec {user_name}, avec qui tu as un historique conversationnel",
                "created_at": "2025-10-11T15:30:00",
                "last_used": "2025-10-11T15:30:00"
            }
        },
        "defaults": {
            "user_name": "Utilisateur",
            "ai_name": "Assistant", 
            "ai_description": "Assistant IA",
            "relationship_type": "professional",
            "relationship_context": "Tu dialogues avec {user_name} dans un contexte professionnel"
        }
    }
    """
    
    def __init__(self, config_path: str = "data/identities.json"):
        self.config_path = Path(config_path)
        self._data = None
        self.load_identities()
    
    def load_identities(self) -> None:
        """Charge la configuration des identités depuis le fichier"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._data = json.load(f)
            else:
                # Créer configuration par défaut si fichier n'existe pas
                self._data = self._create_default_config()
                self.save_identities()
        except Exception as e:
            print(f"[IDENTITY-MANAGER] ERROR Chargement identités: {e}")
            self._data = self._create_default_config()
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Crée la configuration par défaut"""
        from datetime import datetime
        
        now = datetime.now().isoformat()
        
        return {
            "current_profile": "default",
            "profiles": {
                "default": {
                    "user_name": "Utilisateur",
                    "ai_name": "Assistant",
                    "ai_description": "Assistant IA polyvalent",
                    "relationship_type": "professional",
                    "relationship_context": "Tu dialogues avec {user_name} dans un contexte professionnel et bienveillant",
                    "created_at": now,
                    "last_used": now,
                    "description": "Profil par défaut OGMA"
                }
            },
            "defaults": {
                "user_name": "Utilisateur",
                "ai_name": "Assistant",
                "ai_description": "Assistant IA polyvalent",
                "relationship_type": "professional", 
                "relationship_context": "Tu dialogues avec {user_name} dans un contexte professionnel et bienveillant"
            }
        }
    
    def save_identities(self) -> None:
        """Sauvegarde la configuration des identités"""
        try:
            # Créer le répertoire si nécessaire
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[IDENTITY-MANAGER] ERROR Sauvegarde identités: {e}")
    
    def get_current_identity(self) -> Dict[str, str]:
        """
        Récupère les identités du profil actuel
        
        Returns:
            Dict avec user_name, ai_name, ai_description, relationship_context, etc.
        """
        current_profile_id = self._data.get("current_profile")
        
        if current_profile_id and current_profile_id in self._data.get("profiles", {}):
            profile = self._data["profiles"][current_profile_id]
            # Formater relationship_context avec le nom utilisateur
            relationship_context = profile.get("relationship_context", "").format(
                user_name=profile.get("user_name", "Utilisateur")
            )
            
            return {
                "user_identity": profile.get("user_name", self._data["defaults"]["user_name"]),
                "user_name": profile.get("user_name", self._data["defaults"]["user_name"]),
                "main_ai_identity": profile.get("ai_description", self._data["defaults"]["ai_description"]),
                "ai_name": profile.get("ai_name", self._data["defaults"]["ai_name"]),
                "ai_description": profile.get("ai_description", self._data["defaults"]["ai_description"]),
                "relationship_context": relationship_context,
                "relationship_type": profile.get("relationship_type", self._data["defaults"]["relationship_type"])
            }
        else:
            # Utiliser les defaults si aucun profil actuel
            defaults = self._data["defaults"]
            relationship_context = defaults["relationship_context"].format(
                user_name=defaults["user_name"]
            )
            
            return {
                "user_identity": defaults["user_name"],
                "user_name": defaults["user_name"], 
                "main_ai_identity": defaults["ai_description"],
                "ai_name": defaults["ai_name"],
                "ai_description": defaults["ai_description"],
                "relationship_context": relationship_context,
                "relationship_type": defaults["relationship_type"]
            }
    
    def get_user_name(self) -> str:
        """Récupère le nom d'utilisateur actuel"""
        return self.get_current_identity()["user_name"]
    
    def get_ai_name(self) -> str:
        """Récupère le nom de l'IA actuelle"""
        return self.get_current_identity()["ai_name"]
    
    def create_profile(self, profile_id: str, user_name: str, ai_name: str = None, 
                      ai_description: str = None, relationship_type: str = "collaborative",
                      relationship_context: str = None) -> bool:
        """
        Crée un nouveau profil d'identité
        
        Args:
            profile_id: Identifiant unique du profil
            user_name: Nom de l'utilisateur
            ai_name: Nom de l'IA (optionnel)
            ai_description: Description de l'IA (optionnel)
            relationship_type: Type de relation (professional, collaborative, intime, etc.)
            relationship_context: Contexte relationnel personnalisé
        
        Returns:
            True si créé avec succès
        """
        from datetime import datetime
        
        if profile_id in self._data.get("profiles", {}):
            print(f"[IDENTITY-MANAGER] WARNING Profil {profile_id} existe déjà")
            return False
        
        # Valeurs par défaut intelligentes
        if not ai_name:
            ai_name = self._data["defaults"]["ai_name"]
        if not ai_description:
            ai_description = self._data["defaults"]["ai_description"]
        if not relationship_context:
            relationship_context = f"Tu dialogues avec {{user_name}}, dans une relation {relationship_type}"
        
        profile = {
            "user_name": user_name,
            "ai_name": ai_name,
            "ai_description": ai_description,
            "relationship_type": relationship_type,
            "relationship_context": relationship_context,
            "created_at": datetime.now().isoformat(),
            "last_used": datetime.now().isoformat(),
            "description": f"Profil {user_name} ↔ {ai_name}"
        }
        
        if "profiles" not in self._data:
            self._data["profiles"] = {}
        
        self._data["profiles"][profile_id] = profile
        self.save_identities()
        
        print(f"[IDENTITY-MANAGER] ✅ Profil créé: {profile_id} ({user_name} ↔ {ai_name})")
        return True
    
    def switch_profile(self, profile_id: str) -> bool:
        """
        Bascule vers un profil différent
        
        Args:
            profile_id: ID du profil à activer
            
        Returns:
            True si basculé avec succès
        """
        if profile_id not in self._data.get("profiles", {}):
            print(f"[IDENTITY-MANAGER] ERROR Profil {profile_id} introuvable")
            return False
        
        from datetime import datetime
        
        self._data["current_profile"] = profile_id
        self._data["profiles"][profile_id]["last_used"] = datetime.now().isoformat()
        self.save_identities()
        
        identity = self.get_current_identity()
        print(f"[IDENTITY-MANAGER] ✅ Profil activé: {identity['user_name']} ↔ {identity['ai_name']}")
        return True
    
    def list_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Retourne tous les profils disponibles"""
        return self._data.get("profiles", {})
    
    def get_current_profile_id(self) -> Optional[str]:
        """Retourne l'ID du profil actuel"""
        return self._data.get("current_profile")
    
    def delete_profile(self, profile_id: str) -> bool:
        """
        Supprime un profil (sauf s'il est actuel)
        
        Args:
            profile_id: ID du profil à supprimer
            
        Returns:
            True si supprimé avec succès
        """
        if profile_id not in self._data.get("profiles", {}):
            return False
        
        if self._data.get("current_profile") == profile_id:
            print(f"[IDENTITY-MANAGER] ERROR Impossible de supprimer le profil actuel")
            return False
        
        del self._data["profiles"][profile_id]
        self.save_identities()
        print(f"[IDENTITY-MANAGER] ✅ Profil supprimé: {profile_id}")
        return True


# Instance globale du gestionnaire d'identités
_identity_manager = None

def get_identity_manager() -> IdentityManager:
    """Récupère l'instance globale du gestionnaire d'identités"""
    global _identity_manager
    if _identity_manager is None:
        _identity_manager = IdentityManager()
    return _identity_manager

def get_current_user_name() -> str:
    """Fonction utilitaire pour récupérer le nom utilisateur actuel"""
    return get_identity_manager().get_user_name()

def get_current_ai_name() -> str:
    """Fonction utilitaire pour récupérer le nom IA actuel"""
    return get_identity_manager().get_ai_name()

def get_current_identities() -> Dict[str, str]:
    """Fonction utilitaire pour récupérer toutes les identités actuelles"""
    return get_identity_manager().get_current_identity()


if __name__ == "__main__":
    # Test du système
    print("=== TEST IDENTITY MANAGER ===")
    
    manager = IdentityManager()
    
    # Test profil par défaut
    identity = manager.get_current_identity()
    print(f"Profil actuel: {identity['user_name']} ↔ {identity['ai_name']}")
    
    # Test création nouveau profil
    manager.create_profile(
        profile_id="marie_aria",
        user_name="Marie",
        ai_name="Aria", 
        ai_description="IA créative et empathique",
        relationship_type="collaborative",
        relationship_context="Tu travailles en collaboration avec {user_name} sur des projets créatifs"
    )
    
    # Test basculement
    manager.switch_profile("marie_aria")
    identity = manager.get_current_identity()
    print(f"Nouveau profil: {identity['user_name']} ↔ {identity['ai_name']}")
    
    # Test liste profils
    profiles = manager.list_profiles()
    print(f"Profils disponibles: {list(profiles.keys())}")