# OpenClaw → OGMA - Débriefing d'Inspiration

**Date** : 10 février 2026  
**Contexte** : Analyse des fonctionnalités OpenClaw applicables à OGMA  
**Objectif** : Identifier ce qui est faisable techniquement et aligné avec la philosophie OGMA

---

## 📋 Points Clés OpenClaw

### Architecture
- Assistant IA qui tourne **localement** sur la machine utilisateur
- Accessible via **multi-plateformes chat** (WhatsApp, Telegram, Discord, Signal, iMessage)
- **Mémoire persistante** avec contexte 24/7
- **Proactivité** via heartbeats (check-ins spontanés)
- **Skills auto-générées** - l'IA peut coder ses propres extensions
- **Contrôle système complet** - shell, navigateur, fichiers

### Philosophie
- **Privacy-first** : données locales, pas de cloud obligatoire
- **Hackable** : open-source, extensible, personnalisable
- **Self-improving** : l'IA se modifie elle-même

---

## 🎯 Idées Faisables pour OGMA

### 💡 IDÉE #1 : Accès à Distance Sécurisé

**Besoin identifié** :  
Actuellement OGMA n'est accessible qu'en **réseau local** (localhost:8080). Quand Yohan part de chez lui, impossible de se connecter à OGMA qui tourne sur son PC serveur.

**Objectif** :  
PC/serveur fixe à la maison → OGMA accessible depuis **n'importe quel appareil** (téléphone, laptop ailleurs) via **adresse + code d'accès**.

---

#### 🔍 Analyse Technique

**État actuel** :
- OGMA = NiceGUI sur `localhost:8080` (ou 8080-8090 si retry)
- Accessible uniquement sur le même réseau local
- Pas de système d'authentification externe
- Pas de tunnel/reverse proxy

**Solutions Possibles** :

| Solution | Complexité | Sécurité | Coût | Modifications Code |
|----------|------------|----------|------|-------------------|
| **Cloudflare Tunnel** ⭐ | 🟢 Faible | 🟢 Haute (HTTPS auto) | Gratuit | Aucune |
| **Tailscale** | 🟢 Faible | 🟢 Très haute (VPN mesh) | Gratuit (perso) | Aucune |
| **ngrok** | 🟢 Faible | 🟡 Moyenne | Gratuit (limité) | Aucune |
| **Port Forwarding** | 🟡 Moyenne | 🔴 Faible (risques) | Gratuit | Auth à coder |
| **Hébergement Cloud** | 🔴 Haute | 🟢 Haute | €€€ | Refonte DB locale |

---

#### ✅ Recommandation : **Cloudflare Tunnel** (Cloudflared)

**Pourquoi** :
1. **Zéro modification code** - OGMA reste sur localhost:8080
2. **HTTPS automatique** - certificat SSL géré par Cloudflare
3. **Authentification native** - Cloudflare Access (email, Google, code PIN)
4. **Gratuit** pour usage personnel
5. **IP publique non exposée** - le tunnel est chiffré
6. **Compatible NiceGUI** - fonctionne avec WebSockets

**Comment ça marche** :
```
[Téléphone 4G/WiFi externe]
         ↓ HTTPS
[Cloudflare CDN] ← tunnel chiffré →
         ↓
[PC Serveur local] → OGMA (localhost:8080)
```

**Setup estimé** :
- Installation : `pip install cloudflared` ou télécharger exe
- Configuration tunnel : 10-15 min (interface web Cloudflare)
- Auth Cloudflare Access : 5 min (email one-time code ou Google OAuth)
- **Total : ~30 minutes max**

**Limites** :
- Nécessite PC serveur allumé 24/7 (déjà prévu par Yohan)
- Dépend de Cloudflare (mais 99.99% uptime)
- Bande passante gratuite limitée (largement suffisant pour usage perso)

---

#### 🔄 Alternative : **Tailscale** (si besoin VPN privé total)

**Avantages** :
- VPN mesh peer-to-peer (aucun trafic via serveur tiers)
- Ultra sécurisé (WireGuard sous le capot)
- Pas de limite bande passante

**Inconvénient** :
- Nécessite installer Tailscale sur **chaque appareil** (PC serveur + téléphone + laptop)
- Moins "transparent" que Cloudflare (IP locale virtuelle type 100.x.x.x)

---

#### 📋 Implémentation Cloudflare Tunnel

**Étape 1** : Installer cloudflared
```powershell
# Windows
winget install --id Cloudflare.cloudflared
# Ou télécharger : https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/
```

**Étape 2** : Créer tunnel Cloudflare
```powershell
cloudflared tunnel login  # Ouvre navigateur, connexion compte Cloudflare
cloudflared tunnel create ogma-tunnel
cloudflared tunnel route dns ogma-tunnel ogma.tondomaine.com  # Ou sous-domaine gratuit Cloudflare
```

**Étape 3** : Fichier config tunnel (`~/.cloudflared/config.yml`)
```yaml
tunnel: <TUNNEL_ID_AUTO_GÉNÉRÉ>
credentials-file: C:\Users\<USER>\.cloudflared\<TUNNEL_ID>.json

ingress:
  - hostname: ogma.tondomaine.com
    service: http://localhost:8080
  - service: http_status:404
```

**Étape 4** : Lancer tunnel (en background Windows service)
```powershell
cloudflared service install
cloudflared service start
```

**Étape 5** : Activer Cloudflare Access (auth par code)
- Dashboard Cloudflare → Zero Trust → Access → Applications
- Créer politique : email one-time PIN ou Google OAuth
- Facultatif : liste blanche IPs/emails autorisés

**Résultat final** :
- URL publique : `https://ogma.tondomaine.com`
- Accessible partout avec auth code
- OGMA tourne toujours sur localhost:8080 (aucun changement)

---

#### 🎯 Faisabilité

**Complexité technique** : 🟢 **TRIVIAL**  
**Effort implémentation** : 30 min setup, aucune ligne de code  
**Alignement OGMA** : ✅ **100%** - OGMA reste local, privacy preserved, juste exposition sécurisée  

**Verdict** : **FAISABLE IMMÉDIATEMENT** - aucun blocage technique.

---

#### ⚠️ LIMITATION IDENTIFIÉE : Perception Visuelle Mobile

**Question Yohan** : "Si je suis sur mon téléphone, OGMA peut-il utiliser la caméra de mon téléphone pour la perception ?"

**Réponse courte** : **NON par défaut**, mais **OUI avec adaptation code**.

---

#### 🔍 Problème Technique

**État actuel** (`ogma_perception.py`) :
```python
# Capture webcams LOCALES du PC serveur via OpenCV
cap = cv2.VideoCapture(camera_index)  # Index 0, 1, 2... = webcams du PC
```

