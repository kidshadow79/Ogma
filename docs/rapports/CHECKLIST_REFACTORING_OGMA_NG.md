# CHECKLIST REFACTORING OGMA_NG.PY

**Objectif** : Diviser ogma_ng.py (8183 lignes) en 2 fichiers de ~4000 lignes chacun
- `ogma_ng.py` : Code sensible (mémoire, backends, conversations)
- `ogma_ui_components.py` : Code déplaçable (modales, diagnostics, utilitaires)

---

## 📋 PHASE 1: PRÉPARATION (SÉCURITÉ MAXIMUM)

### ✅ Sauvegarde et environnement
- [ ] **Backup complet** : Copier tout le dossier OGMA vers `OGMA_BACKUP_AVANT_REFACTOR`
- [ ] **Git status** : Vérifier qu'il n'y a pas de modifications non committées
- [ ] **Créer branche** : `git checkout -b refactor-ogma-split`
- [ ] **Test fonctionnel** : Lancer OGMA et vérifier que tout fonctionne avant refactor
- [ ] **Noter la config** : Documenter les paramètres critiques actuels

### ✅ Analyse préliminaire
- [ ] **Compter les lignes** : `powershell -Command "(Get-Content 'ogma_ng.py' | Measure-Object -Line).Lines"`
- [ ] **Identifier imports** : Lister tous les imports en début de fichier
- [ ] **Cartographier les variables globales** : Identifier toutes les variables `_global`
- [ ] **Lister les fonctions critiques** : Confirmer la liste des fonctions sensibles

---

## 🎯 PHASE 2: IDENTIFICATION PRÉCISE

### ✅ Code à GARDER dans ogma_ng.py (SENSIBLE)
- [ ] **Variables globales critiques** : `_settings_mgr`, `_chat_controller`, `_memory_manager`, `_archiviste_controller`
- [ ] **Fonctions backend** : `_ensure_*`, `_list_models`, `_test_connection`
- [ ] **Pipeline conversation** : `_send_chat_message`, `_persist_conversation`, `_load_conversation`
- [ ] **Mémoire** : `_memorize_conversation`, `_retrieve_liberating_memory`
- [ ] **Interface principale** : `main_page()`, `_input_overlay()`, `_message()`
- [ ] **Callbacks critiques** : `_handle_conversation_commands`

#### Fonctions critiques à conserver :
```
- _ensure_settings_manager()
- _ensure_audio_manager()
- _ensure_backends()
- _ensure_memory_manager()
- _ensure_temporal_guardian()
- _ensure_chat_controller()
- _ensure_archiviste_controller()
- _send_chat_message()
- _persist_conversation()
- _load_conversation()
- _memorize_conversation()
- _retrieve_liberating_memory()
- main_page()
- _input_overlay()
- _message()
- _handle_conversation_commands()
- _list_models()
- _test_connection()
- _check_global_ia_status()
- _update_ia_status_indicators()
```

### ✅ Code à DÉPLACER vers ogma_ui_components.py (NON-SENSIBLE)
- [ ] **Modales** : `_settings_hub_modal`, `_models_modal`, `_memory_modal`, `_instructions_modal`
- [ ] **Debug/Diagnostic** : `_diagnostic_leds` (x2), `_test_simple_led`, `_test_gauges`, `_test_led_system`
- [ ] **Utilitaires UI** : `_link_styles`, `_status_dot`, `_truncate_filename`, `_get_file_icon`
- [ ] **Upload fichiers** : `_show_file_upload_dialog`, `_process_uploaded_file`
- [ ] **Édition** : `_edit_memory_popup`, `_edit_summary_popup`

#### Fonctions à déplacer (PRIORITÉ 1 - Plus sûres) :
```
- _diagnostic_leds() [ligne 7885]
- _diagnostic_leds() [ligne 7965] ⚠️ DOUBLON À CORRIGER
- _test_simple_led()
- _test_gauges()
- _test_led_system()
- _update_led_gauges()
- _init_metacognition_state()
```

#### Fonctions à déplacer (PRIORITÉ 2 - Utilitaires) :
```
- _link_styles()
- _status_dot()
- _truncate_filename()
- _get_file_icon()
- _format_datetime()
- _parse_thinking_format()
```

#### Fonctions à déplacer (PRIORITÉ 3 - Modales simples) :
```
- _instructions_modal()
- _image_modal()
- _perception_modal()
- _profile_modal()
- _archi_sensor_modal()
```

#### Fonctions à déplacer (PRIORITÉ 4 - Modales complexes) :
```
- _settings_hub_modal()
- _models_modal()
- _memory_modal()
- _edit_memory_popup()
- _edit_summary_popup()
- _memorization_popup()
- _create_edit_interface()
- _edit_summary_popup()
```

