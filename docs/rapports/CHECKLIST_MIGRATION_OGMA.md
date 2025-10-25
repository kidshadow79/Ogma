# ✅ Checklist Migration OGMA (Gradio → NiceGUI) & Backend

Cette checklist est la référence d'avancement. Avant chaque session, la consulter puis cocher/mettre à jour. Les IDs entre parenthèses servent de repères stables.

Légende: [ ] À faire  | [~] En cours | [x] Fait | [!] Bloquant | [n] Note

Dernière mise à jour: 2025-09-02 (Audit Complet Claude)

## 🧭 Jalons (Milestones)
- [x] M0: Baseline stable (backend intact, NiceGUI démarre)
- [x] M1: Chat NiceGUI pleinement fonctionnel (config API testée, réponses)
- [x] M2: Mémoire v2 branchée au chat (triggers + CRUD opérationnels; injection contexte ✅)
- [x] M2.5: Instructions système intégrées (interface complète + 6 instructions)
- [~] M3: Conversations persistantes (CRUD + index) côté NiceGUI - Backend ✅, Frontend partiel
- [ ] M4: Upload fichiers + Perception Agent intégrés NiceGUI
- [ ] M5: Découplage complet du backend (plus d'import Gradio hors UI Gradio)
- [ ] M6: QA/tests min + docs nettes, nettoyage Gradio legacy

## 🚀 Lancement & Environnement
- [x] (NG-00) Wrapper `ogma_app.py` exposant `run_ogma`
- [ ] (NG-01) Vérifier `launch_ogma.py` (Windows PowerShell) fin-à-fin (install dépendances + lancement)
  - [n] Utilise nicegui>=1.4.0, faiss-cpu, sqlalchemy; .env optionnel

## 🎛️ Interface NiceGUI (ogma_ng.py)
- [x] (NG-02) Base UI NiceGUI présente (header, sidebar, chat overlay)
- [x] (NG-03) MemoryManager initialisé (SQLite/FAISS) et utilisé par l'UI
- [x] (NG-04) Injection de contexte: `retrieve_and_synthesize_context` intégré dans le flux de chat ✅
- [x] (NG-05) Persister conversations (save sur envoi/réponse) + mise à jour `data/conversations/index.json` ✅
- [ ] (NG-06) Paramétrage providers/modèles: vérifier "Rafraîchir modèles" + "Tester" pour API/Ollama/GGUF/Kobold
- [x] (NG-07) Triggers de mémorisation (utilisateur/assistant) + badge "mémorisé"
- [x] (NG-08) Modal mémoire: CRUD + bouton "Recalculer via Archiviste"
- [x] (NG-09) Contraintes UI des métriques [0..1] pas 0.1
- [x] (NG-10) Interface Instructions Système: 6 instructions avec preview cards + popups éditeurs ✅

## 🧠 Backend & Découplage
- [!] (BE-01) Extraire un "service layer" UI-agnostique depuis `logic_callbacks.py` (chat/memo/recherche/convos)
- [!] (BE-02) Retirer import Gradio des modules considérés backend; garder un adaptateur Gradio séparé si besoin
  - [n] Cibles principales: `logic_callbacks.py` (nombreux `gr.update()`, `gr.Info()`) - BLOQUE M5

## 💾 Mémoire v2 (SQLite + FAISS)
- [x] (MM-00) Implémentation `MemoryManager` OK (logs, locks, sauvegarde index)
- [x] (MM-01) Mémorisation via UI NiceGUI (triggers → `add_memory`) opérationnelle
- [x] (MM-02) Recherche/synthèse contextuelle prête côté backend; à insérer dans le flux de chat NiceGUI ✅
- [x] (MM-03) Suppression mémoire → suppression SQLite + rebuild FAISS
- [x] (MM-04) Ré-enrichissement via Archiviste (update + re-embed + rebuild FAISS)
- [x] (MM-05) Scoring 100% IA; alias `score`→`score_impact`; prompt corrigé (accolades)

## 👁️ Perception & 📎 Upload
- [ ] (UX-01) Bouton Upload NiceGUI: intégrer `extensions/file_processor.py`
- [ ] (UX-02) PerceptionAgent: start/stop + messages d’état (via notifications)

## 🔔 Statuts & Logs
- [ ] (LOG-01) Drainage `STATUS_QUEUE` périodique (ui.timer) + `ui.notify`
- [ ] (LOG-02) (Optionnel) Panneau “événements” discret (développement)

## 🔒 Sécurité & Config
- [ ] (SEC-01) `.env` chargé si présent, champs clés masqués, persistance `settings.json` vérifiée
  - [n] `launch_ogma.py` supporte `.env` (python-dotenv recommandé)

## 🧪 Tests & QA (minimum viable)
- [ ] (QA-01) Smoke test: démarrage NiceGUI, envoi d’un message, réponse via provider/API local
- [ ] (QA-02) Mémoire: `add_memory` + `retrieve_and_synthesize_context` (log pipeline)
  - [n] Vérifier dimension embeddings (1024D si Mistral-embed)

## 🧹 Nettoyage & Docs
- [ ] (CLN-01) Déprécier `ui.py`/`app.py` en prod NiceGUI, isoler leur usage de transition
- [ ] (DOC-01) Mettre à jour `README_NICEGUI.md` (état M1–M6, ports, troubleshooting, sécurité)

---

## 📝 Notes de session (journal)
Ajouter une entrée à chaque session: date, tâches touchées (IDs), décisions, blocages.

- 2025-08-31
  - [x] (NG-00) Création wrapper `ogma_app.py` → `run_ogma()` renvoie vers `ogma_ng.run_ogma`
  - [n] Audit: Gradio encore dans `logic_callbacks.py` (BE-02 à traiter)
  - [n] NiceGUI: `ogma_ng.py` ne branche pas encore la mémoire (NG-03/NG-04), ni la persistance convos (NG-05)
 
- 2025-09-01
  - [x] (NG-03/07/08/09) Triggers de mémorisation + modal mémoire (CRUD + re-enrich) + contraintes UI
  - [x] (MM-03/04/05) Delete→rebuild FAISS, ré-enrichissement IA, scoring IA-only (alias score)
  - [x] (NG-04/MM-02) Contexte intégré dans le flux de chat NiceGUI ✅

- 2025-09-02 (Audit Claude)
  - [x] Audit complet terminé - Migration à 70%
  - [x] (MM-02) Injection contexte confirmée fonctionnelle
  - [!] (BE-01/02) Découplage Gradio identifié comme priorité critique
  - [n] Recommandation: Finaliser M3→M5 avant M4 pour stabilité
