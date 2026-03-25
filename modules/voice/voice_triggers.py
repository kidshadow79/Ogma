"""
modules/voice/voice_triggers.py
===============================
Détecteur de mots déclencheurs pour le système vocal OGMA

Gère la détection des triggers :
- trigger_activation : "Pour l'IA" -> Active l'écoute / Interrompt TTS
- trigger_send : "Point Final" -> Envoie le message

Auteur: Yohan BROCARD
Date: Janvier 2026
"""

import re
from typing import List, Tuple


class TriggerDetector:
    """
    Détecteur de mots déclencheurs vocaux.
    
    Gère les variantes phonétiques et les erreurs de transcription
    courantes pour une détection robuste.
    """
    
    def __init__(
        self,
        trigger_activation: str = "pour l'ia",
        trigger_send: str = "point final"
    ):
        """
        Initialise le détecteur.
        
        Args:
            trigger_activation: Mot pour activer l'écoute / interrompre TTS
            trigger_send: Mot pour envoyer le message
        """
        self.trigger_activation = trigger_activation.lower().strip()
        self.trigger_send = trigger_send.lower().strip()
        
        print(f"[TRIGGERS] 📋 Activation: '{self.trigger_activation}', Envoi: '{self.trigger_send}'")
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalise le texte pour la comparaison.
        Retire ponctuation et normalise les espaces.
        """
        # Minuscules
        text = text.lower()
        
        # Retirer ponctuation sauf espaces
        text = re.sub(r'[^\w\s]', '', text)
        
        # Normaliser espaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _get_activation_variants(self) -> List[str]:
        """
        Retourne les variantes du trigger d'activation.
        Génère des variantes génériques pour N'IMPORTE QUEL trigger configuré.
        AUCUN trigger hardcodé - tout est basé sur la config utilisateur.
        """
        variants = [self._normalize_text(self.trigger_activation)]
        
        base = self.trigger_activation.lower().strip()
        
        # === VARIANTES GÉNÉRIQUES UNIVERSELLES ===
        
        # Version sans espace (ex: "ma louna" → "malouna")
        if " " in base:
            variants.append(base.replace(" ", ""))
        
        # Version avec tiret (ex: "ma louna" → "ma-louna")
        if " " in base:
            variants.append(base.replace(" ", "-"))
        
        # Version avec apostrophe si commence par "ma/mon/ta/ton" (ex: "ma louna" → "m'a louna")
        if base.startswith(("ma ", "mon ", "ta ", "ton ")):
            variants.append(base.replace("ma ", "m'a ").replace("mon ", "m'on ").replace("ta ", "t'a ").replace("ton ", "t'on "))
        
        # Répétition si un seul mot (ex: "ia" → "ia ia")
        parts = base.split()
        if len(parts) == 1:
            variants.append(f"{base} {base}")
            variants.append(f"{base}{base}")
        
        # Première partie seule si multi-mots (ex: "hey ia" → "hey")
        if len(parts) >= 2:
            variants.append(parts[0])
        
        # Normaliser toutes les variantes
        return list(set(self._normalize_text(v) for v in variants if v))
    
    def _get_send_variants(self) -> List[str]:
        """
        Retourne les variantes du trigger d'envoi.
        TOUT trigger configuré fonctionne automatiquement avec variantes génériques.
        """
        variants = [self._normalize_text(self.trigger_send)]
        
        base = self.trigger_send.lower().strip()
        
        # === VARIANTES GÉNÉRIQUES (pour TOUS les triggers) ===
        
        # Version sans espace
        if " " in base:
            variants.append(base.replace(" ", ""))
        
        # Version avec tiret (ex: "go go" → "go-go")
        if " " in base:
            variants.append(base.replace(" ", "-"))
        
        # Première partie seule si multi-mots (ex: "go go" → "go")
        parts = base.split()
        if len(parts) >= 2:
            variants.append(parts[0])
        
        # Répétition si un seul mot court (ex: "go" → "go go")
        if len(parts) == 1 and len(base) <= 4:
            variants.append(f"{base} {base}")
            variants.append(f"{base}{base}")
            variants.append(f"{base} {base} {base}")
            variants.append(f"{base}{base}{base}")
        
        # Formes verbales courantes si finit en 'er' (infinitif français)
        if base.endswith("er"):
            root = base[:-2]
            variants.extend([
                f"{root}e",      # 1ère pers singulier (ex: "valider" → "valide")
                f"{root}é",      # participe passé (ex: "valider" → "validé")
                f"{root}ez",     # 2ème pers pluriel (ex: "valider" → "validez")
            ])
        
        return list(set(self._normalize_text(v) for v in variants if v))
    
    def check_activation(self, text: str) -> bool:
        """
        Vérifie si le texte contient le trigger d'activation.
        
        Args:
            text: Texte transcrit à vérifier
            
        Returns:
            True si le trigger est détecté
        """
        normalized = self._normalize_text(text)
        variants = self._get_activation_variants()
        
        # DEBUG: Afficher les variantes au premier appel
        if not hasattr(self, '_variants_logged'):
            print(f"[TRIGGERS-DEBUG] 🔍 Variantes pour '{self.trigger_activation}': {', '.join(variants[:10])}...")
            self._variants_logged = True
        
        for variant in variants:
            if variant in normalized:
                print(f"[TRIGGERS] 🎯 Activation détectée: '{variant}' dans '{text[:50]}'")
                return True
        
        return False
    
    def check_send(self, text: str) -> bool:
        """
        Vérifie si le texte contient le trigger d'envoi.
        
        Args:
            text: Texte transcrit à vérifier
            
        Returns:
            True si le trigger est détecté
        """
        normalized = self._normalize_text(text)
        variants = self._get_send_variants()
        
        # DEBUG: Afficher les variantes au premier appel
        if not hasattr(self, '_send_variants_logged'):
            print(f"[TRIGGERS-DEBUG] 📤 Variantes ENVOI pour '{self.trigger_send}': {', '.join(variants[:10])}...")
            self._send_variants_logged = True
        
        for variant in variants:
            if variant in normalized:
                print(f"[TRIGGERS] 🚀 Envoi détecté: '{variant}' dans '{text[:50]}'")
                return True
        
        return False
    
    def remove_activation_trigger(self, text: str) -> str:
        """
        Retire le trigger d'activation du texte.
        
        Args:
            text: Texte à nettoyer
            
        Returns:
            Texte sans le trigger
        """
        result = text
        variants = self._get_activation_variants()
        
        for variant in variants:
            # Pattern insensible à la casse
            pattern = re.compile(re.escape(variant), re.IGNORECASE)
            result = pattern.sub('', result)
        
        # Nettoyer espaces multiples
        result = re.sub(r'\s+', ' ', result).strip()
        
        return result
    
    def remove_send_trigger(self, text: str) -> str:
        """
        Retire le trigger d'envoi du texte et le remplace par
        une ponctuation appropriée.
        
        Args:
            text: Texte à nettoyer
            
        Returns:
            Texte nettoyé avec ponctuation finale
        """
        result = text
        variants = self._get_send_variants()
        
        # Patterns pour "point final" -> remplacer par "."
        point_patterns = [
            r'\s*[,.]?\s*point\s*final\s*[!.]*\s*$',
            r'\s*[,.]?\s*point\s*final\s*[!.]*',
            r'\s*[,.]?\s*pointfinal\s*[!.]*',
            r'\s*[,.]?\s*pointe?\s*finaux?\s*[!.]*',
        ]
        
        for pattern in point_patterns:
            if re.search(pattern, result, flags=re.IGNORECASE):
                result = re.sub(pattern, '.', result, flags=re.IGNORECASE)
                break
        
        # Retirer les autres triggers
        other_patterns = [
            r'\bfin\s*du\s*message\b[!.]*',
            r'\btermine[rz]?\b[!.]*',
            r'\bterminé\b[!.]*',
            r'\bgo\s*go\s*go\b[!.]*',
            r'\bgogogo\b[!.]*',
            r'\bgogo\b[!.]*',
            r'\benvoie?\b[!.]*\s*$',
            r'\benvois\b[!.]*\s*$',
            r'\bfini\b[!.]*\s*$',
        ]
        
        for pattern in other_patterns:
            result = re.sub(pattern, '', result, flags=re.IGNORECASE)
        
        # Nettoyer
        result = re.sub(r'\.+', '.', result)  # Points multiples
        result = re.sub(r'\s+', ' ', result).strip()
        
        # Assurer ponctuation finale
        if result and result[-1] not in '.!?':
            result += '.'
        
        return result
    
    def update_triggers(
        self,
        trigger_activation: str = None,
        trigger_send: str = None
    ):
        """
        Met à jour les triggers (après changement dans settings).
        
        Args:
            trigger_activation: Nouveau trigger d'activation
            trigger_send: Nouveau trigger d'envoi
        """
        if trigger_activation:
            self.trigger_activation = trigger_activation.lower().strip()
        if trigger_send:
            self.trigger_send = trigger_send.lower().strip()
        
        print(f"[TRIGGERS] 🔄 Mise à jour: activation='{self.trigger_activation}', envoi='{self.trigger_send}'")
