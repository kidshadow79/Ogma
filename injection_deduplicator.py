"""
Module de déduplication des injections pour OGMA
===============================================

Ce module implémente un système de déduplication intelligent pour éviter
les redondances dans les injections de contenu vers l'IA principale.

Problème résolu :
- Triple redondance des souvenirs ego (ego prompt + Archiviste + metacognitive)
- Waste potentiel de 3,500-4,500 tokens par requête
- Injections multiples du même contenu via 8 flux différents

Solution hybride :
- Pre-processeur Python (0 token, ~2ms, 100% précision)
- Instructions intelligentes à l'Archiviste
- Conservation de la flexibilité du système existant
"""

import re
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class InjectionContent:
    """Structure pour représenter le contenu injecté"""
    source: str  # ego_prompt, archiviste, metacognitive, etc.
    content_type: str  # ego_trait, memory, behavioral, etc.
    content_id: Optional[str]  # ID du souvenir si applicable
    content_text: str
    injection_timestamp: datetime
    token_count: int = 0

class InjectionDeduplicator:
    """
    Déduplicateur intelligent pour les injections OGMA
    
    Utilise des patterns regex pour identifier les contenus déjà injectés
    et génère des instructions précises pour l'Archiviste.
    """
    
    def __init__(self, enable_semantic_dedup: bool = False, conservative_mode: bool = True):
        self.injected_contents: List[InjectionContent] = []
        self.all_memory_ids: Set[str] = set()  # TOUS les IDs déjà injectés
        self.ego_memory_ids: Set[str] = set()  # Compatibilité ancien code
        self.content_hashes: Set[str] = set()
        
        # ✨ COOLDOWN SYSTEM - Option A (27 nov 2025)
        self.last_injection_message_count: Dict[str, int] = {}  # memory_id -> dernier message injecté
        self.current_message_count: int = 0  # Compteur messages dans conversation
        self.cooldown_threshold: int = 3  # Seuil cooldown: 3 messages (réduit le 7 fév 2026, était 20)
        
        # Configuration de sécurité - DÉSACTIVÉ par défaut pour éviter faux positifs
        self.enable_semantic_dedup = enable_semantic_dedup  # DÉSACTIVÉ: trop risqué
        self.conservative_mode = conservative_mode  # Mode prudent par défaut
        
        # Patterns regex pour identifier TOUS les types de souvenirs
        self.memory_id_patterns = [
            # === IDs EGO ===
            r"#MEM_EGO_(\w+)",  # Références directes ego: #MEM_EGO_123
            r"#(\w+)\s*\(ego_trait\)",  # Format Archiviste: #123 (ego_trait)
            r"ego\s+#?(\w+)",  # Trait ego #123 ou ego 123
            r"souvenirs?\s+ego\s+(\w+)",  # Mentions textuelles ego
            r"trait[s]?\s+(?:personnalité|identité)\s+#(\w+)",  # Trait personnalité #123
            r"traits\s+fondamentaux\s+(\w+)",  # Traits fondamentaux 456
            
            # === IDs UTILISATEUR ===
            r"(usr-[a-f0-9\-]+)",  # IDs utilisateur: usr-abc123-def
            r"souvenir\s+(usr-[a-f0-9\-]+)",  # Mentions explicites
            r"mémoire\s+(usr-[a-f0-9\-]+)",  # Synonymes
            
            # === IDs SYSTÈME ===
            r"(AUTO_CENSURE_\w+)",  # Souvenirs auto-censure
            r"#(\w+)\s*\([^)]+\)",  # Format générique #ID (type)
            r"ID[:\s]+([a-zA-Z0-9\-_]+)",  # ID explicite
            r"référence[:\s]+([a-zA-Z0-9\-_]+)",  # Références génériques
        ]
        
        # Patterns pour identifier les contenus similaires
        self.similarity_patterns = [
            r"Je suis (\w+)",  # Déclarations d'identité
            r"Mon (\w+) est",  # Attributs personnels
            r"J'ai tendance à",  # Patterns comportementaux
            r"Ma philosophie",  # Éléments philosophiques
        ]

    def reset_session(self):
        """Remet à zéro pour une nouvelle conversation"""
        self.injected_contents.clear()
        self.all_memory_ids.clear()
        self.ego_memory_ids.clear()
        self.content_hashes.clear()
        
        # ✨ Reset cooldown tracking
        self.last_injection_message_count.clear()
        self.current_message_count = 0
        
        logger.info("Session de déduplication réinitialisée (cooldown reset)")

    def register_injection(self, source: str, content: str, content_type: str = "unknown", 
                          content_id: Optional[str] = None) -> InjectionContent:
        """
        Enregistre une injection dans le système de tracking
        """
        injection = InjectionContent(
            source=source,
            content_type=content_type,
            content_id=content_id,
            content_text=content,
            injection_timestamp=datetime.now(),
            token_count=len(content.split()) * 1.3  # Estimation approximative
        )
        
        self.injected_contents.append(injection)
        
        # Extraire TOUS les IDs de souvenirs présents
        memory_ids_by_type = self.extract_all_memory_ids(content)
        all_ids = memory_ids_by_type['all']
        ego_ids = memory_ids_by_type['ego']
        
        # Mettre à jour les sets de tracking
        self.all_memory_ids.update(all_ids)
        self.ego_memory_ids.update(ego_ids)  # Compatibilité
        
        # Générer hash de contenu pour déduplication
        content_hash = self._generate_content_hash(content)
        self.content_hashes.add(content_hash)
        
        logger.debug(f"Injection enregistrée: {source} - {len(content)} chars - {len(ego_ids)} ego IDs")
        return injection

    def extract_all_memory_ids(self, content: str) -> Dict[str, Set[str]]:
        """
        Extrait TOUS les types d'IDs de souvenirs présents dans un contenu
        
        Returns:
            Dict avec clés: 'ego', 'user', 'system', 'all'
        """
        memory_ids = {
            'ego': set(),
            'user': set(), 
            'system': set(),
            'all': set()
        }
        
        for pattern in self.memory_id_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                memory_id = match.group(1)
                memory_ids['all'].add(memory_id)
                
                # Classifier par type
                if any(ego_indicator in pattern for ego_indicator in ['MEM_EGO', 'ego_trait', 'ego\\s', 'personnalité', 'fondamentaux']):
                    memory_ids['ego'].add(memory_id)
                elif 'usr-' in memory_id:
                    memory_ids['user'].add(memory_id)
                elif 'AUTO_CENSURE' in memory_id or memory_id.isupper():
                    memory_ids['system'].add(memory_id)
                    
        return memory_ids

    def extract_ego_memory_ids(self, content: str) -> Set[str]:
        """
        Compatibilité avec ancien code - extrait seulement les IDs ego
        """
        all_ids = self.extract_all_memory_ids(content)
        return all_ids['ego']

    def _generate_content_hash(self, content: str) -> str:
        """
        Génère un hash simplifié pour identifier les contenus très similaires
        
        SÉCURISÉ: Utilise plus de mots pour éviter les faux positifs
        sur les nuances sémantiques importantes
        """
        # Nettoyer le contenu pour la comparaison
        cleaned = re.sub(r'\s+', ' ', content.lower().strip())
        cleaned = re.sub(r'[^\w\s]', '', cleaned)
        
        # SÉCURITÉ: Prendre plus de mots pour capturer les nuances (15 au lieu de 10)
        words = cleaned.split()[:15]
        return ' '.join(words)

    def increment_message_count(self):
        """Incrémente le compteur de messages (appelé à chaque tour de conversation)"""
        self.current_message_count += 1
        logger.debug(f"Message count: {self.current_message_count}")
    
    def is_on_cooldown(self, memory_id: str) -> Tuple[bool, int]:
        """
        Vérifie si un souvenir est en cooldown (déjà injecté récemment)
        
        Args:
            memory_id: ID du souvenir à vérifier
            
        Returns:
            (is_on_cooldown: bool, messages_remaining: int)
        """
        if memory_id not in self.last_injection_message_count:
            return False, 0  # Jamais injecté
        
        last_injection = self.last_injection_message_count[memory_id]
        messages_since = self.current_message_count - last_injection
        
        if messages_since < self.cooldown_threshold:
            messages_remaining = self.cooldown_threshold - messages_since
            return True, messages_remaining
        
        return False, 0
    
    def register_memory_injection(self, memory_id: str):
        """Enregistre l'injection d'un souvenir à ce message-ci"""
        self.last_injection_message_count[memory_id] = self.current_message_count
        logger.debug(f"Souvenir {memory_id} injecté au message {self.current_message_count}")
    
    def filter_memories_by_cooldown(self, memories: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Filtre les souvenirs en cooldown
        
        ⚠️  IMPORTANT: Cette fonction NE fait QUE filtrer.
        L'enregistrement effectif doit être fait manuellement après usage
        via register_memory_injection() pour éviter enregistrement prématuré.
        
        Args:
            memories: Liste de souvenirs candidats
            
        Returns:
            (allowed_memories: List[Dict], blocked_memories: List[Dict])
        """
        allowed = []
        blocked = []
        
        for mem in memories:
            memory_id = mem.get('id') or mem.get('memory_id')
            if not memory_id:
                # Pas d'ID → autoriser (souvenirs système)
                allowed.append(mem)
                continue
            
            is_cooled, remaining = self.is_on_cooldown(memory_id)
            if is_cooled:
                mem['cooldown_remaining'] = remaining
                blocked.append(mem)
                logger.debug(f"🚫 Cooldown: {mem.get('title', 'N/A')[:40]} ({remaining} messages restants)")
            else:
                allowed.append(mem)
                # ✅ NE PAS enregistrer ici - sera fait après usage effectif
        
        return allowed, blocked

    def _is_truly_redundant(self, proposed_content: str, proposed_hash: str) -> bool:
        """
        Vérification fine pour éviter les faux positifs sémantiques
        
        Cherche des mots-clés qui indiquent des nuances importantes
        """
        # Mots qui indiquent des nuances critiques à ne pas manquer
        critical_nuances = [
            'superficiel', 'approfondi', 'détaillé', 'rapide', 'lent',
            'évite', 'privilégie', 'refuse', 'accepte', 'préfère',
            'jamais', 'toujours', 'parfois', 'rarement',
            'positif', 'négatif', 'neutre', 'critique',
            'mais', 'cependant', 'néanmoins', 'toutefois'
        ]
        
        # Chercher le contenu original avec le même hash
        for injection in self.injected_contents:
            if self._generate_content_hash(injection.content_text) == proposed_hash:
                original = injection.content_text.lower()
                proposed = proposed_content.lower()
                
                # Vérifier si des nuances critiques diffèrent
                for nuance in critical_nuances:
                    if (nuance in original) != (nuance in proposed):
                        print(f"[DEDUP-SAFE] 🛡️ Nuance critique détectée: '{nuance}' - Conservation du souvenir")
                        return False
                
                # Si aucune nuance critique, c'est vraiment redondant
                return True
        
        # Par défaut, ne pas considérer comme redondant si on ne trouve pas l'original
        return False

    def scan_for_redundancies(self, proposed_content: str, source: str) -> Tuple[bool, Dict]:
        """
        Scanne le contenu proposé pour identifier les redondances
        
        Returns:
            (has_redundancy: bool, analysis: Dict)
        """
        analysis = {
            'has_redundancy': False,
            'redundant_ego_ids': set(),
            'similar_content_sources': [],
            'estimated_token_waste': 0,
            'recommendations': []
        }
        
        # 1. Vérifier TOUS les types d'IDs redondants
        proposed_memory_ids = self.extract_all_memory_ids(proposed_content)
        all_proposed_ids = proposed_memory_ids['all']
        redundant_all_ids = all_proposed_ids.intersection(self.all_memory_ids)
        
        # Séparer par type pour rapport détaillé
        redundant_ego = proposed_memory_ids['ego'].intersection(self.ego_memory_ids)
        redundant_user = proposed_memory_ids['user'].intersection(self.all_memory_ids)
        redundant_system = proposed_memory_ids['system'].intersection(self.all_memory_ids)
        
        if redundant_all_ids:
            analysis['has_redundancy'] = True
            analysis['redundant_ego_ids'] = redundant_ego  # Compatibilité
            analysis['redundant_all_ids'] = redundant_all_ids
            analysis['redundant_by_type'] = {
                'ego': redundant_ego,
                'user': redundant_user, 
                'system': redundant_system
            }
            # Estimation tokens : ego=150, user=100, system=80
            analysis['estimated_token_waste'] += len(redundant_ego) * 150 + len(redundant_user) * 100 + len(redundant_system) * 80
            
        # 2. Vérifier la similarité de contenu (SI ACTIVÉ ET MODE CONSERVATEUR)
        if self.enable_semantic_dedup:
            proposed_hash = self._generate_content_hash(proposed_content)
            if proposed_hash in self.content_hashes:
                # SÉCURITÉ: Vérification supplémentaire pour éviter faux positifs
                if not self.conservative_mode or self._is_truly_redundant(proposed_content, proposed_hash):
                    analysis['has_redundancy'] = True
                    analysis['similar_content_sources'].append(source)
                    analysis['estimated_token_waste'] += len(proposed_content.split()) * 1.3
            
        # 3. Générer les recommandations par type
        if analysis['has_redundancy']:
            recommendations = []
            
            if redundant_ego:
                recommendations.append(f"Éviter souvenirs EGO: {', '.join(sorted(redundant_ego))}")
            if redundant_user:
                recommendations.append(f"Éviter souvenirs UTILISATEUR: {', '.join(sorted(list(redundant_user)[:3]))}")
            if redundant_system:
                recommendations.append(f"Éviter souvenirs SYSTÈME: {', '.join(sorted(list(redundant_system)[:3]))}")
            if analysis.get('similar_content_sources'):
                recommendations.append("Contenu sémantiquement similaire déjà présent")
                
            analysis['recommendations'] = recommendations
        
        return analysis['has_redundancy'], analysis

    def generate_exclusion_instruction(self, analysis: Dict) -> str:
        """
        Génère une instruction précise pour l'Archiviste basée sur l'analyse
        """
        if not analysis['has_redundancy']:
            return ""
            
        instructions = []
        
        # Instructions spécifiques par type de redondance
        redundant_by_type = analysis.get('redundant_by_type', {})
        
        if redundant_by_type.get('ego'):
            ego_list = ', '.join(sorted(redundant_by_type['ego']))
            instructions.append(
                f"⚠️ DÉDUPLICATION EGO: Éviter souvenirs #{ego_list} (déjà dans ego_prompt)"
            )
            
        if redundant_by_type.get('user'):
            user_list = ', '.join(sorted(list(redundant_by_type['user'])[:3]))  # Max 3 pour lisibilité
            instructions.append(
                f"⚠️ DÉDUPLICATION USER: Éviter {user_list} (déjà injectés)"
            )
            
        if redundant_by_type.get('system'):
            system_list = ', '.join(sorted(list(redundant_by_type['system'])[:3]))
            instructions.append(
                f"⚠️ DÉDUPLICATION SYSTEM: Éviter {system_list} (redondant)"
            )
        
        # Instructions pour éviter la duplication de contenu
        if analysis['similar_content_sources']:
            instructions.append(
                "⚠️ DÉDUPLICATION: Contenu similaire déjà présent. "
                "Chercher des souvenirs complémentaires plutôt que redondants."
            )
        
        # Estimation des tokens économisés
        if analysis['estimated_token_waste'] > 100:
            instructions.append(
                f"💡 Économie estimée: ~{int(analysis['estimated_token_waste'])} tokens"
            )
        
        return " | ".join(instructions)

    def get_session_stats(self) -> Dict:
        """
        Retourne les statistiques de la session courante
        """
        total_tokens = sum(inj.token_count for inj in self.injected_contents)
        sources = {}
        for inj in self.injected_contents:
            sources[inj.source] = sources.get(inj.source, 0) + 1
            
        return {
            'total_injections': len(self.injected_contents),
            'total_tokens_estimated': total_tokens,
            'unique_memory_ids': len(self.all_memory_ids),  # TOUS les IDs
            'unique_ego_ids': len(self.ego_memory_ids),     # Compatibilité
            'sources_breakdown': sources,
            'session_start': min((inj.injection_timestamp for inj in self.injected_contents), 
                               default=datetime.now())
        }

    def debug_print_state(self):
        """
        Affiche l'état actuel du déduplicateur pour debug
        """
        stats = self.get_session_stats()
        print("\n=== ÉTAT DÉDUPLICATEUR ===")
        print(f"Injections totales: {stats['total_injections']}")
        print(f"Tokens estimés: {stats['total_tokens_estimated']}")
        print(f"IDs ego uniques: {stats['unique_ego_ids']}")
        print(f"Sources: {stats['sources_breakdown']}")
        if self.ego_memory_ids:
            print(f"IDs ego trackés: {sorted(self.ego_memory_ids)}")
        print("=" * 30)


# Instance globale pour OGMA (Seulement IDs ego pour éviter faux positifs)
deduplicator = InjectionDeduplicator(enable_semantic_dedup=False, conservative_mode=True)

def reset_deduplication_session():
    """Fonction utilitaire pour réinitialiser la session"""
    deduplicator.reset_session()

def register_ego_prompt_injection(ego_content: str):
    """Enregistre l'injection du ego prompt"""
    deduplicator.register_injection("ego_prompt", ego_content, "ego_system")

def check_archiviste_injection(proposed_memories: str) -> Tuple[bool, str]:
    """
    Vérifie si l'injection de l'Archiviste créerait des redondances
    
    Returns:
        (should_modify: bool, exclusion_instruction: str)
    """
    has_redundancy, analysis = deduplicator.scan_for_redundancies(proposed_memories, "archiviste")
    exclusion_instruction = deduplicator.generate_exclusion_instruction(analysis) if has_redundancy else ""
    
    return has_redundancy, exclusion_instruction

def register_archiviste_injection(memories_content: str):
    """Enregistre l'injection effective de l'Archiviste"""
    deduplicator.register_injection("archiviste", memories_content, "detailed_memories")

def increment_message_count():
    """Incrémente le compteur de messages (appelé à chaque message utilisateur)"""
    deduplicator.increment_message_count()

def filter_memories_by_cooldown(memories: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """Filtre les souvenirs en cooldown"""
    return deduplicator.filter_memories_by_cooldown(memories)

def get_deduplication_stats() -> Dict:
    """Retourne les statistiques courantes"""
    stats = deduplicator.get_session_stats()
    stats['cooldown'] = {
        'current_message': deduplicator.current_message_count,
        'cooldown_threshold': deduplicator.cooldown_threshold,
        'memories_tracked': len(deduplicator.last_injection_message_count)
    }
    return stats