# 📸 EXTENSION WEB VISION - Spécification Technique

**Date :** 1 novembre 2025  
**Statut :** 📋 Spécification - En attente d'implémentation  
**Priorité :** Moyenne  
**Complexité :** Moyenne (3-4 jours)

---

## 🎯 **OBJECTIF**

Permettre à Luna d'analyser des images directement depuis des URLs web sans nécessiter de téléchargement manuel par l'utilisateur.

**Cas d'usage :**
- "analyse cette image: https://example.com/photo.jpg"
- "/vision https://website.com/screenshot.png décris ce que tu vois"
- "que vois-tu sur cette image? [URL]"

---

## 🏗️ **ARCHITECTURE**

### **Extension Modulaire**
```
extensions/web_vision/
├── __init__.py              # API publique standardisée
├── url_detector.py          # Détection URLs images dans messages
├── image_downloader.py      # Téléchargement + cache temporaire
├── vision_formatter.py      # Formatage multimodal pour APIs
└── web_vision_agent.py      # Orchestrateur principal
```

### **Pattern OGMA Standard**
- Singleton global `_web_vision_ext`
- Fonction `_ensure_web_vision()` dans `ogma_ng.py`
- Hook pré-envoi message (avant traitement multimodal)
- Intégration minimale (~30 lignes dans ogma_ng.py)

---

## 🔧 **COMPOSANTS DÉTAILLÉS**

### **1. URL Detector (`url_detector.py`)**

**Responsabilité :** Détecter URLs images dans messages utilisateur

**Patterns détection :**
```python
# URLs images directes
r'https?://[^\s]+\.(?:jpg|jpeg|png|gif|webp|bmp)'

# Commande /vision
r'/vision\s+(https?://[^\s]+)'

# Patterns contextuels
r'(?:analyse|décris|regarde|vois)\s+(?:cette|l\')?image[:\s]+?(https?://[^\s]+)'
```

**Classe :** `URLDetector`
```python
class URLDetector:
    def detect(self, message: str) -> List[ImageURL]:
        """Détecte URLs images dans message"""
        
    def is_image_url(self, url: str) -> bool:
        """Vérifie si URL pointe vers une image"""
        
    def extract_all_urls(self, message: str) -> List[str]:
        """Extrait toutes URLs du message"""
```

**Dataclass :**
```python
@dataclass
class ImageURL:
    url: str
    extension: str
    confidence: float
    pattern_matched: str
```

---

### **2. Image Downloader (`image_downloader.py`)**

**Responsabilité :** Télécharger images web + gestion cache

**Fonctionnalités :**
- Téléchargement async images via `requests` ou `aiohttp`
- Validation format (MIME type, taille max)
- Cache temporaire `data/temp/web_vision_cache/`
- Nettoyage automatique (TTL 1h, max 50MB)
- Gestion erreurs (timeout, 404, taille excessive)

**Classe :** `ImageDownloader`
```python
class ImageDownloader:
    def __init__(self, cache_dir: str, max_size_mb: int = 10):
        """
        Args:
            cache_dir: Répertoire cache temporaire
            max_size_mb: Taille max image (défaut 10MB)
        """
        
    async def download(self, url: str) -> Optional[DownloadedImage]:
        """
        Télécharge image depuis URL
        
        Returns:
            DownloadedImage avec path, base64, metadata ou None
        """
        
    def cleanup_cache(self, max_age_hours: int = 1):
        """Nettoie fichiers cache anciens"""
        
    def get_cache_stats(self) -> dict:
        """Stats cache (total files, size, oldest)"""
```

**Dataclass :**
```python
@dataclass
class DownloadedImage:
    url: str
    local_path: str
    base64_data: str
    mime_type: str
    size_bytes: int
    width: int
    height: int
```

**Validation :**
- Formats supportés : JPG, PNG, GIF, WebP, BMP
- Taille max : 10MB (configurable)
- Timeout : 30 secondes
- User-Agent : "OGMA-WebVision/1.0"

---

### **3. Vision Formatter (`vision_formatter.py`)**

**Responsabilité :** Formater images pour APIs multimodales

**Fonctionnalités :**
- Conversion format OpenAI (image_url avec base64)
- Conversion format Anthropic (source base64)
- Conversion format GROK (compatible OpenAI)
- Support URLs directes (option sans download)

**Classe :** `VisionFormatter`
```python
class VisionFormatter:
    def format_for_openai(
        self, 
        image: DownloadedImage, 
        text_prompt: str
    ) -> dict:
        """
        Formate message multimodal OpenAI/GROK
        
        Returns:
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "..."},
                    {"type": "image_url", "image_url": {"url": "data:..."}}
                ]
            }
        """
        
    def format_for_anthropic(
        self, 
        image: DownloadedImage, 
        text_prompt: str
    ) -> dict:
        """
        Formate message multimodal Claude
        
        Returns:
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "..."},
                    {"type": "image", "source": {"type": "base64", ...}}
                ]
            }
        """
        
    def format_direct_url(self, url: str, text_prompt: str) -> dict:
        """Formate avec URL directe (pas de download)"""
```