**Avec Cloudflare Tunnel** :
- Le téléphone accède à l'**interface web** de OGMA
- Mais `cv2.VideoCapture()` continue de capturer les webcams **du PC serveur**
- C'est normal : OpenCV est côté **backend Python** (server-side)
- La caméra du téléphone est côté **client** (navigateur)

**Résultat** : Via Cloudflare, tu verrais les webcams du PC (e2eSoft VCam, etc.), pas celle du téléphone.

---

#### ✅ Solutions Possibles

| Solution | Complexité | Adaptation Code | Use Case |
|----------|------------|-----------------|----------|
| **Upload Photo Manuel** | 🟢 Faible | Minime | Photo ponctuelle analysée |
| **Live Stream WebRTC** | 🟡 Moyenne | Significative | Streaming temps réel |
| **Dual Mode Perception** | 🟡 Moyenne | Modérée | Switch auto server/client cams |

---

#### 🎯 Approche Progressive Recommandée

**Phase 1 : Mode "Upload Photo" (MVP Rapide)**

**Comment** :
- Ajouter bouton "📸 Analyser avec ma caméra" dans l'interface mobile
- Utilise `<input type="file" capture="camera">` HTML5 (natif navigateurs mobiles)
- L'utilisateur prend une photo → upload → OGMA analyse
- **Déjà supporté par NiceGUI** via `ui.upload()`

**Code estimé** :
```python
# Dans ogma_ng.py ou ogma_perception.py
with ui.upload(
    label='📸 Capturer depuis ma caméra',
    on_upload=lambda e: _analyze_uploaded_image(e.content),
    auto_upload=True
).props('accept="image/*" capture="camera"'):
    ui.icon('photo_camera')

async def _analyze_uploaded_image(image_bytes):
    """Analyse une photo uploadée depuis mobile"""
    nparr = np.frombuffer(image_bytes.read(), np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    result = await perception.analyze_frame(frame)
    # Afficher résultat...
```

**Avantages** :
- ✅ **10-20 lignes de code max**
- ✅ Fonctionne immédiatement avec Cloudflare Tunnel
- ✅ Compatible tous navigateurs mobiles
- ✅ Pas de dépendance externe (WebRTC, etc.)

**Limites** :
- ⚠️ Pas de streaming continu (photos one-shot)
- ⚠️ Utilisateur doit cliquer pour chaque photo

---

**Phase 2 : Mode "Live Stream" (Avancé)**

**Comment** :
- Implémenter WebRTC bidirectionnel
- JavaScript côté client : `navigator.mediaDevices.getUserMedia()` capture caméra
- Envoie frames via WebSocket → backend Python
- OGMA traite comme un flux webcam classique

**Complexité** :
- 🟡 Nécessite bibliothèque WebRTC Python (ex: `aiortc`)
- 🟡 Gestion synchronisation frames (latence réseau)
- 🟡 Adaptation `ogma_perception.py` pour accepter sources WebRTC
- **Estimé** : 100-200 lignes de code + tests

**Avantages** :
- ✅ Streaming temps réel (comme webcam native)
- ✅ Expérience fluide

**Limites** :
- ⚠️ Consommation bande passante (vidéo upload continu)
- ⚠️ Complexité debugging (WebRTC notorious pour NAT/firewall issues)

---

**Phase 3 : Dual Mode (Intelligence Contextuelle)**

**Comment** :
- Détecter le type de connexion (local vs remote)
- Si local (192.168.x.x) → webcams PC serveur
- Si remote (via Cloudflare) → mode upload/WebRTC client

**Code pattern** :
```python
def get_perception_mode():
    """Détecte si client est local ou remote"""
    client_ip = request.headers.get('CF-Connecting-IP')  # IP via Cloudflare
    if client_ip and not client_ip.startswith('192.168'):
        return 'client_cam_mode'  # Mobile remote
    return 'server_cam_mode'  # PC local
```

---

#### 🎯 Faisabilité Perception Mobile

**Phase 1 (Upload Photo)** :  
- Complexité : 🟢 **TRIVIAL**  
- Effort : ~30 min code + 15 min tests  
- Alignement : ✅ Compatible philosophie OGMA  
- **Verdict** : **FAISABLE IMMÉDIATEMENT**

**Phase 2 (Live Stream)** :  
- Complexité : 🟡 **MOYENNE**  
- Effort : 1-2 jours dev + debugging WebRTC  
- Alignement : ✅ Enrichit perception mais pas critique  
- **Verdict** : **FAISABLE MAIS PAS PRIORITAIRE** (attendre feedback Phase 1)

**Phase 3 (Dual Mode)** :  
- Complexité : 🟡 **MOYENNE**  
- Effort : 3-4 heures  
- Dépend de : Phase 1 ou 2 implémentée  
- **Verdict** : **FAISABLE APRÈS MVP**

---

#### 💡 Recommandation Stratégique

1. **Maintenant** : Setup Cloudflare Tunnel (accès web mobile)
2. **Ensuite** : Implémenter Phase 1 (upload photo) → valider usage réel
3. **Si besoin confirmé** : Phase 2 (live stream) sinon rester en upload manuel
4. **Optionnel** : Phase 3 (dual mode) si les deux modes coexistent

**Question clé** : Pour ton usage, tu as besoin de **streaming continu caméra mobile** ou des **photos ponctuelles** suffisent ?

---

## 🚧 Contraintes Techniques OGMA

- Architecture actuelle : NiceGUI (localhost:8080)
- Dual-IA : Chat Controller (conversationnel) + Archiviste (analytique)
- Mémoire : SQLite + FAISS + FTS5 (hybride)
- Extensions : Pattern singleton standardisé
- Backend : Multi-provider (API/Ollama/GGUF/KoboldCpp)

---

## 📝 Notes de Discussion

### Session 1 - Accès à Distance

**Yohan** : Besoin accès OGMA depuis l'extérieur (actuellement bloqué hors réseau local)  
**Analyse** : Cloudflare Tunnel = solution optimale (30 min setup, zéro code, HTTPS + auth native, gratuit)  
**Statut** : En attente validation conceptuelle avant implémentation

---

### Session 1.1 - Perception Mobile

**Yohan** : "Via Cloudflare, la caméra de mon téléphone peut-elle servir à la perception OGMA ?"  
**Réponse** : NON par défaut (OpenCV capture serveur-side), OUI avec adaptation  
**Solutions** :
- Phase 1 (MVP) : Upload photo manuel (10-20 lignes, trivial)
- Phase 2 (Avancé) : Live stream WebRTC (100-200 lignes, complexe)
- Phase 3 (Smart) : Dual mode auto (server cams local, client cam remote)  
**Statut** : En attente choix Yohan (streaming continu nécessaire ou photos one-shot suffisantes ?)

