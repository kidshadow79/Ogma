#!/usr/bin/env python3
"""
Model Capabilities Database - Base de données des capacités des modèles
======================================================================

Référentiel des capacités réelles des modèles par provider.
"""

# Base de données des capacités des modèles
MODEL_CAPABILITIES = {
    # Mistral Models
    "mistral": {
        "mistral-tiny": {"context_length": 32768, "max_tokens": 8192},
        "mistral-small": {"context_length": 128000, "max_tokens": 8192},
        "mistral-small-latest": {"context_length": 128000, "max_tokens": 8192},
        "mistral-medium": {"context_length": 32768, "max_tokens": 8192},
        "mistral-medium-latest": {"context_length": 32768, "max_tokens": 8192},
        "mistral-medium-2312": {"context_length": 32768, "max_tokens": 8192},
        "mistral-medium-2405": {"context_length": 32768, "max_tokens": 8192},
        "mistral-medium-2505": {"context_length": 128000, "max_tokens": 8192},
        "mistral-large": {"context_length": 128000, "max_tokens": 8192},
        "mistral-large-latest": {"context_length": 128000, "max_tokens": 8192},
        "mistral-large-2402": {"context_length": 32768, "max_tokens": 8192},
        "mistral-large-2407": {"context_length": 128000, "max_tokens": 8192},
        "mistral-large-2411": {"context_length": 128000, "max_tokens": 8192},
        "pixtral-large": {"context_length": 128000, "max_tokens": 8192},
        "pixtral-large-latest": {"context_length": 128000, "max_tokens": 8192},
        "pixtral-12b": {"context_length": 128000, "max_tokens": 8192},
        "pixtral-12b-latest": {"context_length": 128000, "max_tokens": 8192},
        "codestral": {"context_length": 32768, "max_tokens": 8192},
        "codestral-latest": {"context_length": 32768, "max_tokens": 8192},
        "open-mistral-7b": {"context_length": 32768, "max_tokens": 8192},
        "open-mistral-8x7b": {"context_length": 32768, "max_tokens": 8192},
        "open-mistral-8x22b": {"context_length": 64000, "max_tokens": 8192},
        "open-codestral-mamba": {"context_length": 256000, "max_tokens": 8192},
        "mistral-embed": {"context_length": 8192, "max_tokens": 8192},
    },
    
    # OpenAI Models  
    "openai": {
        "gpt-3.5-turbo": {"context_length": 16385, "max_tokens": 4096},
        "gpt-3.5-turbo-16k": {"context_length": 16385, "max_tokens": 4096},
        "gpt-4": {"context_length": 8192, "max_tokens": 4096},
        "gpt-4-32k": {"context_length": 32768, "max_tokens": 4096},
        "gpt-4-turbo": {"context_length": 128000, "max_tokens": 4096},
        "gpt-4-turbo-preview": {"context_length": 128000, "max_tokens": 4096},
        "gpt-4o": {"context_length": 128000, "max_tokens": 16384},
        "gpt-4o-mini": {"context_length": 128000, "max_tokens": 16384},
        # GPT-5 Models (limites réelles testées avec l'API OpenAI - 16384 max_tokens)
        "gpt-5": {"context_length": 200000, "max_tokens": 16384},
        "gpt-5-chat": {"context_length": 200000, "max_tokens": 16384},
        "gpt-5-chat-latest": {"context_length": 200000, "max_tokens": 16384},
        "gpt-5-latest": {"context_length": 200000, "max_tokens": 16384},
        "text-embedding-3-small": {"context_length": 8191, "max_tokens": 8191},
        "text-embedding-3-large": {"context_length": 8191, "max_tokens": 8191},
    },
    
    # Anthropic Models
    "anthropic": {
        "claude-3-haiku": {"context_length": 200000, "max_tokens": 4096},
        "claude-3-sonnet": {"context_length": 200000, "max_tokens": 4096},
        "claude-3-opus": {"context_length": 200000, "max_tokens": 4096},
        "claude-3.5-sonnet": {"context_length": 200000, "max_tokens": 8192},
        "claude-3.5-haiku": {"context_length": 200000, "max_tokens": 8192},
    },
    
    # Google Models
    "google": {
        "gemini-1.5-pro": {"context_length": 2097152, "max_tokens": 8192},  # 2M tokens!
        "gemini-1.5-flash": {"context_length": 1048576, "max_tokens": 8192},  # 1M tokens!
        "gemini-pro": {"context_length": 32768, "max_tokens": 8192},
        "text-embedding-004": {"context_length": 2048, "max_tokens": 2048},
    },
    
    # Valeurs par défaut pour providers non reconnus
    "default": {
        "unknown": {"context_length": 4096, "max_tokens": 512}
    }
}

