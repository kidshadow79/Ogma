# Cognitive Mirror - API Publique Extraite

**Date d'extraction** : extract_cognitive_api
**Fichier source** : `extensions/cognitive_mirror/__init__.py`
**Total fonctions publiques** : 16
**Version Extension** : v2.0.0 (Introspection)

---

## 📊 Statistiques

- **Fonctions synchrones** : 15
- **Fonctions asynchrones** : 1

### Répartition par catégorie

- **API Commune** : 6 fonction(s)
- **API Legacy (Compatibilité)** : 5 fonction(s)
- **API v2.0 (Nouveau)** : 5 fonction(s)

---

## 📋 Fonctions par Catégorie

### API v2.0 (Nouveau)

#### `initialize_introspection(chat_controller, archiviste_controller, memory_manager, ui_container = None)`

**Ligne** : 70  
**Retour** : `Any`

**Description** :
> Initialise l'extension Introspection v2.0 (NOUVEAU)

Args:
    chat_controller: Instance AIController (Luna/IA principale)
    archiviste_controller: Instance AIController (Archiviste)
    memory_manager: Instance MemoryManager
    ui_container: Container UI NiceGUI (optionnel)

Returns:
    bool: True si initialisation réussie

#### `get_introspection()`

**Ligne** : 117  
**Retour** : `'IntrospectionCore'`

**Description** :
> Retourne l'instance singleton IntrospectionCore v2.0

Returns:
    IntrospectionCore ou None

#### `async process_user_message(user_message: str, conversation_context: dict)`

**Ligne** : 212  
**Retour** : `Any`

**Description** :
> Traite message utilisateur avec introspection si nécessaire

Args:
    user_message: Message utilisateur
    conversation_context: Contexte conversationnel

Returns:
    Réponse enrichie ou None

#### `check_magic_phrases(text: str, source: str = 'user')`

**Ligne** : 228  
**Retour** : `Any`

**Description** :
> Vérifie phrases magiques dans texte

Args:
    text: Texte à vérifier
    source: "user" ou "ia"

Returns:
    Type phrase ("trigger", "stop") ou None

#### `stop_current_introspection(reason: str = 'external')`

**Ligne** : 244  
**Retour** : `Any`

**Description** :
> Arrête introspection en cours

Args:
    reason: Raison arrêt

### API Legacy (Compatibilité)

#### `initialize_cognitive_mirror(chat_controller, archiviste_controller, memory_manager, ui_container = None)`

**Ligne** : 131  
**Retour** : `Any`

**Description** :
> Initialise extension (LEGACY - redirige vers v2.0)

Maintenue pour compatibilité avec code OGMA existant.
Utilise le nouveau système Introspection v2.0 en arrière-plan.

Args:
    chat_controller: Instance AIController
    archiviste_controller: Instance AIController
    memory_manager: Instance MemoryManager
    ui_container: Container UI (optionnel)

Returns:
    bool: True si succès

#### `get_cognitive_mirror()`

**Ligne** : 150  
**Retour** : `Any`

**Description** :
> Retourne instance core (LEGACY - redirige vers v2.0)

Returns:
    IntrospectionCore ou None

#### `get_reflection_context()`

**Ligne** : 267  
**Retour** : `Any`

**Description** :
> LEGACY - Obsolète en v2.0

#### `start_inactivity_monitoring()`

**Ligne** : 272  
**Retour** : `Any`

**Description** :
> LEGACY - Obsolète en v2.0 (pas de détection auto)

#### `stop_reflection_session()`

**Ligne** : 277  
**Retour** : `Any`

**Description** :
> LEGACY - Redirige vers stop_current_introspection()

### API Commune

#### `is_available()`

**Ligne** : 160  
**Retour** : `bool`

**Description** :
> Vérifie si extension disponible

#### `is_enabled()`

**Ligne** : 165  
**Retour** : `bool`

**Description** :
> Vérifie si extension activée

#### `toggle_enabled()`

**Ligne** : 171  
**Retour** : `bool`

**Description** :
> Bascule état ON/OFF

Returns:
    bool: Nouvel état

#### `get_ui_components()`

**Ligne** : 183  
**Retour** : `Any`

**Description** :
> Retourne composants UI pour intégration OGMA

Returns:
    CognitiveMirrorUI ou None

#### `get_extension_status()`

**Ligne** : 195  
**Retour** : `Any`

**Description** :
> Retourne statut détaillé extension

Returns:
    dict: Statut complet

#### `cleanup()`

**Ligne** : 255  
**Retour** : `Any`

**Description** :
> Nettoyage et fermeture propre