---

### Session 1.2 - Clarification Use Case Stream vs TeamViewer

**Yohan** : "La solution stream est sympa, mais au final, j'aurais exactement le même résultat en utilisant TeamViewer, non ?"  
**Analyse** : **OUI, excellent point.** TeamViewer donne déjà accès à l'interface OGMA + webcams du PC.  
**Conclusion** : Le stream WebRTC n'a de sens QUE si le besoin est "OGMA doit voir via la caméra du téléphone" (pas juste "je veux accéder à OGMA")  
**Vraie valeur** : Cloudflare Tunnel (interface web native) + Upload photo (analyse ponctuelle de ce que TU vois)  
**Statut** : Validation que Phase 1 (upload photo) est le vrai sweet spot, pas le stream complexe

---

### Session 1.3 - Use Cases Concrets Identifiés ✅

**Yohan** : "Pouvoir utiliser les capacités d'OGMA où que je sois. Exemples :
1. **Forêt** : Photo champignon → OGMA recherche web + identifie
2. **Email mobile** : PDF reçu → partager avec OGMA pour analyse"

**EXCELLENTE NOUVELLE** : OGMA a **DÉJÀ** les capacités backend nécessaires !

#### 📋 Inventaire Existant

| Capacité Demandée | Existe dans OGMA ? | Fichier |
|-------------------|-------------------|---------|
| Recherche web auto | ✅ OUI | `extensions/web_navigator/` |
| Traitement PDF | ✅ OUI | `extensions/file_processor/` |
| Analyse image/photo | ✅ OUI | `ogma_perception.py` + vision APIs |
| Accès mobile web | ❌ **MANQUE** | Setup Cloudflare Tunnel |
| Upload photo mobile | ❌ **MANQUE** | Bouton capture caméra UI |
| Upload fichier mobile | ⚠️ **PARTIEL** | UI upload existe mais pas optimisé mobile |

**Statut** : Plan d'action validé (voir section dédiée)

---

### Session 1.4 - Plan d'Action Validé ✅

**Yohan** : "Note qu'il faudra qu'on teste en codant déjà une fonction d'upload via mobile en local, et qu'on devra procéder à l'implémentation du système privilégiant Cloudflare"

**Décisions** :
1. **Étape 1** : Coder + tester upload photo mobile en LOCAL d'abord (réseau WiFi)
2. **Étape 2** : Implémenter Cloudflare Tunnel APRÈS validation fonctionnelle

**Approche progressive confirmée** :
- Phase test locale = validation concept sans complexité accès distant
- Phase Cloudflare = déploiement accès externe une fois fonctionnalité stable
- Effort total : ~1h15 (45 min code + 30 min Cloudflare)

**Statut** : ⏳ En attente démarrage implémentation Étape 1

---

### Session 1.5 - Suite du Débriefing

**Yohan** : "Non on va continuer à débrieffer... j'ai encore plein de questions"  
**Statut** : 🔍 Exploration continue des concepts OpenClaw applicables à OGMA

*Notes à venir au fur et à mesure des questions...*

---

### 💡 IDÉE #3 : Boucle Auto-Corrective I2I + Prompt Auto-Évolutif

**Question Yohan** : "Je voudrais cette boucle d'apprentissage pour les images-to-images surtout. L'IA a un prompt par défaut qu'elle utilise pour limiter les erreurs, il est injecté avant chaque modification par i2i. Le top serait que l'IA elle-même puisse modifier son prompt d'instruction i2i en fonction des erreurs apprises."

---

#### 🔑 Le Prompt Clé : `img2img_guide`

**Fichier** : `data/settings.json` → `image_generation.img2img_guide`  
**Injection** : `ogma_ng.py` ligne 3398-3401 → injecté comme message `system` avant chaque échange  
**Valeur par défaut** : `ogma_image_config.py` ligne 452 (version minimale)  
**Version active** : ~2000+ caractères, méticuleusement écrit par Yohan avec :
- Règles GARDE/SUPPRIME/CHANGE pour préserver éléments
- Contraintes de proportions anatomiques
- Tags de puissance (cinematic render, 8k, etc.)
- Interdictions de description (anti "pâte à modeler")
- Déclencheur phrase magique "il faut que je modifie cette image :"
- Règles de concision (50-120 mots)

**C'est CE prompt que l'IA devrait pouvoir auto-améliorer.**

---

#### ⚡ Principes Directeurs (validés par Yohan)

**1. Priorité Frontend Absolue**
- Le textarea `img2img_guide` dans le frontend EST la source de vérité
- Quand Yohan modifie le guide dans l'interface → sa version prévaut TOUJOURS
- Le système auto-évolutif modifie `settings.json` → reflété dans le frontend
- Pas de fichier "shadow" parallèle : UNE seule source = `settings.json → img2img_guide`
- Si Yohan édite manuellement après une auto-modification → son edit gagne

**2. IA Principale = Seule Responsable du Craft I2I**
- C'est l'IA principale (0.7, créative, "Architecte Visuelle") qui génère les prompts i2i
- C'est donc ELLE qui doit : analyser ses résultats, reformuler, extraire les leçons, proposer des modifications du guide
- L'Archiviste (0.3, analytique) NE PARTICIPE PAS à la boucle corrective
- L'Archiviste garde son rôle actuel : traduction auto FR→EN du prompt final
- Le Memory Manager gère le stockage/retrieval technique des leçons

**Raison** : L'artiste qui s'auto-critique est plus cohérent qu'un analyste qui juge un artiste. L'IA principale comprend le lien causal prompt→résultat puisque c'est elle qui crée.

---

#### 🔍 Ce Qui Existe DÉJÀ dans OGMA

| Brique | Status | Localisation |
|--------|--------|-------------|
| Génération i2i | ✅ | `modules/logic/image_generation.py` → `process_img2img_generation()` |
| Guide d'instruction i2i | ✅ | `settings.json` → `img2img_guide` (injecté en system) |
| Vision feedback post-gen | ✅ | `get_luna_image_feedback()` (texte libre, non structuré) |
| Error feedback API | ✅ | `get_ai_error_feedback()` |
| Auto-translation FR→EN | ✅ | Via Archiviste dans pipeline i2i |
| **Boucle correction i2i** | ❌ ABSENT | Pipeline one-shot actuellement |
| **Analyse structurée défauts** | ❌ ABSENT | Feedback = texte libre, pas JSON |
| **Leçons persistantes i2i** | ❌ ABSENT | Aucun apprentissage entre sessions |
| **Auto-modification guide** | ❌ ABSENT | `img2img_guide` statique dans settings |

---

#### 📊 Flux Actuel vs Souhaité