#### Fonctions à déplacer (PRIORITÉ 5 - Upload/Fichiers) :
```
- _show_file_upload_dialog()
- _process_uploaded_file()
- _handle_upload_and_close()
- _process_uploaded_file_and_close()
```

---

## 🔄 PHASE 3: EXÉCUTION PAS À PAS

### ✅ Étape 1: Créer le fichier de composants
- [ ] **Créer** `ogma_ui_components.py` vide
- [ ] **Copier les imports** nécessaires depuis ogma_ng.py
- [ ] **Ajouter** commentaire d'en-tête explicatif

```python
"""
OGMA UI Components
==================
Composants d'interface utilisateur déplacés depuis ogma_ng.py
pour améliorer la maintenabilité du code.

Ce fichier contient :
- Modales et dialogues
- Fonctions de diagnostic et debug
- Utilitaires d'interface
- Composants non-critiques

Le code sensible (backends, mémoire, conversations) reste dans ogma_ng.py
"""
```

### ✅ Étape 2: Déplacer par blocs (ORDRE IMPORTANT)

#### ✅ **Bloc 1** : Fonctions de diagnostic/debug (le plus sûr)
- [ ] `_diagnostic_leds` (ligne 7885)
- [ ] `_diagnostic_leds` (ligne 7965) ⚠️ **RÉSOUDRE LE DOUBLON**
- [ ] `_test_simple_led`, `_test_gauges`, `_test_led_system`
- [ ] `_update_led_gauges`, `_init_metacognition_state`
- [ ] **Test** : Vérifier que OGMA démarre toujours

#### ✅ **Bloc 2** : Utilitaires simples
- [ ] `_link_styles`, `_status_dot`, `_truncate_filename`
- [ ] `_get_file_icon`, `_format_datetime`, `_parse_thinking_format`
- [ ] **Test** : Vérifier affichage des messages et interface

#### ✅ **Bloc 3** : Modales autonomes
- [ ] `_instructions_modal`, `_image_modal`, `_perception_modal`
- [ ] `_profile_modal`, `_archi_sensor_modal`
- [ ] **Test** : Vérifier ouverture des modales

#### ✅ **Bloc 4** : Modales avec dépendances légères
- [ ] `_settings_hub_modal`, `_memory_modal`, `_models_modal`
- [ ] `_edit_memory_popup`, `_edit_summary_popup`
- [ ] **Test** : Vérifier fonctionnement complet des paramètres

#### ✅ **Bloc 5** : Upload de fichiers
- [ ] `_show_file_upload_dialog`, `_process_uploaded_file`
- [ ] `_handle_upload_and_close`, `_process_uploaded_file_and_close`
- [ ] **Test** : Vérifier upload et traitement des fichiers

### ✅ Étape 3: Ajuster les imports
- [ ] **Dans ogma_ng.py** : Ajouter `from ogma_ui_components import *` après les autres imports
- [ ] **Dans ogma_ui_components.py** : Importer les dépendances nécessaires
- [ ] **Résoudre les imports circulaires** si nécessaire
- [ ] **Vérifier variables globales** : S'assurer qu'elles sont accessibles

### ✅ Étape 4: Tests progressifs
- [ ] **Test après chaque bloc** : Lancer OGMA et vérifier fonctionnement
- [ ] **Test fonctions déplacées** : Vérifier que les modales s'ouvrent
- [ ] **Test diagnostics** : Vérifier que les LEDs fonctionnent
- [ ] **Test upload** : Vérifier traitement des fichiers

---

## 🧪 PHASE 4: VALIDATION COMPLÈTE

### ✅ Tests fonctionnels essentiels
- [ ] **Lancement** : OGMA démarre sans erreur
- [ ] **Chat** : Envoyer un message, recevoir une réponse
- [ ] **Mémoire** : Vérifier sauvegarde/rappel des souvenirs
- [ ] **Modales** : Ouvrir paramètres, mémoire, instructions
- [ ] **Audio** : Test enregistrement/lecture si configuré
- [ ] **Backends** : Test connexion API/Ollama si configuré
- [ ] **Upload** : Test upload de fichier PDF/image
- [ ] **Diagnostics** : Test activation des LEDs métacognitives

### ✅ Vérifications techniques
- [ ] **Compter lignes** finales :
  - ogma_ng.py ~4000 lignes : `powershell -Command "(Get-Content 'ogma_ng.py' | Measure-Object -Line).Lines"`
  - ogma_ui_components.py ~4000 lignes : `powershell -Command "(Get-Content 'ogma_ui_components.py' | Measure-Object -Line).Lines"`
