"""
⏰ TEMPORAL PARSER - Analyse expressions temporelles
===================================================

Détecte et convertit expressions temporelles relatives en dates absolues.

PATTERNS DÉTECTÉS:
- "il y a 2 jours" → 2025-10-30
- "la semaine dernière" → plage 2025-10-21 à 2025-10-27
- "hier" → 2025-10-31
- "quand on a parlé de X" → trigger recherche
- "notre conversation sur Y" → trigger recherche

LOGIQUE:
1. Scan regex patterns temporels
2. Conversion relatif → absolu
3. Retour métadonnées (date_start, date_end, confidence)
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class TemporalMatch:
    """Résultat parsing temporel."""
    pattern_type: str          # Type pattern détecté
    date_start: datetime       # Date début plage
    date_end: datetime         # Date fin plage
    confidence: float          # Confiance détection (0.0-1.0)
    original_text: str         # Texte original matchant
    is_period: bool            # True si plage, False si date unique


class TemporalParser:
    """Parser d'expressions temporelles dans requêtes utilisateur."""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        
        # Patterns temporels avec groupes de capture
        self.patterns = {
            # Phrase magique IA
            'ia_magic_phrase': [
                r'il\s+faut\s+que\s+je\s+consulte\s+notre\s+conversation\s+de\s+(.+?)(?:\.|$|,|\n)',
                r'je\s+dois\s+consulter\s+notre\s+conversation\s+de\s+(.+?)(?:\.|$|,|\n)',
                r'il\s+faut\s+que\s+je\s+consulte\s+mes\s+conversations?\s*(?:avec\s+(\w+))?',  # mes conversations (avec Bob)
                r'je\s+dois\s+consulter\s+mes\s+conversations?\s*(?:avec\s+(\w+))?',
                r'il\s+faut\s+que\s+je\s+consulte\s+(?:la|les)\s+conversations?\s*(?:avec\s+(\w+))?',
            ],
            # Relatif jours
            'relative_days': [
                r'il y a (\d+) jours?',
                r'(\d+) jours? avant',
                r'y a (\d+) jours?',
            ],
            # Relatif semaines
            'relative_weeks': [
                r'il y a (\d+) semaines?',
                r'(\d+) semaines? avant',
                r'y a (\d+) semaines?',
            ],
            # Relatif mois
            'relative_months': [
                r'il y a (\d+) mois',
                r'(\d+) mois avant',
                r'le mois dernier',
            ],
            # Absolus simples
            'absolute_simple': [
                r'\bhier\b',
                r'avant-?hier',
                r'aujourd\'?hui',
            ],
            # Périodes nommées
            'named_periods': [
                r'la semaine derni[èe]re',
                r'cette semaine',
                r'le week-?end dernier',
                r'la semaine pass[ée]e',
            ],
            # Triggers généraux mémoire
            'memory_triggers': [
                r'(tu )?(te )?(souviens|rappelles)( de | du | quand)',
                r'(qu\'?est-?ce qu\'?|ce qu\'?)(on|nous) (a|avait) (dit|parl[ée]|discut[ée])',
                r'(rappelle-?moi|redis-?moi) (ce que|la|notre)',
                r'(notre|la|cette) (conversation|discussion|[ée]change) (sur|[àa] propos|du|de)',
                r'quand (on a|tu as|nous avons|j\'?ai) (parl[ée]|discut[ée]|[ée]voqu[ée])',
            ]
        }
        
    def parse(self, text: str) -> List[TemporalMatch]:
        """
        Analyse texte et extrait références temporelles.
        
        Args:
            text: Texte utilisateur
            
        Returns:
            Liste TemporalMatch trouvés
        """
        matches = []
        now = datetime.now()
        
        if self.debug:
            print(f"[TEMPORAL-PARSER] 🔍 Analyse: '{text}'")
        
        # Scanner chaque catégorie de patterns
        for category, pattern_list in self.patterns.items():
            for pattern in pattern_list:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    temporal_match = self._convert_to_temporal(
                        category, match, now
                    )
                    if temporal_match:
                        matches.append(temporal_match)
                        if self.debug:
                            print(f"[TEMPORAL-PARSER] ✅ Match: {temporal_match.pattern_type} → {temporal_match.date_start.date()}")
        
        # Dédupliquer et trier par confiance
        matches = self._deduplicate_matches(matches)
        matches.sort(key=lambda m: m.confidence, reverse=True)
        
        return matches
    
    def _convert_to_temporal(
        self, 
        category: str, 
        match: re.Match, 
        now: datetime
    ) -> Optional[TemporalMatch]:
        """Convertit match regex en TemporalMatch."""
        
        text = match.group(0)
        
        # PHRASE MAGIQUE IA - "il faut que je consulte notre conversation de..."
        if category == 'ia_magic_phrase':
            # Extraire la référence temporelle après "de" (groupe 1)
            # OU le nom de la personne après "avec" (groupe 1 aussi selon le pattern)
            try:
                temporal_ref = match.group(1) if match.group(1) else ""
                temporal_ref = temporal_ref.strip().lower()
            except (IndexError, AttributeError):
                # Pas de groupe capturé (cas "mes conversations" sans précision)
                temporal_ref = ""
            
            if self.debug:
                print(f"[TEMPORAL-PARSER] 🔮 Phrase magique IA détectée: '{temporal_ref}' (from: '{text}')")
            
            # Si on a une référence temporelle ou un nom, essayer de parser
            if temporal_ref:
                # Parser la référence temporelle (hier, la semaine dernière, etc.)
                # OU utiliser le nom comme contexte de recherche
                sub_matches = self.parse(temporal_ref)
                if sub_matches:
                    # Utiliser le premier match de la sous-analyse
                    sub_match = sub_matches[0]
                    return TemporalMatch(
                        pattern_type='ia_magic_phrase',
                        date_start=sub_match.date_start,
                        date_end=sub_match.date_end,
                        confidence=0.95,  # Haute confiance car phrase magique explicite
                        original_text=text,
                        is_period=sub_match.is_period
                    )
            
            # Fallback: dernière semaine si pas de pattern reconnu
            return TemporalMatch(
                pattern_type='ia_magic_phrase_fallback',
                date_start=(now - timedelta(days=7)).replace(hour=0, minute=0, second=0),
                date_end=now,
                confidence=0.7,
                original_text=text,
                is_period=True
            )
        
        # RELATIF JOURS
        if category == 'relative_days':
            days = int(match.group(1))
            date_target = now - timedelta(days=days)
            return TemporalMatch(
                pattern_type='relative_days',
                date_start=date_target.replace(hour=0, minute=0, second=0),
                date_end=date_target.replace(hour=23, minute=59, second=59),
                confidence=0.9,
                original_text=text,
                is_period=False
            )
        
        # RELATIF SEMAINES
        elif category == 'relative_weeks':
            weeks = int(match.group(1)) if match.group(1).isdigit() else 1
            date_end = now - timedelta(weeks=weeks)
            date_start = date_end - timedelta(days=6)
            return TemporalMatch(
                pattern_type='relative_weeks',
                date_start=date_start.replace(hour=0, minute=0, second=0),
                date_end=date_end.replace(hour=23, minute=59, second=59),
                confidence=0.85,
                original_text=text,
                is_period=True
            )
        
        # RELATIF MOIS
        elif category == 'relative_months':
            if 'mois dernier' in text.lower():
                months = 1
            else:
                months = int(match.group(1))
            
            # Approximation: 1 mois = 30 jours
            date_end = now - timedelta(days=30 * months)
            date_start = date_end - timedelta(days=29)
            return TemporalMatch(
                pattern_type='relative_months',
                date_start=date_start.replace(hour=0, minute=0, second=0),
                date_end=date_end.replace(hour=23, minute=59, second=59),
                confidence=0.75,
                original_text=text,
                is_period=True
            )
        
        # ABSOLUS SIMPLES
        elif category == 'absolute_simple':
            if 'hier' in text.lower():
                offset = 2 if 'avant' in text.lower() else 1
                date_target = now - timedelta(days=offset)
            else:  # aujourd'hui
                date_target = now
            
            return TemporalMatch(
                pattern_type='absolute_simple',
                date_start=date_target.replace(hour=0, minute=0, second=0),
                date_end=date_target.replace(hour=23, minute=59, second=59),
                confidence=0.95,
                original_text=text,
                is_period=False
            )
        
        # PÉRIODES NOMMÉES
        elif category == 'named_periods':
            if 'semaine dernière' in text.lower() or 'semaine passée' in text.lower():
                # Semaine dernière = lundi à dimanche précédent
                days_since_monday = now.weekday()
                last_monday = now - timedelta(days=days_since_monday + 7)
                last_sunday = last_monday + timedelta(days=6)
                
                return TemporalMatch(
                    pattern_type='named_week',
                    date_start=last_monday.replace(hour=0, minute=0, second=0),
                    date_end=last_sunday.replace(hour=23, minute=59, second=59),
                    confidence=0.85,
                    original_text=text,
                    is_period=True
                )
            elif 'cette semaine' in text.lower():
                days_since_monday = now.weekday()
                this_monday = now - timedelta(days=days_since_monday)
                
                return TemporalMatch(
                    pattern_type='current_week',
                    date_start=this_monday.replace(hour=0, minute=0, second=0),
                    date_end=now,
                    confidence=0.9,
                    original_text=text,
                    is_period=True
                )
        
        # TRIGGERS MÉMOIRE (pas de date précise, juste détection)
        elif category == 'memory_triggers':
            # Retour plage large (7 derniers jours par défaut)
            return TemporalMatch(
                pattern_type='memory_trigger',
                date_start=(now - timedelta(days=7)).replace(hour=0, minute=0, second=0),
                date_end=now,
                confidence=0.6,  # Plus basse car vague
                original_text=text,
                is_period=True
            )
        
        return None
    
    def _deduplicate_matches(self, matches: List[TemporalMatch]) -> List[TemporalMatch]:
        """Élimine doublons (même plage temporelle)."""
        unique = []
        seen_ranges = set()
        
        for match in matches:
            range_key = (
                match.date_start.date(),
                match.date_end.date(),
                match.pattern_type
            )
            if range_key not in seen_ranges:
                unique.append(match)
                seen_ranges.add(range_key)
        
        return unique
    
    def has_temporal_reference(self, text: str) -> bool:
        """Vérifie rapidement si texte contient référence temporelle."""
        matches = self.parse(text)
        return len(matches) > 0
    
    def get_best_match(self, text: str) -> Optional[TemporalMatch]:
        """Retourne le meilleur match (confidence la plus haute)."""
        matches = self.parse(text)
        return matches[0] if matches else None