**ACTUEL (ONE-SHOT)** :
```
IA reçoit image → génère prompt i2i → API génère → vision feedback texte → FIN
```

**SOUHAITÉ (SELF-CORRECTING + SELF-EVOLVING)** :
```
IA reçoit image
    ↓
Charge img2img_guide BASE + leçons apprises
    ↓
IA génère prompt i2i selon instructions
    ↓
API génère image modifiée
    ↓
Vision analyse → JSON structuré {score, défauts, prompt_issues}
    ↓
Score < seuil ? ── NON → Afficher résultat ✅
    │
   OUI
    ↓
IA analyse défauts + reformule prompt
    ↓
Re-génère (max 3 tentatives)
    ↓
Succès ? → Archiviste extrait leçon
    ↓
Leçon stockée dans data/i2i_lessons.json
    ↓
Après N leçons similaires → propose modification du img2img_guide
    ↓
Yohan valide → img2img_guide ÉVOLUE dans settings.json
```

---

#### 🏗️ Architecture 4 Couches

##### Couche 1 : Analyse Structurée Post-I2I (remplace feedback texte libre)

**Principe** : Après chaque génération i2i, la Vision API retourne un **JSON structuré** au lieu d'un commentaire texte libre.

**Constat actuel** : Le `vision_feedback_prompt` est trop vague. Il dit "commente ce que tu vois en 2-3 phrases" sans grille de vérification. Grok 4.1 Fast a la capacité de détecter les défauts, mais on ne lui dit pas QUOI chercher. Résultat : il laisse passer des déformations évidentes.

**Solution** : Séparer en DEUX prompts :
- `vision_feedback_prompt` (existant, amélioré) → commentaire conversationnel court pour l'utilisateur
- `vision_i2i_analysis_prompt` (NOUVEAU) → analyse structurée JSON avec checklist systématique

**Nouveau prompt d'analyse i2i (checklist systématique)** :
```python
I2I_ANALYSIS_PROMPT = """Tu viens de modifier cette image avec le prompt: "{original_prompt}"

MISSION : Analyse RIGOUREUSE du résultat. Tu es une inspectrice qualité impitoyable.
RÈGLE : PIXELS_ONLY. Ne commente que ce que tu VOIS. 0_Hallucination.

CHECKLIST SYSTÉMATIQUE (vérifie CHAQUE point) :
□ ANATOMIE : Nombre de doigts correct (5/main) ? Bras/jambes corrects ? Pas de membre en trop/manquant ?
□ PROPORTIONS : Tailles relatives cohérentes entre personnages ? Tête/corps ratio normal ?
□ DÉFORMATIONS : Zones "pâte à modeler" ? Étirements anormaux ? Effet tentacule ?
□ VISAGE : Symétrie faciale ? Expression naturelle ? Pas de fusion de traits ?
□ ÉLÉMENTS GARDÉS : Ce qui devait être préservé l'est-il vraiment ?
□ ÉLÉMENTS AJOUTÉS : Intégrés naturellement ? Proportions correctes ?
□ CONTACT PHYSIQUE : Points de contact réalistes ? Pas de fusion entre corps ?
□ ARRIÈRE-PLAN : Cohérent ? Pas de distorsion/artefacts ?
□ LUMIÈRE/TEXTURE : Cohérence d'éclairage entre éléments source et ajoutés ?

Réponds UNIQUEMENT en JSON valide :
{
  "score": <1-10>,
  "satisfaisant": <true si score >= 6>,
  "defauts_detectes": [
    {"type": "deformation|proportion|artefact|anatomie|fusion|manquant|extra|texture",
     "gravite": "critique|majeur|mineur",
     "description": "description factuelle du défaut",
     "zone": "zone de l'image concernée"}
  ],
  "elements_bien_preserves": ["liste des éléments gardés avec succès"],
  "prompt_issues": ["ce qui dans le prompt a probablement causé chaque défaut"],
  "correction_suggérée": "reformulation du prompt pour corriger les défauts critiques"
}

BARÈME : 9-10=parfait | 7-8=bon, défauts mineurs | 5-6=passable | 3-4=défauts majeurs | 1-2=raté
Score < 6 = à refaire. Sois EXIGEANTE."""
```

**Ce prompt sera aussi éditable dans le frontend** (comme `img2img_guide`), avec le même principe de priorité.

**Effort** : 1h (prompt + parsing JSON + fallback si JSON invalide + textarea frontend)

---

##### Couche 2 : Boucle Correction I2I (intra-session)

**Principe** : Si le score < seuil, l'IA reformule automatiquement et re-génère. Max N tentatives.

```python
async def generate_img2img_with_correction(
    image_source, original_prompt, max_retries=3, score_threshold=6
):
    """Boucle auto-corrective pour i2i"""
    
    prompt = original_prompt
    best_result = None
    best_score = 0
    
    for attempt in range(1, max_retries + 1):
        # Vérifier interruption utilisateur
        if _i2i_stop_requested:
            break
            
        # Générer
        result = await backend.generate_img2img(image_source, prompt, ...)
        
        # Analyser résultat (JSON structuré)
        analysis = await analyze_i2i_result(result.image, prompt)
        
        # Afficher tentative à l'utilisateur (transparence!)
        display_attempt(attempt, result.image, analysis)
        
        if analysis['score'] >= score_threshold:
            best_result = result
            best_score = analysis['score']
            break  # Succès!
        
        if analysis['score'] > best_score:
            best_result = result
            best_score = analysis['score']
        
        # Reformuler prompt basé sur analyse
        prompt = await refine_i2i_prompt(
            original_prompt, 
            analysis['defauts_detectes'],
            analysis['correction_suggérée'],
            attempt
        )
        
        # Afficher "Je corrige..." (transparence)
        notify_user(f"Tentative {attempt}/{max_retries} - Score {analysis['score']}/10, je corrige...")
    
    # Stocker la leçon si correction a amélioré le score
    if best_score > initial_score:
        await save_i2i_lesson(original_prompt, corrections_applied, best_score)
    
    return best_result
```

**Interruption utilisateur** : Flag global `_i2i_stop_requested` + bouton STOP dans UI

**Effort** : 2-3h (boucle + reformulation prompt + UI progression + flag stop)

---

##### Couche 3 : Leçons Persistantes I2I (entre sessions)

**Principe** : Les corrections réussies sont mémorisées comme "leçons" et injectées dans le contexte des futures générations.