- [ ] **Imports résolus** : Aucune erreur d'import
- [ ] **Variables globales** : Accessibles depuis les deux fichiers
- [ ] **Performance** : Temps de démarrage similaire
- [ ] **Pas de régression** : Toutes les fonctionnalités opérationnelles

### ✅ Tests de régression spécifiques
- [ ] **Conversation** : Créer nouvelle conversation, charger ancienne
- [ ] **Mémorisation** : Mémoriser une conversation, la retrouver
- [ ] **Paramètres** : Modifier paramètres IA, tester connexion
- [ ] **Temporal Guardian** : Vérifier enrichissement temporel
- [ ] **Extensions** : Tester archi_sensor, perception si activés

---

## 🚨 SÉCURITÉS ET ROLLBACK

### ✅ Points d'arrêt obligatoires
- [ ] **Si erreur critique** : Arrêter immédiatement, revenir au backup
- [ ] **Si >50% fonctions cassées** : Rollback complet
- [ ] **Si impossible résoudre imports** : Revenir à l'original
- [ ] **Si performance dégradée >20%** : Investiguer ou rollback

### ✅ Plan de rollback
- [ ] **Commande rapide** : `cp -r OGMA_BACKUP_AVANT_REFACTOR/* ./`
- [ ] **Git reset** : `git checkout main && git branch -D refactor-ogma-split`
- [ ] **Test post-rollback** : Vérifier retour à l'état initial
- [ ] **Documentation** : Noter les problèmes rencontrés

### ✅ Signaux d'alerte
- ⚠️ **Erreurs d'import** persistantes après 15min de debug
- ⚠️ **Variables globales** non accessibles
- ⚠️ **Interface** ne se charge pas correctement
- ⚠️ **Fonctions critiques** (chat, mémoire) cassées

---

## 📊 MÉTRIQUES DE SUCCÈS

### ✅ Objectifs quantifiables
- [ ] **Réduction lignes** : ogma_ng.py passe de 8183 à ~4000 lignes (-50%)
- [ ] **Fonctionnalité** : 100% des fonctions critiques opérationnelles
- [ ] **Stabilité** : Aucune régression fonctionnelle
- [ ] **Maintenabilité** : Code debug/modal séparé du code critique
- [ ] **Performance** : Temps de démarrage <+10% par rapport à l'original

### ✅ Critères de validation
- [ ] **Conversation fluide** : Chat fonctionne normalement
- [ ] **Mémoire persistante** : Sauvegarde/rappel opérationnel
- [ ] **Interface complète** : Toutes les modales accessibles
- [ ] **Code propre** : Suppression du doublon `_diagnostic_leds`
- [ ] **Documentation** : Commentaires clairs sur la séparation

---

## 🎯 ORDRE D'EXÉCUTION RECOMMANDÉ

### Phase d'exécution optimale :
1. ✅ **SAUVEGARDE** : Backup + branche Git
2. ✅ **DIAGNOSTIC FIRST** : Commencer par les fonctions de test (le plus sûr)
3. ✅ **UTILITAIRES** : Fonctions simples sans dépendances
4. ✅ **MODALES SIMPLES** : Interfaces autonomes
5. ✅ **MODALES COMPLEXES** : Avec dépendances légères
6. ✅ **UPLOAD** : Fonctions de traitement de fichiers
7. ✅ **VALIDATION CONTINUE** : Tester après chaque bloc
8. ✅ **VALIDATION FINALE** : Tests complets + métriques

### Temps estimé :
- **Préparation** : 30 minutes
- **Exécution** : 2-3 heures (avec tests)
- **Validation** : 1 heure
- **Total** : 3-4 heures

---

## ⚠️ NOTES IMPORTANTES

### Points critiques à surveiller :
1. **Doublon `_diagnostic_leds`** : Résoudre avant déplacement
2. **Variables globales** : Vérifier accessibilité depuis les deux fichiers
3. **Imports circulaires** : Éviter les dépendances croisées
4. **Tests continus** : Ne jamais déplacer plus d'un bloc sans tester

### Structure finale attendue :
```
ogma_ng.py (~4000 lignes)
├── Imports + from ogma_ui_components import *
├── Variables globales critiques
├── Fonctions backend (_ensure_*)
├── Pipeline conversation (_send_chat_message, etc.)
├── Gestion mémoire
├── Interface principale (main_page, _input_overlay, _message)
└── Fonction run_ogma()

ogma_ui_components.py (~4000 lignes)
├── Imports nécessaires
├── Fonctions de diagnostic/debug
├── Utilitaires d'interface
├── Modales et dialogues
└── Fonctions d'upload/édition
```

Cette approche garantit une **sécurité maximale** tout en atteignant l'objectif de **division du fichier monolithique** !