---

### **4. Web Vision Agent (`web_vision_agent.py`)**

**Responsabilité :** Orchestration complète workflow

**Workflow :**
```
1. Détection URLs images (URLDetector)
2. Téléchargement images (ImageDownloader)
3. Formatage multimodal (VisionFormatter)
4. Injection dans messages système
5. Cleanup cache si nécessaire
```

**Classe :** `WebVisionAgent`
```python
class WebVisionAgent:
    def __init__(
        self,
        cache_dir: str = "data/temp/web_vision_cache",
        max_image_size_mb: int = 10,
        debug: bool = False
    ):
        self.detector = URLDetector(debug=debug)
        self.downloader = ImageDownloader(cache_dir, max_image_size_mb)
        self.formatter = VisionFormatter(debug=debug)
        
    async def process_message(
        self, 
        user_message: str,
        provider: str = "OpenAI"
    ) -> Optional[List[dict]]:
        """
        Traite message utilisateur pour vision web
        
        Args:
            user_message: Message utilisateur
            provider: Provider IA (OpenAI, Anthropic, GROK)
            
        Returns:
            Liste messages multimodaux ou None si pas d'image
        """
        
    def is_vision_request(self, message: str) -> bool:
        """Check rapide si message contient URL image"""
        
    def get_statistics(self) -> dict:
        """Stats extension (images_processed, cache_size, etc.)"""
        
    def cleanup(self):
        """Nettoyage complet cache"""
```

**Statistiques trackées :**
```python
{
    "images_detected": 0,
    "images_downloaded": 0,
    "download_failures": 0,
    "cache_size_bytes": 0,
    "cache_file_count": 0,
    "last_cleanup": None
}
```

---

### **5. API Publique (`__init__.py`)**

**Export standardisé :**
```python
def initialize_web_vision(
    cache_dir: str = "data/temp/web_vision_cache",
    max_image_size_mb: int = 10,
    auto_cleanup: bool = True,
    debug: bool = False
) -> object:
    """Initialise extension Web Vision"""
    
def is_available() -> bool:
    """Vérifie disponibilité extension"""
    
def get_web_vision():
    """Retourne singleton agent"""
    
async def process_message(
    user_message: str, 
    provider: str = "OpenAI"
) -> Optional[List[dict]]:
    """Interface publique traitement message"""
    
def get_statistics() -> dict:
    """Stats extension"""
    
def cleanup():
    """Nettoyage extension"""
```

---

## 🔌 **INTÉGRATION OGMA**

### **Modifications `ogma_ng.py`** (minimal ~30 lignes)

**1. Variable globale** (ligne ~152) :
```python
_web_vision_ext = None  # Extension Web Vision - Analyse images URLs
```

**2. Fonction initialisation** (après `_ensure_file_writer`) :
```python
def _ensure_web_vision():
    """Initialise l'extension Web Vision pour analyse images web"""
    global _web_vision_ext
    if _web_vision_ext is not None:
        return _web_vision_ext
    
    try:
        from extensions.web_vision import initialize_web_vision
        
        _web_vision_ext = initialize_web_vision(
            cache_dir="data/temp/web_vision_cache",
            max_image_size_mb=10,
            auto_cleanup=True,
            debug=False
        )
        
        if _web_vision_ext:
            print("[WEB-VISION] ✅ Extension initialisée")
        
    except Exception as e:
        print(f"[WEB-VISION] ⚠️ Erreur initialisation: {e}")
        _web_vision_ext = None
    
    return _web_vision_ext
```

**3. Hook pré-traitement message** (dans `_send_chat_message`, avant formatage multimodal) :
```python
# 📸 WEB VISION - Analyse images depuis URLs
print("[WEB-VISION] Vérification URLs images...")
try:
    web_vision = _ensure_web_vision()
    
    if web_vision and web_vision.is_vision_request(text):
        print("[WEB-VISION] 🔍 URL image détectée, téléchargement...")
        
        # Récupérer provider actuel
        chat_ctrl = _ensure_chat_controller()
        provider = chat_ctrl.backend_type if chat_ctrl else "OpenAI"
        
        # Traiter message avec vision web
        vision_messages = await web_vision.process_message(text, provider)
        
        if vision_messages:
            print(f"[WEB-VISION] ✅ Image traitée, injection multimodal")
            # Remplacer dernier message user par version multimodale
            if messages and messages[-1]['role'] == 'user':
                messages[-1] = vision_messages[0]
            else:
                messages.extend(vision_messages)
        else:
            print("[WEB-VISION] ⚠️ Échec traitement image")
    else:
        print("[WEB-VISION] ⚪ Pas d'URL image détectée")
except Exception as e:
    print(f"[WEB-VISION] ERROR: {e}")
```