**Stockage** : `data/i2i_lessons.json`
```json
{
  "lessons": [
    {
      "id": "lesson_20260210_001",
      "created": "2026-02-10T14:30:00",
      "context": "Ajout d'une femme interagissant avec l'homme",
      "defaut_original": "Déformation tentacule du bras droit",
      "prompt_fautif": "add woman touching man's arm with her hand",
      "correction_efficace": "add woman, her right hand gently on man's shoulder, keep man's arm unchanged",
      "regle_extraite": "Ne jamais décrire un contact direct main-bras, plutôt décrire la position finale de la main ajoutée",
      "score_avant": 3,
      "score_apres": 8,
      "confirmations": 3,
      "applicable": true
    }
  ],
  "stats": {
    "total_lessons": 12,
    "avg_score_improvement": 3.2,
    "most_common_defects": ["deformation", "proportion"]
  }
}
```

**Injection** : Avant chaque i2i, les N leçons les plus pertinentes sont ajoutées au contexte :
```python
# Dans ogma_ng.py, après injection img2img_guide
relevant_lessons = load_relevant_i2i_lessons(user_prompt, max_lessons=5)
if relevant_lessons:
    lessons_text = format_lessons_for_injection(relevant_lessons)
    messages.append({
        'role': 'system',
        'content': f"⚠️ LEÇONS APPRISES DE TES ERREURS I2I PRÉCÉDENTES :\n{lessons_text}"
    })
```

**Effort** : 1-2h (stockage JSON + chargement + injection + recherche pertinence)

---

##### Couche 4 : Auto-Modification du `img2img_guide` (le Graal)

**Principe** : Quand une leçon est confirmée N fois (ex: 3 confirmations), l'IA principale propose une modification du `img2img_guide` lui-même. Yohan valide, le guide évolue dans settings.json (= visible dans le frontend).

**Flux** :
1. Leçon confirmée 3+ fois → trigger analyse Archiviste
2. Archiviste reçoit : `img2img_guide` actuel + leçon + contexte
3. Archiviste propose : `{zone_à_modifier, ancien_texte, nouveau_texte, justification}`
4. Notification Yohan : "L'IA propose de modifier son guide i2i : [diff]"
5. Yohan valide → `img2img_guide` mis à jour dans settings.json
6. Backup automatique dans `data/i2i_guide_history/`

```python
async def propose_guide_modification(lesson):
    """L'IA principale propose une évolution de son propre img2img_guide"""
    
    current_guide = settings.get('image_generation', {}).get('img2img_guide', '')
    
    prompt = f"""ANALYSE DE MODIFICATION DU GUIDE I2I

GUIDE ACTUEL :
{current_guide}

LEÇON APPRISE (confirmée {lesson['confirmations']}x) :
- Défaut récurrent : {lesson['defaut_original']}
- Correction efficace : {lesson['correction_efficace']}
- Règle extraite : {lesson['regle_extraite']}

MISSION : Propose UNE modification précise du guide actuel pour intégrer
cette leçon. Réponds en JSON :
{{
  "zone_modifiée": "section du guide concernée",
  "ajout_proposé": "texte exact à ajouter/remplacer",
  "position": "après quel paragraphe/règle",
  "justification": "pourquoi cette modification aide"
}}"""
    
    response = await chat_controller.generate(prompt)  # IA principale, pas Archiviste
    modification = parse_json(response)
    
    # Sauvegarder proposition pour validation Yohan
    save_pending_guide_modification(modification)
    
    # Mettre à jour settings.json SI validé → reflété dans le textarea frontend
    # Jamais de modification silencieuse, Yohan voit le diff et valide
    notify_guide_evolution_proposal(modification)
```

**Versionning** :
```
data/i2i_guide_history/
├── img2img_guide_v1_20260210.json  # Guide original
├── img2img_guide_v2_20260215.json  # Après leçon "anti-tentacule"
├── img2img_guide_v3_20260220.json  # Après leçon "proportions visage"
└── modifications_log.json          # Historique toutes modifications
```

**Effort** : 2-3h (Archiviste analysis + notification UI + backup/versioning + validation flow)

---

#### 🎯 Plan d'Implémentation par Phases

| Phase | Description | Effort | Prérequis | Valeur |
|-------|-------------|--------|-----------|--------|
| **1** | Analyse structurée JSON post-i2i | 1h | `ai_can_see_images = true` | ⭐⭐⭐ Base de tout |
| **2** | Boucle correction i2i (max 3 retry) | 2-3h | Phase 1 | ⭐⭐⭐⭐ Auto-correction |
| **3** | Leçons persistantes i2i (JSON) | 1-2h | Phase 2 | ⭐⭐⭐⭐ Apprentissage |
| **4** | Auto-modification img2img_guide | 2-3h | Phase 3 + N leçons | ⭐⭐⭐⭐⭐ Le Graal |

**TOTAL** : 6-9h dev | Complexité globale : 🟡 MOYENNE-HAUTE  
**Prérequis critique** : `ai_can_see_images = true` dans settings  
**Alignement OGMA** : ✅ PARFAIT
- Transparence : chaque tentative montrée, raison expliquée
- Authenticité : "j'ai raté, voilà pourquoi, je corrige"
- Croissance organique : le guide s'améliore avec l'usage
- Pas de fallback silencieux : Yohan valide les modifications du guide

---

#### ⚠️ Points d'Attention

1. **Coût API** : Chaque retry = 1 appel i2i + 1 appel vision. 3 retries = 6 appels au lieu de 2.
   → Configurable : `max_retries` et `score_threshold` dans settings

2. **Parsing JSON Vision** : Les LLM ne retournent pas toujours du JSON parfait.
   → Fallback : regex extraction si JSON invalide, ou re-prompt "corrige ton JSON"

