#!/usr/bin/env python3
"""
Hybrid API Detection System
============================

Système hybride qui combine détection API et spécifications officielles.
Utilise les meilleures valeurs disponibles en détectant le bridage.
"""

import requests
import json
import logging
from typing import Dict, Optional, Tuple

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache global pour éviter détections multiples
_DETECTION_CACHE = {}

# Fallbacks par provider (si modèle absent de OFFICIAL_SPECIFICATIONS)
# Valeurs minimales sûres pour éviter context overflow
PROVIDER_FALLBACKS = {
    "openai":      {"context_length": 128000, "max_tokens": 8192},
    "anthropic":   {"context_length": 200000, "max_tokens": 8192},
    "mistral":     {"context_length": 128000, "max_tokens": 8192},
    "google":      {"context_length": 1048576, "max_tokens": 8192},
    "grok":        {"context_length": 131072,  "max_tokens": 16384},
    "minimax":     {"context_length": 1000000, "max_tokens": 40960},
    "openrouter":  {"context_length": 32768,   "max_tokens": 4096},  # conservatif car modèles variés
    "deepseek":    {"context_length": 163840,  "max_tokens": 32768},
    "qwen":        {"context_length": 131072,  "max_tokens": 16384},
    "cohere":      {"context_length": 128000,  "max_tokens": 4096},
    "meta-llama":  {"context_length": 131072,  "max_tokens": 8192},
    "default":     {"context_length": 32768,   "max_tokens": 4096},
}

# Base de données des spécifications officielles
OFFICIAL_SPECIFICATIONS = {
    "openai": {
        "gpt-5": {"context_length": 192000, "max_tokens": 16384},
        "gpt-5-nano": {"context_length": 128000, "max_tokens": 16384},
        "gpt-5-mini": {"context_length": 128000, "max_tokens": 16384},
        "gpt-5-chat": {"context_length": 192000, "max_tokens": 16384},
        "gpt-5-chat-latest": {"context_length": 192000, "max_tokens": 16384},
        "gpt-5-latest": {"context_length": 192000, "max_tokens": 16384},
        "gpt-4o": {"context_length": 128000, "max_tokens": 16384},
        "gpt-4o-mini": {"context_length": 128000, "max_tokens": 16384},
        "gpt-4-turbo": {"context_length": 128000, "max_tokens": 4096},
        "gpt-4": {"context_length": 8192, "max_tokens": 4096},
    },
    "mistral": {
        "pixtral-large-latest": {"context_length": 128000, "max_tokens": 8192},
        "pixtral-large": {"context_length": 128000, "max_tokens": 8192},
        "mistral-large-latest": {"context_length": 128000, "max_tokens": 8192},
        "mistral-medium-2505": {"context_length": 128000, "max_tokens": 8192},
        "mistral-small-latest": {"context_length": 128000, "max_tokens": 8192},
    },
    "anthropic": {
        "claude-3.5-sonnet": {"context_length": 200000, "max_tokens": 8192},
        "claude-3.5-haiku": {"context_length": 200000, "max_tokens": 8192},
        "claude-3-opus": {"context_length": 200000, "max_tokens": 4096},
        "claude-3-sonnet": {"context_length": 200000, "max_tokens": 4096},
        "claude-3-haiku": {"context_length": 200000, "max_tokens": 4096},
    },
    "google": {
        # Gemini 3.x (dernière génération - Jan 2026)
        "gemini-3-pro": {"context_length": 1048576, "max_tokens": 65536},
        "gemini-3-flash": {"context_length": 1048576, "max_tokens": 65536},
        # Gemini 2.5
        "gemini-2.5-pro": {"context_length": 1048576, "max_tokens": 65536},
        "gemini-2.5-flash": {"context_length": 1048576, "max_tokens": 65536},
        "gemini-2.5-flash-lite": {"context_length": 1048576, "max_tokens": 8192},
        # Gemini 2.0
        "gemini-2.0-flash": {"context_length": 1048576, "max_tokens": 8192},
        # Gemini 1.5 (legacy)
        "gemini-1.5-pro": {"context_length": 2097152, "max_tokens": 8192},
        "gemini-1.5-flash": {"context_length": 1048576, "max_tokens": 8192},
    },
    "grok": {
        "grok-4": {"context_length": 256000, "max_tokens": 32768},
        "grok-4-0709": {"context_length": 256000, "max_tokens": 32768},
        "grok-4-fast": {"context_length": 2000000, "max_tokens": 32768},
        "grok-4-fast-reasoning": {"context_length": 2000000, "max_tokens": 32768},
        "grok-4-fast-non-reasoning": {"context_length": 2000000, "max_tokens": 32768},
        "grok-3": {"context_length": 131072, "max_tokens": 16384},
        "grok-3-mini": {"context_length": 131072, "max_tokens": 16384},
        "grok-3-mini-fast": {"context_length": 131072, "max_tokens": 16384},
        "grok-2": {"context_length": 128000, "max_tokens": 16384},
        "grok-2-012": {"context_length": 128000, "max_tokens": 16384},
        "grok-2-vision-012": {"context_length": 128000, "max_tokens": 16384},
        "grok-code-fast-1": {"context_length": 128000, "max_tokens": 16384},
    },
    "minimax": {
        "minimax-m2.7": {"context_length": 1000000, "max_tokens": 40960},
        "minimax-m2": {"context_length": 1000000, "max_tokens": 40960},
        "minimax-01": {"context_length": 1000000, "max_tokens": 4096},
    },
    "openrouter": {
        # MiniMax
        "minimax/minimax-m2.7": {"context_length": 1000000, "max_tokens": 40960},
        "minimax/minimax-m2": {"context_length": 1000000, "max_tokens": 40960},
        "minimax/minimax-01": {"context_length": 1000000, "max_tokens": 4096},
        # DeepSeek
        "deepseek/deepseek-r2": {"context_length": 163840, "max_tokens": 32768},
        "deepseek/deepseek-r1": {"context_length": 163840, "max_tokens": 32768},
        "deepseek/deepseek-chat-v3-5": {"context_length": 163840, "max_tokens": 32768},
        "deepseek/deepseek-v3": {"context_length": 163840, "max_tokens": 32768},
        # Qwen
        "qwen/qwen3-235b-a22b": {"context_length": 131072, "max_tokens": 16384},
        "qwen/qwen3-32b": {"context_length": 131072, "max_tokens": 16384},
        # Meta
        "meta-llama/llama-4-maverick": {"context_length": 1048576, "max_tokens": 16384},
        "meta-llama/llama-4-scout": {"context_length": 512000, "max_tokens": 16384},
        "meta-llama/llama-3.3-70b-instruct": {"context_length": 131072, "max_tokens": 16384},
        # Mistral (via OpenRouter)
        "mistralai/mistral-large-2411": {"context_length": 128000, "max_tokens": 8192},
        "mistralai/mistral-small-3.2-24b-instruct": {"context_length": 128000, "max_tokens": 8192},
    }
}

