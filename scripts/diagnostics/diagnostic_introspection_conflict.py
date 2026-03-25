"""
Diagnostic système introspection - Identifier conflit ancien/nouveau système
"""

print("=" * 70)
print("DIAGNOSTIC INTROSPECTION - CONFLIT SYSTÈMES")
print("=" * 70)

# 1. Vérifier ancien système (CognitiveMirrorCore)
print("\n1️⃣ Ancien système (CognitiveMirrorCore)...")
try:
    from extensions.cognitive_mirror.core_cognitive_mirror import CognitiveMirrorCore
    
    # Vérifier file messages
    pending = CognitiveMirrorCore.get_pending_messages()
    print(f"  ✅ CognitiveMirrorCore disponible")
    print(f"  📬 Messages en attente: {len(pending)}")
    print(f"  Méthode affichage: get_pending_messages() → ogma_ng.py ligne 770-870")
    
except ImportError as e:
    print(f"  ❌ CognitiveMirrorCore non disponible: {e}")

# 2. Vérifier nouveau système (IntrospectionCore v2.0)
print("\n2️⃣ Nouveau système (IntrospectionCore v2.0)...")
try:
    from extensions.cognitive_mirror import get_introspection_core, get_introspection
    
    core_v2 = get_introspection_core()
    
    if core_v2:
        print(f"  ✅ IntrospectionCore v2.0 disponible")
        print(f"  Type: {type(core_v2)}")
        print(f"  Enabled: {core_v2.is_enabled}")
        print(f"  Méthode affichage: callbacks → _on_introspection_message_callback")
        
        # Vérifier callbacks
        if hasattr(core_v2, 'on_message_ready'):
            print(f"  Callback on_message_ready: {core_v2.on_message_ready is not None}")
        
        if hasattr(core_v2, 'on_introspection_start'):
            print(f"  Callback on_introspection_start: {core_v2.on_introspection_start is not None}")
    else:
        print(f"  ⚠️ IntrospectionCore v2.0 non initialisé")
        
except ImportError as e:
    print(f"  ❌ IntrospectionCore v2.0 non disponible: {e}")

# 3. Vérifier alias compatibility
print("\n3️⃣ Alias compatibilité...")
try:
    from extensions.cognitive_mirror import get_cognitive_mirror
    
    alias = get_cognitive_mirror()
    
    if alias:
        print(f"  ✅ Alias get_cognitive_mirror() disponible")
        print(f"  Type: {type(alias)}")
        print(f"  Pointe vers: {'IntrospectionCore v2.0' if 'Introspection' in type(alias).__name__ else 'CognitiveMirrorCore v1.0'}")
    else:
        print(f"  ⚠️ Alias retourne None")
        
except ImportError as e:
    print(f"  ❌ Alias non disponible: {e}")

# 4. Vérifier workflows ogma_ng.py
print("\n4️⃣ Workflows détection ogma_ng.py...")

with open("ogma_ng.py", "r", encoding="utf-8") as f:
    content = f.read()
    
# Workflow 1: Phrase magique USER (ligne 3200-3350)
if "is_introspection_trigger" in content and "with ui.expansion().classes('thinking-expansion')" in content:
    print("  ✅ Workflow 1: Phrase magique USER détectée")
    print("     → Crée boîte expansion (ligne 3261)")
    print("     → Appelle trigger_introspection_sync() nouveau système")
else:
    print("  ❌ Workflow 1 non trouvé")

# Workflow 2: Messages IA via queue (ligne 770-870)
if "get_pending_messages()" in content:
    print("  ✅ Workflow 2: get_pending_messages() détecté")
    print("     → Récupère messages ancien système")
    print("     → Affiche expansion inline (ligne 847)")
else:
    print("  ❌ Workflow 2 non trouvé")

# Workflow 3: Callbacks v2.0
if "_on_introspection_message_callback" in content:
    print("  ✅ Workflow 3: Callbacks v2.0 détectés")
    print("     → _on_introspection_message_callback (ligne 922)")
    print("     → _on_message_ready (ligne 955)")
else:
    print("  ❌ Workflow 3 non trouvé")

# 5. Identifier conflit
print("\n5️⃣ Analyse conflit...")
print()
print("🔴 PROBLÈME IDENTIFIÉ:")
print("  - Workflow 1 (USER phrase magique): Crée boîte expansion ✅")
print("  - Workflow 2 (IA phrase magique ancien système): Utilise get_pending_messages() ❓")
print("  - Workflow 3 (IA phrase magique nouveau système): Utilise callbacks ❓")
print()
print("❌ CONFLIT:")
print("  Quand l'IA déclenche introspection via phrase magique dans SA réponse,")
print("  le système ne sait pas quel workflow utiliser.")
print()
print("  Workflow 1 ne se déclenche que si USER envoie phrase magique.")
print("  Donc boîte expansion (ligne 3261) jamais créée si IA déclenche.")
print()
print("✅ SOLUTION:")
print("  Créer la boîte expansion AUTOMATIQUEMENT quand introspection démarre,")
print("  quelle que soit la source (USER ou IA).")
print()
print("  Modifier _on_introspection_message_callback ou _on_message_ready")
print("  pour créer la boîte expansion si elle n'existe pas encore.")

print("\n" + "=" * 70)
print("FIN DIAGNOSTIC")
print("=" * 70)