3. **Pertinence des leçons** : Comment trouver les leçons pertinentes pour un nouveau prompt ?
   → Option A : Recherche par mots-clés (simple)
   → Option B : Embedding vectoriel via FAISS (plus précis, OGMA l'a déjà)

4. **Inflation du guide** : Si trop de leçons intégrées, le guide devient trop long.
   → Limiter à ~20 règles actives max, archiver les anciennes
   → L'Archiviste peut CONSOLIDER plusieurs leçons similaires en une seule règle

5. **Validation humaine** : La Couche 4 DOIT passer par Yohan.
   → Jamais de modification auto du guide sans validation
   → Aligné avec la philosophie OGMA : "Yohan architecte, IA exécute"

6. **🚨 MODULARITÉ ABSOLUE** : `ogma_ng.py` fait déjà 7145 lignes — INTERDIT de le faire grossir.
   → Toute nouvelle logique va dans `modules/logic/` (image_generation.py, i2i_lessons.py)
   → `ogma_ng.py` ne reçoit que des imports + appels courts (max 5-10 lignes par point d'intégration)
   → Frontend image → `ogma_image_config.py` (déjà dédié)
   → Tests → `tests/` (fichiers séparés par phase)
   → **Principe : si tu ajoutes > 15 lignes à ogma_ng.py, tu es en train de te tromper**

**Statut** : ⏳ En attente validation conceptuelle par Yohan

---### 💡 IDÉE #2 : Système d'Apprentissage Évolutif

**Question Yohan** : "Je suis très intéressé par le système d'apprentissage d'OpenClaw. Il semble apprendre de ses erreurs, puis il recommence en contournant ses erreurs et ne les répète plus... il évolue. Est-ce que l'approche mémorielle est documentée ? Comment ça marche ?"

---

#### 🔍 État des Connaissances OpenClaw

**Ce qu'on sait (depuis témoignages/site)** :
- ✅ "Persistent memory" - contexte 24/7
- ✅ "Self-hackable" - peut se modifier lui-même
- ✅ "Can write its own skills" - code ses propres extensions
- ✅ Témoignages : "it learned", "got better everyday", "designed a skill on its own"

**Ce qu'on NE sait PAS (détails techniques)** :
- ❓ Architecture mémoire précise (vector DB ? SQLite ? Redis ?)
- ❓ Mécanisme d'apprentissage (fine-tuning ? RAG ? prompt injection ?)
- ❓ Comment les "erreurs" sont détectées et mémorisées
- ❓ Format stockage des "lessons learned"
- ❓ Trigger de modification comportement

**Source manquante** : Documentation technique détaillée ou code source GitHub

---

#### 🎯 Options d'Investigation

**Option A** : Analyser le code source OpenClaw (GitHub)
- Repo public : `https://github.com/openclaw/openclaw`
- Chercher : `memory/`, `learning/`, `skills/`, README architecture
- **Avantage** : Vérité terrain, détails d'implémentation
- **Inconvénient** : Temps de lecture code (peut-être complexe)

**Option B** : Théoriser approches possibles + comparer OGMA
- Analyser ce qu'OGMA fait déjà
- Identifier gaps conceptuels
- Proposer implémentation OGMA-compatible
- **Avantage** : Rapide, pragmatique
- **Inconvénient** : Risque de réinventer ce qui existe

---

#### 🧠 Ce Qu'OGMA Fait DÉJÀ (Analyse Comparative)

**Mémoire OGMA Actuelle** :

| Aspect | OGMA | OpenClaw (supposé) |
|--------|------|-------------------|
| **Stockage long-terme** | SQLite + FAISS vectoriel | ? (probablement similaire) |
| **Contexte conversation** | Last N messages + souvenirs pertinents | Persistent 24/7 |
| **Enrichissement** | Archiviste analyse → tags/résumé | ? |
| **Évolution personnalité** | Ego Boolean (18 groupes) | Persona onboarding |
| **Apprentissage erreurs** | ❌ **ABSENT** | ✅ Apparemment OUI |
| **Auto-modification** | ❌ **ABSENT** | ✅ Code ses skills |

**Gap critique identifié** : OGMA ne "retient" pas explicitement ses erreurs pour les éviter.

---

#### 🔬 Hypothèses Mécanisme Apprentissage OpenClaw

**Hypothèse 1 : Loop Reflection + Memory Injection**
```
1. Tâche échoue (ex: API key manquante)
2. LLM analysé l'erreur → génère "lesson learned"
3. Lesson stockée en mémoire avec contexte
4. Prochaine tentative similaire → RAG récupère lesson
5. Prompt enrichi : "Tu as déjà échoué sur ça à cause de X, fais Y"
6. Comportement adapté
```

**Hypothèse 2 : Modification Dynamique Prompts**
```
1. Échec détecté
2. LLM génère correction au system prompt
3. Prompt modifié sauvegardé
4. Relance avec nouveau prompt
5. Prompts s'accumulent (versioning)
```

**Hypothèse 3 : Skills Auto-Générées Persistantes**
```
1. Tâche nouvelle rencontrée (ex: "contrôle mon purificateur d'air")
2. LLM code une "skill" Python
3. Skill testée, debuggée itérativement
4. Skill sauvegardée dans dossier `skills/`
5. Skill chargée automatiquement au prochain démarrage
6. Prochaine demande similaire → skill réutilisée
```

**La plus crédible** : Probablement une **combinaison des 3**.

---

#### 🛠️ Implémentation Potentielle OGMA

**Approche Minimaliste (Quick Win)** :

**1. Table SQLite "lessons_learned"**
```sql
CREATE TABLE lessons_learned (
    id TEXT PRIMARY KEY,
    context TEXT,           -- "Tentative de [action]"
    error TEXT,             -- "Erreur: [message]"
    solution TEXT,          -- "Pour éviter cela, [solution]"
    success_after BOOLEAN,  -- La solution a-t-elle marché ?
    created_at TIMESTAMP
);
```

**2. Détection Erreurs Automatique**
```python
# Dans ogma_ng.py, après chaque réponse IA
if "erreur" in reply.lower() or "impossible" in reply.lower():
    # Demander à l'Archiviste d'analyser l'échec
    lesson = await archiviste.analyze_failure(
        context=user_message,
        error=reply,
        history=_chat_history[-5:]
    )
    if lesson:
        save_lesson(lesson)
```

**3. Injection Contexte "Lessons"**
```python
# Avant envoi prompt à l'IA principale
relevant_lessons = search_lessons(user_message)  # RAG vectoriel
if relevant_lessons:
    system_prompt += f"\n\n⚠️ LESSONS APPRISES:\n{relevant_lessons}"
```

**Effort estimé** : 2-3 heures (table DB + détection + injection)

---

**Approche Avancée (Self-Modifying Skills)** :

**1. Dossier `skills/user_generated/`**
```python
# L'IA principale peut demander à créer une skill
if "il faut que je code une fonction pour" in reply:
    skill_code = await chat_controller.generate_skill(description)
    save_skill(f"skills/user_generated/{skill_name}.py")
    reload_skills()  # Hot reload
```

**2. System Prompt Dynamique Versionné**
```python
# data/system_prompts/main_ai_v{timestamp}.txt
# Chaque modification sauvegardée
# L'IA peut proposer : "Je pense que je devrais modifier mon prompt système pour..."
```

**Effort estimé** : 1-2 jours (sandbox sécurisé pour code généré + tests)

---

#### ⚠️ Risques & Considérations

**Apprentissage par erreurs** :
- ✅ **Pro** : IA s'améliore naturellement
- ⚠️ **Con** : Risque de "sur-apprentissage" (généralise mal)
- ⚠️ **Con** : Détection erreur pas toujours fiable

**Auto-modification code** :
- ✅ **Pro** : Évolutivité maximale
- 🔴 **Con** : **RISQUE SÉCURITÉ** (code généré non vérifié)
- 🔴 **Con** : Debugging cauchemardesque si l'IA casse son propre code
- ⚠️ **Con** : Nécessite sandbox Python (conteneur, vm, etc.)

**Philosophie OGMA** :
- ✅ Aligné : Croissance organique
- ⚠️ Tension : Transparence totale vs boîte noire évolutive
- 🤔 Authenticité : L'IA qui se modifie reste-t-elle "elle-même" ?

---

#### 🎯 Recommandation Stratégique

**Phase 1 : "Lessons Learned" (Safe & Quick)**
- Table SQLite erreurs/solutions
- Détection échecs + analyse Archiviste
- Injection RAG des lessons pertinentes
- **Effort** : 2-3 heures
- **Risque** : 🟢 Faible
- **Valeur** : ⭐⭐⭐⭐ OGMA apprend de ses erreurs

**Phase 2 : "Skills Repository" (Avancé, supervisé)**
- L'IA propose des skills, Yohan valide avant sauvegarde
- Skills stockées en Python mais **pas auto-exécutées**
- Yohan review + active manuellement
- **Effort** : 1 jour
- **Risque** : 🟡 Modéré (avec validation humaine)
- **Valeur** : ⭐⭐⭐ Extensibilité collaborative

**Phase 3 : "Self-Modification" (Expert, long-terme)**
- Après 6 mois d'usage OGMA stable
- Sandbox sécurisé pour code généré
- Rollback automatique si régression détectée
- **Effort** : 3-5 jours
- **Risque** : 🔴 Élevé (sans précautions)
- **Valeur** : ⭐⭐⭐⭐⭐ AGI-like behavior

---

#### 🔍 Prochaine Étape Investigation

**Question pour Yohan** : Tu veux que je :

**A)** Aille chercher dans le code source OpenClaw (GitHub) pour voir exactement comment ils font ?  
**B)** On commence à implémenter Phase 1 ("Lessons Learned") dans OGMA directement ?  
**C)** On continue à explorer d'autres aspects OpenClaw avant de coder ?

