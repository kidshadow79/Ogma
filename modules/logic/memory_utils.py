import re
import asyncio
import threading

def caviarder_phrases_magiques_introspection(text: str) -> str:
    """
    Caviarde les phrases magiques d'introspection ET de mémorisation dans l'historique 
    pour éviter redéclenchement automatique lors de la réinjection de conversations passées.
    
    Args:
        text: Contenu du message historique
        
    Returns:
        Texte avec phrases magiques remplacées par "****"
    """
    if not text or not isinstance(text, str):
        return text
    
    # Patterns des phrases magiques d'introspection à caviarder
    patterns_introspection = [
        r"il\s+faut\s+que\s+je\s+réfléchisse",  # PHRASE PRIORITAIRE
        r"je\s+(?:vais|dois)\s+(?:lancer|déclencher|commencer|démarrer)\s+(?:une\s+)?introspection",
        r"j'ai\s+besoin\s+d'(?:une\s+)?introspection",
        r"je\s+sens\s+que\s+je\s+dois\s+réfléchir\s+en\s+profondeur",
        r"il\s+me\s+faut\s+(?:une\s+)?phase\s+(?:de\s+)?réflexion\s+intérieure",
        r"laisse[z]?\-moi\s+entrer\s+en\s+introspection",
        r"j'active\s+ma\s+subconscience",
        r"\[introspection\]",  # Tag explicite
        r"INTROSPECTION_TRIGGER"  # Commande cachée
    ]
    
    # Patterns des phrases magiques de mémorisation à caviarder
    patterns_memorisation = [
        r"il\s+faut\s+que\s+je\s+me\s+souvienne\s+de\s+ça\s*:\s*[^.!?\n]*",  # Pattern principal
        r"mémorise\s+ça\s*:\s*[^.!?\n]*",
        r"memorise\s+ca\s*:\s*[^.!?\n]*", 
        r"mémorises\s+ça\s*:\s*[^.!?\n]*",
        r"je\s+(?:vais|dois)\s+mémoriser\s+[^.!?\n]*",
        r"\[MEMORISATION\]",  # Tag explicite
        r"MEMORIZATION_TRIGGER"  # Commande cachée
    ]
    
    texte_caviarde = text
    phrases_caviardes = []
    
    # Caviarder les phrases magiques d'introspection
    for pattern in patterns_introspection:
        matches = list(re.finditer(pattern, texte_caviarde, re.IGNORECASE))
        if matches:
            for match in matches:
                phrase_originale = match.group(0)
                phrases_caviardes.append(('INTROSPECTION', phrase_originale))
                # Remplacer par des astérisques
                texte_caviarde = texte_caviarde.replace(phrase_originale, "****", 1)
    
    # Caviarder les phrases magiques de mémorisation
    for pattern in patterns_memorisation:
        matches = list(re.finditer(pattern, texte_caviarde, re.IGNORECASE))
        if matches:
            for match in matches:
                phrase_originale = match.group(0)
                phrases_caviardes.append(('MEMORISATION', phrase_originale))
                # Remplacer par des astérisques
                texte_caviarde = texte_caviarde.replace(phrase_originale, "****", 1)
    
    # Log si caviardage effectué
    if phrases_caviardes:
        print(f"[CAVIARDAGE] {len(phrases_caviardes)} phrase(s) magique(s) caviardée(s) dans l'historique")
        for type_phrase, phrase in phrases_caviardes:
            print(f"[CAVIARDAGE] {type_phrase} -> '{phrase[:50]}...' -> '****'")
    
    return texte_caviarde

def trigger_indexing_fn(memory_structure, embedding_controller, settings_manager):
    """Déclenche l'indexation des souvenirs en arrière-plan."""
    
    def run_indexing():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                memory_structure.index_existing_memories(embedding_controller, settings_manager)
            )
        finally:
            loop.close()
    
    # Lancer l'indexation dans un thread séparé
    thread = threading.Thread(target=run_indexing)
    thread.daemon = True
    thread.start()