---

## ⚙️ **CONFIGURATION**

### **Settings Extension**
```json
{
  "web_vision": {
    "enabled": true,
    "max_image_size_mb": 10,
    "cache_ttl_hours": 1,
    "max_cache_size_mb": 50,
    "auto_cleanup": true,
    "timeout_seconds": 30,
    "supported_formats": ["jpg", "jpeg", "png", "gif", "webp", "bmp"]
  }
}
```

### **Variables Environnement**
```bash
# Aucune clé API nécessaire (utilise APIs vision existantes)
```

---

## 🧪 **TESTS**

### **Script `test_web_vision.py`**

**Tests unitaires :**
1. **URLDetector** : Détection 10+ patterns URLs
2. **ImageDownloader** : Téléchargement, cache, cleanup
3. **VisionFormatter** : Formats OpenAI, Anthropic, GROK
4. **WebVisionAgent** : Workflow complet
5. **Integration** : Hook ogma_ng.py

**Exemples test :**
```python
# Test détection
assert detector.detect("analyse https://test.com/photo.jpg")

# Test download
image = await downloader.download("https://picsum.photos/200")
assert image.base64_data is not None

# Test format
msg = formatter.format_for_openai(image, "Décris cette image")
assert msg["content"][1]["type"] == "image_url"

# Test workflow
messages = await agent.process_message(
    "que vois-tu? https://example.com/img.png"
)
assert len(messages) > 0
```

---

## 🎯 **PROVIDERS VISION SUPPORTÉS**

### **OpenAI (GPT-4o, GPT-4 Turbo Vision)**
- ✅ Support natif URLs + base64
- ✅ Format `image_url` standard
- ✅ Meilleure qualité analyse

### **Anthropic (Claude 3.5 Sonnet, Claude 3 Opus)**
- ✅ Support base64 uniquement
- ✅ Format `image.source.base64`
- ✅ Excellente compréhension contextuelle

### **GROK (GROK-Vision)**
- ✅ Compatible format OpenAI
- ✅ Support URLs + base64
- ✅ Rapide

### **Limitations**
- ❌ Ollama : Support vision limité (modèles locaux uniquement)
- ❌ GGUF : Pas de support vision multimodale standard
- ❌ Mistral : Support vision en beta

---

## 🚀 **WORKFLOW UTILISATEUR**

### **Scénario 1 : Analyse Image Web Simple**
```
User: analyse cette image: https://example.com/photo.jpg

[WEB-VISION] 🔍 URL image détectée
[WEB-VISION] 📥 Téléchargement...
[WEB-VISION] ✅ Image traitée (1.2MB, 1920x1080)
[WEB-VISION] 📤 Injection format multimodal

Luna: Sur cette image, je vois un magnifique coucher de soleil 
sur une plage. Les couleurs orangées se reflètent sur l'eau...
```

### **Scénario 2 : Commande /vision**
```
User: /vision https://website.com/screenshot.png décris l'interface

[WEB-VISION] 🔍 Commande /vision détectée
[WEB-VISION] 📥 Téléchargement screenshot...
[WEB-VISION] ✅ Image traitée (450KB, 1366x768)

Luna: Cette capture d'écran montre une interface web moderne avec...
```

### **Scénario 3 : Comparaison Multiple Images**
```
User: compare ces deux images:
https://site.com/image1.jpg
https://site.com/image2.jpg

[WEB-VISION] 🔍 2 URLs images détectées
[WEB-VISION] 📥 Téléchargement parallèle...
[WEB-VISION] ✅ 2 images traitées

Luna: En comparant les deux images, je remarque que...
```

---

## 📊 **ESTIMATION DÉVELOPPEMENT**

### **Temps par composant**
- `url_detector.py` : **4h** (patterns regex + tests)
- `image_downloader.py` : **8h** (async download + cache + validation)
- `vision_formatter.py` : **4h** (formats multi-providers)
- `web_vision_agent.py` : **6h** (orchestration + stats)
- `__init__.py` : **2h** (API publique)
- Intégration `ogma_ng.py` : **2h** (hook + tests)
- Tests `test_web_vision.py` : **4h** (suite complète)

**Total estimé :** **30h** (3-4 jours)

---

## 🔒 **SÉCURITÉ**