---

---

### Session 1.3 - Use Cases Concrets Identifiés ✅

**Yohan** : "Pouvoir utiliser les capacités d'OGMA où que je sois. Exemples :
1. **Forêt** : Photo champignon → OGMA recherche web + identifie
2. **Email mobile** : PDF reçu → partager avec OGMA pour analyse"

**EXCELLENTE NOUVELLE** : OGMA a **DÉJÀ** les capacités backend nécessaires !

#### 📋 Inventaire Existant

| Capacité Demandée | Existe dans OGMA ? | Fichier |
|-------------------|-------------------|---------|
| Recherche web auto | ✅ OUI | `extensions/web_navigator/` |
| Traitement PDF | ✅ OUI | `extensions/file_processor/` |
| Analyse image/photo | ✅ OUI | `ogma_perception.py` + vision APIs |
| Accès mobile web | ❌ **MANQUE** | Setup Cloudflare Tunnel |
| Upload photo mobile | ❌ **MANQUE** | Bouton capture caméra UI |
| Upload fichier mobile | ⚠️ **PARTIEL** | UI upload existe mais pas optimisé mobile |

---

#### ✅ Solution Complète (Triviale)

**Workflow Champignon en Forêt** :
1. Yohan ouvre OGMA sur mobile (`https://ogma.tondomaine.com`)
2. Clic bouton "📸 Analyser" → capture photo champignon
3. Photo uploadée → `ogma_perception.py` analyse l'image
4. Yohan dans le chat : "C'est quoi ce champignon ?"
5. OGMA détecte phrase magique recherche web → `web_navigator` cherche
6. Résultat : identification + comestibilité + infos

**Workflow PDF Email** :
1. Yohan ouvre PDF sur mobile → bouton "Partager"
2. Upload dans OGMA (bouton 📎 existant)
3. `file_processor` extrait contenu → mémorise
4. Yohan : "Résume-moi ce document"
5. OGMA accède au contenu extrait → synthèse

---

#### 🛠️ Implémentation Nécessaire

**Étape 1 : Cloudflare Tunnel** (30 min)
- Déjà détaillé plus haut
- Aucune ligne de code

**Étape 2 : Bouton Upload Photo Mobile** (30 min code)
```python
# Dans ogma_ng.py, section header ou perception
with ui.button('📸', on_click=lambda: photo_upload.open()).props('flat round'):
    ui.tooltip('Capturer une photo')

with ui.dialog() as photo_upload:
    with ui.card():
        ui.label('Analyser une photo').classes('text-h6')
        
        ui.upload(
            label='Prendre une photo ou choisir fichier',
            on_upload=_handle_mobile_photo_upload,
            auto_upload=True,
            max_file_size=10_000_000  # 10 MB
        ).props('accept="image/*" capture="camera"').classes('full-width')

async def _handle_mobile_photo_upload(e):
    """Traite photo uploadée depuis mobile"""
    try:
        # Convertir en frame OpenCV
        content = e.content.read()
        nparr = np.frombuffer(content, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Analyser avec perception existante
        perception = _ensure_perception()
        if perception:
            result = await perception._analyze_frame_with_llm(frame, force=True)
            
            if result and result.get('description'):
                # Afficher dans le chat comme message système
                with _chat_inner:
                    _message('system', f"📸 **Photo analysée** : {result['description']}")
                
                # Ajouter à l'historique pour contexte
                _chat_history.append({
                    'role': 'system',
                    'content': f"[Photo analysée par perception visuelle] : {result['description']}"
                })
                
                ui.notify('Photo analysée avec succès !', type='positive')
            else:
                ui.notify('Impossible d\'analyser la photo', type='warning')
    except Exception as ex:
        print(f"[MOBILE-PHOTO] ❌ Erreur : {ex}")
        import traceback
        traceback.print_exc()
        ui.notify(f'Erreur analyse photo : {ex}', type='negative')
```

**Étape 3 : Optimiser Upload Fichier Mobile** (15 min)
- Bouton upload existant fonctionne déjà
- Juste ajouter attribut `capture` pour accès direct caméra documents
- Améliorer responsive mobile si besoin

---

#### 🎯 Résultat Final

**Champignon en forêt** :
- Photo → Perception analyse → "champignon brun avec lamelles blanches"
- Toi : "C'est quoi ce champignon ?"
- OGMA → Web search → "Agaricus campestris (champignon de Paris sauvage), comestible"

**PDF email** :
- Upload PDF → File processor extrait texte
- Toi : "Résume ce contrat"
- OGMA → Synthèse depuis mémoire du document

**Capacités existantes activées partout** :
- ✅ Recherche web (phrase magique "il faut que je cherche")
- ✅ Traitement documents (PDF, DOCX, images avec OCR)
- ✅ Analyse visuelle (GPT-4 Vision, Claude Vision)
- ✅ Mémoire persistante (tout est mémorisé)

---

