# 📋 NOTE TECHNIQUE : RÉGLAGES API FONCTIONNELS OGMA

## 🎯 Configuration API Par Provider

### ✅ **ARCHITECTURE API ACTUELLE FONCTIONNELLE**

**Structure APIManager dans `core_logic.py` (Lignes 373-890)**
```python
class APIManager:
    API_CONFIG = {
        "OpenAI": {
            "base_url": "https://api.openai.com/v1",
            "chat_endpoint": "/chat/completions",
            "models_endpoint": "/models",
            "embed_endpoint": "/embeddings"
        },
        "Anthropic": {
            "base_url": "https://api.anthropic.com/v1",
            "chat_endpoint": "/messages",
            "models_endpoint": None  # Anthropic n'a pas d'endpoint de liste
        },
        "Mistral": {
            "base_url": "https://api.mistral.ai/v1",
            "chat_endpoint": "/chat/completions",
            "models_endpoint": "/models",
            "embed_endpoint": "/embeddings"
        },
        "Google": {
            "base_url": "https://generativelanguage.googleapis.com",
            "chat_endpoint": "/v1/models/gemini-1.0-pro:generateContent",
            "models_endpoint": "/v1/models",
            "embed_endpoint": None  # Google utilise un système différent
        }
    }
```

---

## 🔧 **SYSTÈME MAX_TOKENS AUTO-ADAPTATIF (-1)**

### **Logique de fallback par provider (Ligne 588):**
```python
final_max_tokens = max_tokens if max_tokens != -1 else (8192 if self.provider in ["OpenAI", "Anthropic"] else 4096)
```

### **Valeurs par défaut natives (-1):**
- **OpenAI**: 8192 tokens
- **Anthropic**: 8192 tokens  
- **Mistral**: 4096 tokens
- **Google**: Configuré dans payload (ligne 728)

### **Spécificité OpenAI (Ligne 592):**
```python
if self.provider == "OpenAI":
    payload = {"model": self.model, "messages": final_api_messages, "max_completion_tokens": final_max_tokens, "temperature": temperature}
```
**Note**: OpenAI utilise `max_completion_tokens` au lieu de `max_tokens` pour certains modèles.

---

## 🌡️ **TEMPÉRATURE ADAPTATIVE**

### **Température actuelle:**
- **Valeur reçue directement** : `temperature` parameter dans les appels API
- **Pas de logique -1 implémentée** pour température auto-provider
- **Valeurs par défaut dans settings** : 0.7 (chat), 0.3 (reasoning)

### **À IMPLÉMENTER - Système -1 pour température:**
```python
# Températures natives recommandées par provider
PROVIDER_DEFAULT_TEMPERATURES = {
    "OpenAI": 1.0,      # Défaut OpenAI
    "Anthropic": 1.0,   # Défaut Anthropic  
    "Mistral": 0.7,     # Défaut Mistral
    "Google": 0.9       # Défaut Google
}

final_temperature = temperature if temperature != -1 else PROVIDER_DEFAULT_TEMPERATURES.get(self.provider, 0.7)
```

---

## 📏 **CONTEXT_LENGTH AUTOMATIQUE**

### **Système hybride existant (hybrid_detection.py):**
- **Détection API** + **Spécifications officielles**
- **Auto-détection intelligente** avec fallback
- **Utilisé uniquement pour Archiviste** (ligne 267-279 ogma_ng.py)

### **Base de données context_length (hybrid_detection.py ligne 18-30):**
```python
OFFICIAL_SPECIFICATIONS = {
    "openai": {
        "gpt-5": {"context_length": 192000, "max_tokens": 16384},
        "gpt-4o": {"context_length": 128000, "max_tokens": 16384},
        "gpt-4": {"context_length": 8192, "max_tokens": 4096},
    },
    "mistral": {
        "mistral-large": {"context_length": 128000, "max_tokens": 8192},
        "mistral-small": {"context_length": 128000, "max_tokens": 8192},
    }
    # + Anthropic, Google...
}
```