class HybridDetection:
    """Système de détection hybride API + spécifications."""
    
    def __init__(self):
        self.bridging_threshold = 0.5  # Si API < 50% officiel, utiliser officiel
        self.cache = {}
        
    def detect_with_hybrid_approach(self, provider: str, model: str, api_type: str, api_key: str) -> Dict[str, int]:
        """
        Détection hybride intelligente.
        
        Args:
            provider: Provider (openai, mistral, etc.)
            model: Nom du modèle
            api_type: Type d'API (chat, reasoning, embedding)
            api_key: Clé API
            
        Returns:
            Dict avec context_length et max_tokens optimaux
        """
        print(f"[HYBRID-DETECT] 🔄 {provider}/{model} - Détection hybride")
        
        # Étape 1: Récupérer spécifications officielles
        official_specs = self._get_official_specs(provider, model)
        
        # Étape 2: Tenter détection API
        api_detected = self._detect_via_api(provider, model, api_type, api_key)
        
        # Étape 3: Analyser et choisir la meilleure option
        optimal_caps = self._choose_optimal_capabilities(
            provider, model, official_specs, api_detected
        )
        
        return optimal_caps
    
    def _get_official_specs(self, provider: str, model: str) -> Optional[Dict[str, int]]:
        """Récupère les spécifications officielles."""
        
        provider_lower = provider.lower()
        official_specs = OFFICIAL_SPECIFICATIONS.get(provider_lower, {}).get(model)
        
        if official_specs:
            print(f"[HYBRID-DETECT] 📋 Spéc officielle: {official_specs['context_length']:,}/{official_specs['max_tokens']:,}")
            return official_specs
        else:
            print(f"[HYBRID-DETECT] ❌ Pas de spéc officielle pour {provider}/{model}")
            return None
    
    def _detect_via_api(self, provider: str, model: str, api_type: str, api_key: str) -> Optional[Dict[str, int]]:
        """Détecte via API."""
        
        try:
            # Importer le système de vraie détection
            from scripts.utils.real_api_detection import real_auto_detect_capabilities
            
            api_detected = real_auto_detect_capabilities(provider, model, api_type, api_key)
            print(f"[HYBRID-DETECT] 🔍 API détecté: {api_detected['context_length']:,}/{api_detected['max_tokens']:,}")
            return api_detected
            
        except Exception as e:
            print(f"[HYBRID-DETECT] ❌ Erreur détection API: {e}")
            return None
    
    def _choose_optimal_capabilities(self, provider: str, model: str, 
                                   official_specs: Optional[Dict], 
                                   api_detected: Optional[Dict]) -> Dict[str, int]:
        """Choisit les capacités optimales."""
        
        print(f"[HYBRID-DETECT] 🎯 Analyse optimale pour {provider}/{model}")
        
        # Si pas de détection API, utiliser officiel ou fallback provider
        if not api_detected:
            if official_specs:
                print(f"[HYBRID-DETECT] ✅ Utilise spéc officielle (pas d'API)")
                return official_specs
            else:
                fallback = PROVIDER_FALLBACKS.get(provider.lower(), PROVIDER_FALLBACKS["default"])
                print(f"[HYBRID-DETECT] 🔄 Fallback provider '{provider}': {fallback['context_length']:,}/{fallback['max_tokens']:,}")
                return fallback
        
        # Si pas de spéc officielle, utiliser API
        if not official_specs:
            print(f"[HYBRID-DETECT] ✅ Utilise API (pas de spéc officielle)")
            return api_detected
        
        # Comparer API vs Officiel
        api_context = api_detected['context_length']
        official_context = official_specs['context_length']
        api_max = api_detected['max_tokens'] 
        official_max = official_specs['max_tokens']
        
        # Calculer le ratio de bridage
        context_ratio = api_context / official_context if official_context > 0 else 1
        max_tokens_ratio = api_max / official_max if official_max > 0 else 1
        
        print(f"[HYBRID-DETECT] 📊 Ratios API/Officiel:")
        print(f"   Context: {context_ratio:.2%} ({api_context:,} vs {official_context:,})")
        print(f"   Max Tokens: {max_tokens_ratio:.2%} ({api_max:,} vs {official_max:,})")
        
        # Détecter bridage significatif
        context_bridged = context_ratio < self.bridging_threshold
        max_tokens_bridged = max_tokens_ratio < self.bridging_threshold
        
        # Choisir la meilleure valeur pour chaque paramètre
        optimal_context = official_context if context_bridged else api_context
        optimal_max = official_max if max_tokens_bridged else api_max
        
        # Logs de décision
        if context_bridged:
            loss = (1 - context_ratio) * 100
            print(f"[HYBRID-DETECT] 🚨 Context bridé API: -{loss:.1f}% → Utilise officiel")
        else:
            print(f"[HYBRID-DETECT] ✅ Context API acceptable → Utilise API")
            
        if max_tokens_bridged:
            loss = (1 - max_tokens_ratio) * 100
            print(f"[HYBRID-DETECT] 🚨 Max tokens bridé API: -{loss:.1f}% → Utilise officiel")
        else:
            print(f"[HYBRID-DETECT] ✅ Max tokens API acceptable → Utilise API")
        
        optimal_caps = {
            "context_length": optimal_context,
            "max_tokens": optimal_max
        }
        
        print(f"[HYBRID-DETECT] 🎯 OPTIMAL: {optimal_caps['context_length']:,}/{optimal_caps['max_tokens']:,}")
        
        return optimal_caps