#### 📊 Effort Total vs Valeur

| Tâche | Temps | Complexité | Valeur Ajoutée |
|-------|-------|------------|----------------|
| Cloudflare Tunnel | 30 min | 🟢 Trivial | ⭐⭐⭐⭐⭐ Accès mobile |
| Upload photo | 30 min | 🟢 Trivial | ⭐⭐⭐⭐⭐ Use case champignon |
| Optim upload fichier | 15 min | 🟢 Trivial | ⭐⭐⭐ Use case PDF |
| **TOTAL** | **1h15** | 🟢 **TRIVIAL** | **🚀 GAME CHANGER** |

---

#### 💡 Ce Qui Change Conceptuellement

**AVANT** : OGMA = assistant fixe sur PC, accessible seulement chez toi  
**APRÈS** : OGMA = compagnon IA accessible partout, analyse le monde que tu vois

**La philosophie OGMA reste intacte** :
- ✅ Mémoire persistante locale (SQLite + FAISS sur PC serveur)
- ✅ Privacy-first (données jamais dans le cloud)
- ✅ Croissance organique (souvenirs s'enrichissent)
- **NOUVEAU** : Perception étendue au-delà du PC (yeux = ta caméra mobile)

**C'est exactement l'esprit OpenClaw** : l'IA accessible partout, qui fait des trucs utiles.

---

#### ✅ Verdict Final

**Faisabilité** : 🟢 **TRIVIAL** - 1h15 dev total  
**Alignement OGMA** : ✅ **PARFAIT** - étend les capacités sans dénaturer  
**Recommandation** : **GO IMMÉDIAT** - c'est le sweet spot effort/valeur

**Prochaine étape** : Tu veux qu'on setup Cloudflare Tunnel maintenant ou tu veux continuer à explorer d'autres idées OpenClaw ?

---

## 🎬 PLAN D'ACTION VALIDÉ

### Étape 1 : Test Upload Photo Mobile (Local) ✅ PRIORITAIRE

**Objectif** : Valider la fonctionnalité upload photo + analyse AVANT l'accès distant
**Approche** : Coder et tester en réseau local d'abord
**Environnement** : Mobile connecté au même WiFi que le PC serveur OGMA
**Tests à valider** :
- [ ] Bouton "📸 Capturer" accessible interface mobile
- [ ] Capture photo native mobile (HTML5 `capture="camera"`)
- [ ] Upload → conversion numpy → OpenCV
- [ ] Analyse perception visuelle (GPT-4V/Claude)
- [ ] Intégration résultat dans chat comme contexte
- [ ] Workflow complet : photo champignon → "c'est quoi ?" → recherche web

**Fichiers à modifier** :
- `ogma_ng.py` : Ajout UI bouton + handler upload
- Possiblement : `ogma_perception.py` si adaptation nécessaire

**Durée estimée** : 30-45 min code + 15 min tests

---

### Étape 2 : Implémentation Cloudflare Tunnel ✅ APRÈS VALIDATION

**Objectif** : Rendre OGMA accessible en dehors du réseau local
**Prérequis** : Étape 1 validée et fonctionnelle
**Solution technique** : Cloudflare Tunnel (cloudflared)
**Avantages** :
- Zéro modification code OGMA
- HTTPS + authentification native
- Gratuit usage personnel
- Compatible NiceGUI/WebSockets

**Configuration** :
1. Installation `cloudflared`
2. Création tunnel Cloudflare dashboard
3. Config `~/.cloudflared/config.yml` pointant vers `localhost:8080`
4. Activation Cloudflare Access (auth email/Google)
5. Test accès externe via URL publique

**Durée estimée** : 30 min setup + 15 min tests

---

### Validation Finale

**Une fois étapes 1 + 2 complétées** :
- ✅ OGMA accessible partout (mobile 4G/WiFi externe)
- ✅ Upload photo champignon en forêt → analyse + recherche
- ✅ Upload PDF depuis email mobile → extraction + synthèse
- ✅ Toutes capacités OGMA portables

**Transformation conceptuelle** :
OGMA fixe PC → **OGMA compagnon mobile avec perception étendue**

---

## ✅ IMPLÉMENTATION IDÉE #3 - BILAN FINAL

**Date d'implémentation** : Session courante  
**Statut** : ✅ **COMPLÈTE - 4 phases, 44 tests, 0 échecs**

### Fichiers créés/modifiés

| Fichier | Action | Description |
|---------|--------|-------------|
| `modules/logic/image_generation.py` | MODIFIÉ | +300 lignes : `_prepare_image_for_vision()`, `_parse_i2i_analysis_json()`, `_normalize_analysis()`, `analyze_i2i_result()`, flags stop, `refine_i2i_prompt()`, `generate_img2img_with_correction()`, branchement autocorrect/one-shot dans pipeline |
| `modules/logic/i2i_lessons.py` | **CRÉÉ** | ~600 lignes : `I2ILessonsManager` SQLite, stockage/retrieval leçons, propositions guide, versioning, approbation/rejet |
| `modules/logic/__init__.py` | MODIFIÉ | Exports : toutes nouvelles fonctions + classes |
| `ogma_image_config.py` | MODIFIÉ | Defaults i2i_autocorrect + Section UI "Boucle Auto-Corrective I2I" (checkbox, sliders, textarea, reset) |
| `ogma_ng.py` | MODIFIÉ | +8 lignes : reset stop flag + notification autocorrect |
| `tests/test_i2i_analysis_parsing.py` | **CRÉÉ** | 11 tests Phase 1 |
| `tests/test_i2i_correction_loop.py` | **CRÉÉ** | 9 tests Phase 2 |
| `tests/test_i2i_lessons.py` | **CRÉÉ** | 12 tests Phase 3 |
| `tests/test_i2i_guide_proposals.py` | **CRÉÉ** | 12 tests Phase 4 |

### Architecture implémentée (4 couches)

1. **Analyse structurée** : Vision API + checklist systématique → JSON score/défauts/correction
2. **Boucle corrective** : Generate → Analyze → Refine prompt → Retry (max N, seuil configurable)
3. **Leçons persistantes** : SQLite `i2i_lessons.db`, recherche par mots-clés, injection contexte
4. **Auto-évolution guide** : Proposition basée sur leçons récurrentes → Approbation Yohan → Application settings.json

### Respect des contraintes

- ✅ **Modularité** : ogma_ng.py +8 lignes seulement (< 15 max)
- ✅ **Frontend priorité** : textarea dans settings = source de vérité
- ✅ **IA Principale** : gère analyse + refinement + proposition guide
- ✅ **Anti-régression** : mode one-shot inchangé quand autocorrect désactivé
- ✅ **Flag stop** : interruption utilisateur respectée entre tentatives

---