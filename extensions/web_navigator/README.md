# 🌐 Extension Web Navigator pour OGMA

## Vue d'ensemble

L'extension **Web Navigator** permet à OGMA de naviguer sur internet et d'analyser des images en ligne via des commandes simples dans le chat.

## 🚀 Fonctionnalités

### Navigation Web (`/web`)
- **Commande :** `/web https://exemple.com`
- **Fonction :** Lit et résume le contenu d'une page web
- **Extraction :** Titre, description, contenu principal, liens
- **Nettoyage :** Suppression automatique des éléments non pertinents
- **Formats :** Support HTML avec fallback regex si BeautifulSoup indisponible

### Analyse d'Images (`/image`)  
- **Commande :** `/image https://site.com/photo.jpg`
- **Fonction :** Télécharge et analyse une image avec la vision d'OGMA
- **Sauvegarde :** Automatique dans `data/uploads/`
- **Formats :** JPG, PNG, GIF, WebP (configurable)
- **Taille max :** 10MB par défaut (configurable)

### Configuration (`/web-config`)
- **Commande :** `/web-config` 
- **Fonction :** Affiche configuration et statistiques actuelles
- **Informations :** État, limites, domaines, statistiques d'usage

## 📋 Installation

### Dépendances
```bash
pip install beautifulsoup4 lxml
```

### Structure des fichiers
```
extensions/web_navigator/
├── __init__.py              # Point d'entrée
├── config.py               # Configuration
├── web_scraper.py          # Navigation web
├── image_fetcher.py        # Téléchargement images
├── commands.py             # Gestion commandes chat
├── ui_components.py        # Interface paramètres
└── requirements.txt        # Dépendances
```

## ⚙️ Configuration

### Paramètres par défaut
```json
{
  "enabled": true,
  "web_scraping_enabled": true,
  "image_analysis_enabled": true,
  "max_page_size_mb": 1.0,
  "max_image_size_mb": 10.0,
  "request_timeout": 30,
  "rate_limit_seconds": 2.0,
  "allowed_domains": ["*"],
  "blocked_domains": [],
  "save_downloaded_images": true,
  "image_save_directory": "data/uploads"
}
```

### Accès aux paramètres
1. **Interface OGMA :** Menu → Paramètres → Web Navigator
2. **Configuration automatique :** Intégration dans `settings.json`
3. **Domaines :** Tous autorisés par défaut, liste noire configurable

## 🎮 Utilisation

### Exemples de commandes

**Navigation sur Wikipedia :**
```
/web https://wikipedia.org/wiki/Intelligence_artificielle
```

**Lecture d'actualités :**
```
/web lemonde.fr
```
*(https:// ajouté automatiquement)*

**Analyse d'image :**
```
/image https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/AI.jpg/640px-AI.jpg
```

**Vérification configuration :**
```
/web-config
```

### Réponses OGMA

**Navigation réussie :**
```
[NAVIGATION WEB] Contenu de la page : https://exemple.com

**Titre :** Page d'exemple
**Description :** Description de la page
**Contenu principal :** 
[Contenu extrait et nettoyé...]

**Liens trouvés :**
- [Lien 1](https://exemple.com/lien1)
- [Lien 2](https://exemple.com/lien2)

**Statistiques :** 245 mots extraits
```

**Image téléchargée :**
```
🖼️ Image téléchargée et prête pour analyse

**Source :** https://site.com/photo.jpg
**Fichier :** web_image_1634567890_abc123.jpg
**Taille :** 2.34MB
**Sauvegarde :** C:\IA\OGMA\data\uploads\web_image_1634567890_abc123.jpg

*Analyse de l'image en cours...*
```

## 🛡️ Sécurité & Limites

### Sécurité intégrée
- **Rate limiting :** 2 secondes entre requêtes (configurable)
- **Timeouts :** 30 secondes max par requête
- **Taille max :** 1MB pour pages web, 10MB pour images
- **Domaines :** Système whitelist/blacklist
- **SSL :** Vérification certificats par défaut

### Limitations techniques  
- **JavaScript :** Sites JS lourds peuvent nécessiter Selenium (future extension)
- **Authentification :** Pas de support cookies/sessions
- **Formats :** HTML principalement, pas de PDF/Word
- **Performance :** Impact tokens sur gros contenus

### Gestion d'erreurs
- **Domaine bloqué :** Message clair avec domaine
- **Timeout :** Indication du délai dépassé  
- **Format non supporté :** Liste des formats acceptés
- **Erreur réseau :** Diagnostics de connexion

## 🔧 Architecture technique

### Classes principales

**WebNavigatorConfig :** Gestion configuration et paramètres
**WebScraper :** Moteur navigation et extraction HTML  
**ImageFetcher :** Téléchargement et validation d'images
**WebNavigatorCommands :** Traitement commandes chat
**WebNavigatorUI :** Interface paramètres NiceGUI

### Intégration OGMA

**Point d'entrée :** `logic_callbacks.py` dans `enhanced_chat_fn()`
**Détection :** Messages commençant par `/web`, `/image`, `/web-config` 
**Traitement :** Asynchrone pour éviter blocage UI
**Résultat :** Injection dans flux de conversation normal

### Flux de données

1. **Commande détectée** → Parsing URL et validation
2. **Requête HTTP** → Avec rate limiting et sécurité
3. **Traitement** → Extraction/téléchargement selon type
4. **Formatage** → Préparation pour IA conversationnelle  
5. **Injection** → Intégration dans réponse chat

## 📊 Statistiques & Monitoring

### Métriques collectées
- Nombre de commandes `/web` et `/image`
- Taux de réussite des requêtes
- Erreurs par type (timeout, domaine, format, etc.)
- Temps de dernière utilisation

### Accès aux statistiques
- **Interface :** Bouton "Actualiser statistiques" dans paramètres
- **Commande :** `/web-config` affiche statistiques de session
- **Logs :** Messages détaillés dans console OGMA

## 🎯 Évolutions futures possibles

### Fonctionnalités avancées
- **Selenium :** Support sites JavaScript complexes
- **Authentification :** Gestion cookies et sessions
- **Formats :** PDF, Word, Excel via libraries dédiées
- **Cache :** Système de cache intelligent pour URLs fréquentes
- **Batch :** Traitement multiple d'URLs en une commande

### Optimisations
- **Performance :** Cache intelligent, compression
- **Précision :** Amélioration extraction contenu principal  
- **Sécurité :** Sandbox, analyse malware basique
- **UI :** Interface graphique navigation dans OGMA

## 🆘 Dépannage

### Problèmes courants

**Extension non disponible :**
```bash
pip install beautifulsoup4 lxml
```

**Erreur réseau :**
- Vérifier connexion internet
- Tester avec `/web-config` puis bouton "Test connexion"

**Site inaccessible :**
- Vérifier que le domaine n'est pas dans la blacklist
- Certains sites bloquent les bots (User-Agent configurable)

**Images non téléchargées :**
- Vérifier format supporté (JPG, PNG, GIF, WebP)
- Vérifier taille < limite configurée
- Vérifier permissions dossier `data/uploads/`

### Support

**Logs détaillés :** Tous préfixés `[WEB-NAV]`, `[WEB-SCRAPER]`, `[IMAGE-FETCHER]`
**Configuration :** Accessible via interface OGMA → Paramètres → Web Navigator  
**Reset config :** Bouton "Réinitialiser config" dans l'interface

---

*Extension Web Navigator v1.0.0 - Développée pour OGMA*