def hybrid_auto_detect_capabilities(provider: str, model: str, api_type: str, api_key: str) -> Dict[str, int]:
    """
    Interface principale pour la détection hybride avec CACHE.
    
    Args:
        provider: Provider (openai, mistral, anthropic, google)
        model: Nom du modèle
        api_type: Type d'API (chat, reasoning, embedding)
        api_key: Clé API
        
    Returns:
        Dict avec context_length et max_tokens optimaux
    """
    # Vérification cache
    cache_key = f"{provider}/{model}/{api_type}"
    if cache_key in _DETECTION_CACHE:
        print(f"[HYBRID-CACHE] ✅ {cache_key} (from cache)")
        return _DETECTION_CACHE[cache_key]
    
    print(f"[HYBRID-AUTO-DETECT] 🚀 {provider}/{model} ({api_type})")
    
    detector = HybridDetection()
    
    try:
        result = detector.detect_with_hybrid_approach(provider, model, api_type, api_key)
        # Mise en cache
        _DETECTION_CACHE[cache_key] = result
        return result
    except Exception as e:
        print(f"[HYBRID-AUTO-DETECT] ❌ Erreur: {e}")
        # Fallback ultime par provider
        fallback = PROVIDER_FALLBACKS.get(provider.lower(), PROVIDER_FALLBACKS["default"])
        print(f"[HYBRID-AUTO-DETECT] 🔄 Fallback provider '{provider}': {fallback['context_length']:,}/{fallback['max_tokens']:,}")
        _DETECTION_CACHE[cache_key] = fallback
        return fallback

if __name__ == "__main__":
    print("🧠 OGMA - SYSTÈME DÉTECTION HYBRIDE")
    print("===================================")
    
    # Tests de démonstration
    test_cases = [
        ("openai", "gpt-5-chat-latest", "chat", "fake-key"),
        ("openai", "gpt-5", "chat", "fake-key"),
        ("mistral", "pixtral-large-latest", "chat", "fake-key"),
        ("anthropic", "claude-3.5-sonnet", "reasoning", "fake-key")
    ]
    
    for provider, model, api_type, api_key in test_cases:
        print(f"\n🔍 Test hybride {provider}/{model}:")
        try:
            result = hybrid_auto_detect_capabilities(provider, model, api_type, api_key)
            print(f"   ✅ Résultat optimal: {result['context_length']:,} context, {result['max_tokens']:,} max_tokens")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
    
    print(f"\n" + "=" * 60)
    print("✅ SYSTÈME HYBRIDE PRÊT!")
    print("🎯 Combine API + spécifications officielles")
    print("🚨 Détecte automatiquement le bridage API")
    print("💡 Utilise toujours les meilleures capacités disponibles")
    print("=" * 60)