### **Mesures Implémentées**
1. **Validation URLs** : Whitelist extensions images
2. **Taille max** : 10MB par défaut (configurable)
3. **Timeout** : 30s pour éviter blocages
4. **User-Agent** : Identifiant OGMA clair
5. **Cache sécurisé** : Cleanup automatique, pas de stockage permanent
6. **Validation MIME** : Vérification format réel fichier
7. **Sandbox** : Pas d'exécution code, lecture seule

### **Risques Potentiels**
- ⚠️ URLs malveillantes → **Mitigation : timeout + validation**
- ⚠️ Images énormes → **Mitigation : limite 10MB**
- ⚠️ Cache croissance → **Mitigation : cleanup auto 1h**
- ⚠️ Scraping détecté → **Mitigation : User-Agent + rate limiting**

---

## 📝 **DÉPENDANCES**

### **Bibliothèques Python**
```python
# Déjà installées dans OGMA
requests          # Download HTTP
Pillow (PIL)      # Validation images
pathlib           # Gestion fichiers
asyncio           # Async operations

# Optionnelles (amélioration perf)
aiohttp           # Async HTTP (alternative à requests)
```

### **Aucune clé API supplémentaire**
Utilise les APIs vision déjà configurées (OpenAI, Anthropic, GROK)

---

## 🎯 **ÉVOLUTIONS FUTURES**

### **V1.0 - MVP** (Cette spécification)
- Détection URLs basique
- Download + cache simple
- Formats OpenAI/Anthropic/GROK
- Stats basiques

### **V1.1 - Améliorations**
- Support authentification (headers customs)
- Rate limiting intelligent
- Compression images lourdes
- Preview thumbnails dans UI

### **V1.2 - Avancé**
- OCR automatique (Tesseract)
- Détection objets (YOLO local)
- Analyse batch multiple images
- Export résultats analyse

### **V2.0 - Intelligence**
- Cache persistant intelligent (LRU)
- Apprentissage préférences utilisateur
- Suggestions images similaires
- Intégration recherche web (Serper)

---

## 📚 **RÉFÉRENCES**

### **APIs Vision**
- [OpenAI Vision Guide](https://platform.openai.com/docs/guides/vision)
- [Anthropic Claude Vision](https://docs.anthropic.com/claude/docs/vision)
- [GROK Vision Docs](https://docs.x.ai/docs)

### **Standards**
- RFC 3986 (URI Generic Syntax)
- MIME Types for Images
- HTTP/1.1 RFC 2616

### **Inspiration**
- ChatGPT Vision
- Claude.ai Image Analysis
- Google Bard Multimodal

---

## ✅ **CHECKLIST IMPLÉMENTATION**

### **Phase 1 : Composants Core**
- [ ] Créer structure `extensions/web_vision/`
- [ ] Implémenter `url_detector.py`
- [ ] Implémenter `image_downloader.py`
- [ ] Implémenter `vision_formatter.py`
- [ ] Implémenter `web_vision_agent.py`
- [ ] Créer API publique `__init__.py`

### **Phase 2 : Intégration**
- [ ] Ajouter variable globale `ogma_ng.py`
- [ ] Créer `_ensure_web_vision()`
- [ ] Intégrer hook dans `_send_chat_message()`
- [ ] Tester avec GPT-4o
- [ ] Tester avec Claude 3.5
- [ ] Tester avec GROK Vision

### **Phase 3 : Tests**
- [ ] Créer `test_web_vision.py`
- [ ] Tests URLDetector (10+ cas)
- [ ] Tests ImageDownloader (cache, cleanup)
- [ ] Tests VisionFormatter (3 providers)
- [ ] Tests WebVisionAgent (workflow)
- [ ] Tests intégration OGMA

### **Phase 4 : Documentation**
- [ ] Commentaires code détaillés
- [ ] Docstrings toutes fonctions
- [ ] README extension
- [ ] Exemples utilisation
- [ ] Guide troubleshooting

### **Phase 5 : Polish**
- [ ] Optimisation performances
- [ ] Logs standardisés
- [ ] Gestion erreurs robuste
- [ ] UI notifications
- [ ] Settings configuration

---

## 🎉 **RÉSULTAT ATTENDU**

Une fois implémentée, cette extension permettra à Luna d'analyser **n'importe quelle image web** aussi facilement qu'une image locale, offrant une expérience multimodale complète et fluide.

**Exemple final :**
```
User: que penses-tu de cette photo? https://mysite.com/sunset.jpg

Luna: Quelle magnifique image ! Je vois un coucher de soleil spectaculaire
avec des nuances d'orange, de rose et de violet qui se reflètent sur l'océan.
La silhouette d'un palmier sur la gauche ajoute une touche tropicale. 
La composition est très équilibrée avec l'horizon placé sur le tiers inférieur.
C'est une photo qui inspire la sérénité et la contemplation. 🌅
```

---

**Prêt pour implémentation future** ✨
