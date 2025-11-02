"""
Prompt Enhancer pour génération d'images NSFW haute qualité
===========================================================
Enrichit les prompts simples de Luna en descriptions ultra-détaillées
pour obtenir une qualité similaire à Perchance.org avec Pollinations.AI
"""

import re
from typing import Dict, List, Set


class PromptEnhancer:
    """
    Enrichit les prompts pour génération d'images NSFW haute qualité
    
    Stratégie:
    1. Détecte mots-clés anatomiques/descriptifs dans le prompt simple
    2. Expanse chaque mot-clé en description détaillée
    3. Ajoute automatiquement des qualifiers techniques de qualité
    4. Assemble un prompt ultra-détaillé optimisé pour Pollinations
    """
    
    # Dictionnaire d'expansion anatomique et descriptive
    ANATOMY_EXPANSIONS: Dict[str, str] = {
        # Corps et anatomie féminine
        "femme": "beautiful woman, feminine features, graceful posture, elegant presence",
        "woman": "beautiful woman, feminine features, graceful posture, elegant presence",
        "latina": "latina woman, caramel skin tone, exotic beauty, warm complexion",
        "nue": "nude, natural body, authentic nudity, unclothed",
        "naked": "nude, natural body, authentic nudity, unclothed",
        "voluptueuse": "voluptuous curves, full figure, curvaceous body, generous proportions",
        "seins": "natural breasts, realistic chest anatomy, detailed bust",
        "breasts": "natural breasts, realistic chest anatomy, detailed bust",
        "hanches": "wide hips, curved hips, feminine hip structure",
        "hips": "wide hips, curved hips, feminine hip structure",
        "fesses": "round buttocks, shapely posterior, curved backside",
        "buttocks": "round buttocks, shapely posterior, curved backside",
        "jambes": "long legs, shapely legs, toned limbs",
        "legs": "long legs, shapely legs, toned limbs",
        "cheveux": "flowing hair, lustrous hair, detailed hair strands",
        "hair": "flowing hair, lustrous hair, detailed hair strands",
        
        # Expressions et poses
        "sensuel": "sensual expression, seductive look, alluring presence",
        "sensual": "sensual expression, seductive look, alluring presence",
        "séductrice": "seductive pose, alluring stance, confident attitude",
        "seductive": "seductive pose, alluring stance, confident attitude",
        "confiant": "confident pose, self-assured posture, empowered stance",
        "confident": "confident pose, self-assured posture, empowered stance",
        "sourire": "gentle smile, soft smile, warm expression",
        "smile": "gentle smile, soft smile, warm expression",
        
        # Éclairage et ambiance
        "lumière": "professional lighting, soft shadows, balanced exposure",
        "lighting": "professional lighting, soft shadows, balanced exposure",
        "tamisée": "dim lighting, ambient glow, subdued illumination",
        "dim": "dim lighting, ambient glow, subdued illumination",
        "douce": "soft lighting, gentle illumination, diffused light",
        "soft": "soft lighting, gentle illumination, diffused light",
        
        # Lieux et contextes
        "chambre": "bedroom setting, intimate interior, private space",
        "bedroom": "bedroom setting, intimate interior, private space",
        "lit": "bed, sheets, bedding details",
        "bed": "bed, sheets, bedding details",
        "douche": "shower setting, water droplets, wet skin",
        "shower": "shower setting, water droplets, wet skin",
    }
    
    # Qualifiers techniques de qualité (ajoutés systématiquement)
    QUALITY_BOOSTS: List[str] = [
        "highly detailed",
        "photorealistic",
        "8k uhd resolution",
        "sharp focus",
        "professional photography",
        "studio quality lighting",
        "cinematic composition",
        "masterpiece quality",
        "perfect anatomy",
        "natural skin texture",
        "realistic details",
        "high definition",
        "crisp image",
        "professional color grading"
    ]
    
    # Boosts spécifiques NSFW pour réalisme
    NSFW_QUALITY_BOOSTS: List[str] = [
        "anatomically correct",
        "natural proportions",
        "realistic body",
        "authentic human anatomy",
        "detailed skin pores",
        "natural skin imperfections",
        "subtle muscle definition",
        "realistic lighting on skin"
    ]
    
    # Patterns à détecter pour activation NSFW boosts
    NSFW_KEYWORDS: Set[str] = {
        "nue", "nude", "naked", "seins", "breasts", "fesses", "buttocks",
        "corps", "body", "anatomie", "anatomy", "voluptueuse", "sensuel"
    }
    
    def __init__(self, debug: bool = False):
        """
        Initialise le prompt enhancer
        
        Args:
            debug: Active les logs de debug
        """
        self.debug = debug
        self._compiled_patterns = self._compile_patterns()
        
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile les patterns regex pour détection rapide"""
        patterns = {}
        for keyword in self.ANATOMY_EXPANSIONS.keys():
            # Pattern word boundary pour éviter matches partiels
            patterns[keyword] = re.compile(
                r'\b' + re.escape(keyword) + r'\b',
                re.IGNORECASE
            )
        return patterns
    
    def enhance(
        self,
        prompt: str,
        quality_boosts: str = "",
        nsfw_boosts: str = "",
        custom_boosts: str = ""
    ) -> str:
        """
        Enrichit un prompt simple en prompt ultra-détaillé
        
        Args:
            prompt: Prompt original simple de Luna
            quality_boosts: String CSV des quality boosts (ou utilise QUALITY_BOOSTS par défaut)
            nsfw_boosts: String CSV des NSFW boosts (ou utilise NSFW_QUALITY_BOOSTS par défaut)
            custom_boosts: Boosts personnalisés additionnels (string CSV)
            
        Returns:
            str: Prompt enrichi avec expansions et qualifiers
        """
        if self.debug:
            print(f"[PROMPT-ENHANCER] 📝 Prompt original: '{prompt}'")
        
        # Liste des expansions détectées
        expansions = []
        detected_keywords = []
        
        # 1. Détecter et expanser les mots-clés anatomiques
        for keyword, pattern in self._compiled_patterns.items():
            if pattern.search(prompt):
                expansion = self.ANATOMY_EXPANSIONS[keyword]
                expansions.append(expansion)
                detected_keywords.append(keyword)
                
                if self.debug:
                    print(f"[PROMPT-ENHANCER] 🔍 Détecté '{keyword}' → '{expansion}'")
        
        # 2. Construire le prompt enrichi
        parts = [prompt]  # Commencer avec le prompt original
        
        # Ajouter les expansions anatomiques
        if expansions:
            parts.extend(expansions)
        
        # 3. Ajouter les quality boosts (depuis settings ou défaut)
        if quality_boosts:
            # Utiliser les boosts depuis settings (CSV string)
            quality_list = [b.strip() for b in quality_boosts.split(',') if b.strip()]
            parts.extend(quality_list)
            if self.debug:
                print(f"[PROMPT-ENHANCER] 📊 {len(quality_list)} quality boosts (custom)")
        else:
            # Utiliser les boosts par défaut hardcodés
            parts.extend(self.QUALITY_BOOSTS)
            if self.debug:
                print(f"[PROMPT-ENHANCER] 📊 {len(self.QUALITY_BOOSTS)} quality boosts (défaut)")
        
        # 4. Ajouter les boosts NSFW si pertinent
        if self._is_nsfw_content(prompt, detected_keywords):
            if nsfw_boosts:
                # Utiliser les boosts NSFW depuis settings (CSV string)
                nsfw_list = [b.strip() for b in nsfw_boosts.split(',') if b.strip()]
                parts.extend(nsfw_list)
                if self.debug:
                    print(f"[PROMPT-ENHANCER] 🔞 {len(nsfw_list)} NSFW boosts (custom)")
            else:
                # Utiliser les boosts NSFW par défaut hardcodés
                parts.extend(self.NSFW_QUALITY_BOOSTS)
                if self.debug:
                    print(f"[PROMPT-ENHANCER] 🔞 {len(self.NSFW_QUALITY_BOOSTS)} NSFW boosts (défaut)")
        
        # 5. Ajouter les boosts personnalisés additionnels
        if custom_boosts:
            # Parser les boosts personnalisés (CSV)
            custom_list = [b.strip() for b in custom_boosts.split(',') if b.strip()]
            
            if custom_list:
                parts.extend(custom_list)
                if self.debug:
                    print(f"[PROMPT-ENHANCER] ✨ {len(custom_list)} boosts custom additionnels")
        
        # 6. Assembler le prompt final
        enhanced_prompt = ", ".join(parts)
        
        if self.debug:
            print(f"[PROMPT-ENHANCER] ✅ Prompt enrichi ({len(enhanced_prompt)} chars)")
            print(f"[PROMPT-ENHANCER] 📊 {len(detected_keywords)} mots-clés, {len(expansions)} expansions")
        
        return enhanced_prompt
    
    def _is_nsfw_content(self, prompt: str, detected_keywords: List[str]) -> bool:
        """
        Détermine si le prompt contient du contenu NSFW
        
        Args:
            prompt: Prompt original
            detected_keywords: Mots-clés détectés
            
        Returns:
            bool: True si contenu NSFW détecté
        """
        prompt_lower = prompt.lower()
        
        # Check dans le prompt original
        if any(keyword in prompt_lower for keyword in self.NSFW_KEYWORDS):
            return True
        
        # Check dans les keywords détectés
        if any(keyword.lower() in self.NSFW_KEYWORDS for keyword in detected_keywords):
            return True
        
        return False
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Retourne des statistiques sur l'enhancer
        
        Returns:
            dict: Statistiques (keywords disponibles, boosts, etc.)
        """
        return {
            "anatomy_keywords": len(self.ANATOMY_EXPANSIONS),
            "quality_boosts": len(self.QUALITY_BOOSTS),
            "nsfw_boosts": len(self.NSFW_QUALITY_BOOSTS),
            "total_keywords": len(self._compiled_patterns)
        }


# Instance globale pour réutilisation
_prompt_enhancer: PromptEnhancer = None


def get_enhancer(debug: bool = False) -> PromptEnhancer:
    """
    Récupère l'instance globale du prompt enhancer (singleton)
    
    Args:
        debug: Active les logs de debug
        
    Returns:
        PromptEnhancer: Instance du prompt enhancer
    """
    global _prompt_enhancer
    
    if _prompt_enhancer is None:
        _prompt_enhancer = PromptEnhancer(debug=debug)
        print(f"[PROMPT-ENHANCER] ✅ Enhancer initialisé")
        stats = _prompt_enhancer.get_statistics()
        print(f"[PROMPT-ENHANCER] 📊 {stats['anatomy_keywords']} mots-clés, "
              f"{stats['quality_boosts']} boosts qualité, "
              f"{stats['nsfw_boosts']} boosts NSFW")
    
    return _prompt_enhancer
