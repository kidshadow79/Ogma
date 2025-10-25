"""
TEMPLATE FEATURE OGMA V2
========================

INSTRUCTIONS:
1. Copier ce fichier: extensions/ogma_ng_v2/features/ma_feature/__init__.py
2. Renommer toutes les occurrences de "template_feature" par votre nom
3. Implémenter initialize_feature() avec votre logique
4. Ajouter dans extensions/ogma_ng_v2/__init__.py:
   from .features.ma_feature import initialize_feature
   status['ma_feature'] = initialize_feature(dependencies)

EXEMPLE UTILISATION:
    from extensions.ogma_ng_v2.features.ma_feature import initialize_feature
    
    deps = {
        'chat_controller': chat_ctrl,
        'memory_manager': mem_mgr,
        ...
    }
    
    success = initialize_feature(deps)
"""

# Global state (singleton pattern)
_feature_instance = None
_is_initialized = False


def initialize_feature(dependencies=None):
    """
    Initialise la feature avec les dépendances OGMA.
    
    Args:
        dependencies (dict): Dépendances OGMA
            - chat_controller (AIController): Contrôleur IA principal
            - archiviste_controller (AIController): Contrôleur IA archiviste
            - memory_manager (MemoryManager): Gestionnaire mémoire
            - settings_manager (SettingsManager): Gestionnaire config
            - audio_manager (AudioManager): Gestionnaire audio
            
    Returns:
        bool: True si initialisation réussie
    """
    global _feature_instance, _is_initialized
    
    print("[TEMPLATE-FEATURE] 🚀 Initialisation...")
    
    # Vérifier si déjà initialisé (singleton)
    if _is_initialized:
        print("[TEMPLATE-FEATURE] ⚠️  Déjà initialisé")
        return True
    
    try:
        # Extraire dépendances (si fournies)
        if dependencies:
            chat_controller = dependencies.get('chat_controller')
            memory_manager = dependencies.get('memory_manager')
            # ... autres dépendances
            
            # Validation dépendances critiques
            if not chat_controller:
                print("[TEMPLATE-FEATURE] ❌ Erreur: chat_controller requis")
                return False
        
        # TODO: Votre logique d'initialisation ici
        # Exemples:
        # - Créer instances classes
        # - Charger configuration
        # - Initialiser state
        # - Enregistrer callbacks
        
        # Simuler initialisation réussie
        _feature_instance = {
            "status": "initialized",
            "version": "1.0.0"
        }
        
        _is_initialized = True
        print("[TEMPLATE-FEATURE] ✅ Initialisé avec succès")
        return True
        
    except Exception as e:
        print(f"[TEMPLATE-FEATURE] ❌ Erreur initialisation: {e}")
        return False


def is_available():
    """
    Vérifie si la feature est disponible.
    
    Returns:
        bool: True si feature initialisée et disponible
    """
    return _is_initialized


def get_ui_components():
    """
    Retourne composants UI pour intégration dans OGMA.
    
    Returns:
        dict: Composants UI
            - header_button (callable): Bouton header (optionnel)
            - modal (callable): Modal settings (optionnel)
            - sidebar_section (callable): Section sidebar (optionnel)
    """
    if not _is_initialized:
        return {}
    
    # TODO: Retourner vos composants UI
    # Exemple:
    # return {
    #     'header_button': _create_header_button,
    #     'modal': _create_settings_modal
    # }
    
    return {}


def get_feature_info():
    """
    Retourne informations sur la feature.
    
    Returns:
        dict: Informations feature
    """
    return {
        "name": "template_feature",
        "version": "1.0.0",
        "author": "Votre Nom",
        "description": "Description de votre feature",
        "initialized": _is_initialized,
        "dependencies": ["chat_controller"]  # Liste dépendances requises
    }


def cleanup():
    """
    Nettoyage propre de la feature.
    
    Appelé lors de l'arrêt d'OGMA ou désactivation feature.
    """
    global _feature_instance, _is_initialized
    
    print("[TEMPLATE-FEATURE] 🧹 Nettoyage...")
    
    # TODO: Votre logique de nettoyage
    # Exemples:
    # - Sauvegarder état
    # - Fermer connexions
    # - Libérer ressources
    
    _feature_instance = None
    _is_initialized = False
    
    print("[TEMPLATE-FEATURE] ✅ Nettoyage terminé")


# Fonctions publiques de votre feature (API)
def votre_fonction_publique():
    """
    Fonction publique accessible depuis OGMA.
    
    TODO: Implémenter votre logique
    """
    if not _is_initialized:
        print("[TEMPLATE-FEATURE] ⚠️  Feature non initialisée")
        return None
    
    # Votre code ici
    return True


# Exemple: Magic Phrases Handler
def check_magic_phrases(text, source="user"):
    """
    Détecte phrases magiques pour activer la feature.
    
    Args:
        text (str): Texte à analyser
        source (str): 'user' ou 'assistant'
        
    Returns:
        bool: True si phrase magique détectée
    """
    if not _is_initialized:
        return False
    
    # TODO: Votre détection phrases magiques
    # Exemple:
    # patterns = [
    #     r"active ma feature",
    #     r"lance template"
    # ]
    # for pattern in patterns:
    #     if re.search(pattern, text, re.IGNORECASE):
    #         return True
    
    return False


# Exemple: Hook Extension
def on_message_received(message_data):
    """
    Hook appelé quand message reçu (user ou IA).
    
    Args:
        message_data (dict): Données message
            - role (str): 'user' ou 'assistant'
            - content (str): Contenu message
            - metadata (dict): Metadata
    """
    if not _is_initialized:
        return
    
    # TODO: Votre traitement message
    pass


# --- EXEMPLE CODE MÉTIER ---
# Mettre votre logique métier dans des fonctions privées

def _votre_logique_interne():
    """Fonction privée (interne feature uniquement)."""
    pass


class VotreClasseMetier:
    """Classe métier de votre feature."""
    
    def __init__(self):
        """Initialisation."""
        self.state = {}
    
    def process(self, data):
        """Traite des données."""
        return data