def get_model_capabilities(provider: str, model: str) -> dict:
    """
    Récupère les capacités d'un modèle spécifique.
    
    Args:
        provider: Provider (mistral, openai, anthropic, google, etc.)
        model: Nom du modèle
        
    Returns:
        dict: {"context_length": int, "max_tokens": int}
    """
    provider = provider.lower()
    model = model.lower()
    
    # Recherche exacte
    if provider in MODEL_CAPABILITIES:
        if model in MODEL_CAPABILITIES[provider]:
            return MODEL_CAPABILITIES[provider][model].copy()
        
        # Recherche partielle pour les modèles avec suffixes
        for model_key, capabilities in MODEL_CAPABILITIES[provider].items():
            if model_key in model or model in model_key:
                return capabilities.copy()
    
    # Fallback sur valeurs par défaut
    print(f"[MODEL-CAPABILITIES] ⚠️ Modèle {provider}/{model} non trouvé, utilisation valeurs par défaut")
    return MODEL_CAPABILITIES["default"]["unknown"].copy()

def auto_detect_capabilities(provider: str, model: str, api_type: str = "reasoning") -> dict:
    """
    Auto-détection des capacités avec ajustements selon le type d'API.
    
    Args:
        provider: Provider du modèle
        model: Nom du modèle  
        api_type: Type d'API (reasoning, chat, embedding)
        
    Returns:
        dict: {"context_length": int, "max_tokens": int}
    """
    base_capabilities = get_model_capabilities(provider, model)
    
    # Ajustements selon le type d'usage
    if api_type == "reasoning":
        # Pour l'archiviste, on peut utiliser la pleine capacité
        pass
    elif api_type == "chat":
        # Pour la conversation, on peut aussi utiliser la pleine capacité
        pass
    elif api_type == "embedding":
        # Pour l'embedding, généralement plus petit
        base_capabilities["max_tokens"] = min(base_capabilities["max_tokens"], 8192)
    
    print(f"[AUTO-DETECT] {provider}/{model} ({api_type}): {base_capabilities['context_length']:,} context, {base_capabilities['max_tokens']:,} max_tokens")
    
    return base_capabilities

def test_capabilities_database():
    """Test de la base de données des capacités."""
    
    print("🧪 TEST BASE DONNÉES CAPACITÉS MODÈLES")
    print("=" * 45)
    
    test_cases = [
        ("mistral", "mistral-small-latest", "128k expected"),
        ("mistral", "pixtral-large-latest", "128k expected"),
        ("mistral", "mistral-medium-2505", "128k expected"),
        ("openai", "gpt-4o", "128k expected"),
        ("anthropic", "claude-3.5-sonnet", "200k expected"),
        ("google", "gemini-1.5-pro", "2M expected"),
        ("unknown", "unknown-model", "4k fallback"),
    ]
    
    for provider, model, expectation in test_cases:
        caps = get_model_capabilities(provider, model)
        ctx_k = caps["context_length"] // 1000
        print(f"   {provider:12} {model:20} → {ctx_k:4}k context ({expectation})")

if __name__ == "__main__":
    print("🧠 OGMA - BASE DONNÉES CAPACITÉS MODÈLES")
    print("========================================")
    
    test_capabilities_database()
    
    print(f"\n💡 EXEMPLES AUTO-DETECT:")
    examples = [
        ("mistral", "mistral-small-latest", "reasoning"),
        ("mistral", "pixtral-large-latest", "chat"), 
        ("openai", "gpt-4o", "reasoning"),
    ]
    
    for provider, model, api_type in examples:
        caps = auto_detect_capabilities(provider, model, api_type)
        print(f"   {provider}/{model} → {caps['context_length']:,} tokens")