---

## 🔄 **LOGIC DE DÉTECTION HYBRIDE FONCTIONNELLE**

### **Fonction hybrid_auto_detect_capabilities():**
1. **Interroge l'API** pour capacités réelles
2. **Compare avec spécifications officielles**
3. **Détecte le bridage** (API < Officiel)
4. **Retourne les meilleures valeurs**

### **Messages de debug existants:**
```
[HYBRID-DETECT] 🔄 mistral/mistral-small-latest - Détection hybride
[REAL-DETECT] ✅ Modèle mistral-small-latest trouvé dans l'API Mistral
[HYBRID-DETECT] 🎯 OPTIMAL: 128,000/8,192
```

---

## 🎛️ **CONFIGURATION SETTINGS.JSON FONCTIONNELLE**

### **Section par IA avec -1 pour auto:**
```json
"chat_api": {
    "provider": "OpenAI",
    "api_key": "sk-...",
    "api_model": "gpt-4",
    "max_tokens": -1,        // Auto selon provider
    "context_length": -1,    // Auto-détection
    "temperature": 0.7,      // FIXE (à adapter en -1)
    "backend_type": "API"
}
```

---

## 🚨 **PARTICULARITÉS PAR PROVIDER**

### **OpenAI (Lignes 591-600):**
- Utilise `max_completion_tokens` 
- Format `response_format: {"type": "json_object"}` pour JSON
- Gestion multi-modal images dans content array

### **Anthropic (Lignes 604-690):**
- Structure messages différente avec `system` séparé
- Headers spéciaux: `anthropic-version: 2023-06-01`
- max_tokens obligatoire (pas de fallback API)

### **Mistral (Lignes 558-603):**
- Compatible OpenAI format
- Embeddings supportés
- Auto-détection fonctionnelle

### **Google (Lignes 696-780):**
- Format `generateContent` 
- API key dans URL : `?key={api_key}`
- Format images: `inlineData` avec `mimeType` et `data`
- Messages: `user`/`model` au lieu de `user`/`assistant`

---

## 📊 **DÉTECTION D'ERREURS PAR PROVIDER**

### **Gestion d'erreurs spécialisée (Lignes 779-850):**
```python
elif self.provider in ["OpenAI", "Mistral"]: 
    return None, f"Erreur {response.status_code}: {response.text}"
elif self.provider == "Anthropic":
    # Parse JSON error pour Anthropic
    return None, error_data.get('error', {}).get('message', 'Erreur inconnue')
elif self.provider == "Google": 
    # Parse structure Google spécifique
```

---

## ✅ **CE QUI FONCTIONNE ACTUELLEMENT**

1. ✅ **Auto-détection max_tokens** avec -1 selon provider
2. ✅ **Context_length hybride** pour Archiviste uniquement  
3. ✅ **Multi-providers** OpenAI/Mistral/Anthropic/Google
4. ✅ **Embeddings** OpenAI/Mistral/Google
5. ✅ **Images multi-modal** tous providers
6. ✅ **JSON mode** avec adaptations provider
7. ✅ **Gestion d'erreurs** spécialisée par provider

---

## 🔧 **À AMÉLIORER**

1. 🔄 **Température -1** pour valeurs natives provider
2. 🔄 **Context_length auto** pour Chat et Embeddings 
3. 🔄 **Settings unifiés** sans duplication other_backends
4. 🔄 **Status indicators** synchronisés avec configuration réelle
5. 🔄 **Simplification** logique backend sans fallback

---

## 🎯 **RÈGLES DE L'ARCHITECTURE PROPRE**

1. **UN backend = UNE configuration explicite**
2. **-1 = auto-détection native du provider**
3. **Pas de fallback automatique entre backends**
4. **Configuration visible et modifiable par l'utilisateur**
5. **Status en temps réel = configuration réelle**

---

*Documentation générée le 14 septembre 2025*
*Base: OGMA core_logic.py + ogma_ng.py + hybrid_detection.py*