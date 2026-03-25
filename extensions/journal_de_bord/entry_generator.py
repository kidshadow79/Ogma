# JOURNAL Extension Journal de Bord - Générateur d'Entrées

"""
Générateur de résumés et entrées via l'Archiviste OGMA
Intégration IA, extraction de métadonnées, génération intelligente
"""

import time
import uuid
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional, Union
import re
import asyncio

class EntryGenerator:
    """
    Générateur de résumés et entrées via l'Archiviste
    
    Responsabilités:
    - Génération de résumés de conversation (200-400 tokens)
    - Extraction automatique de tags et métadonnées
    - Évaluation de l'importance des conversations
    - Intégration avec l'AIController Archiviste
    - Formatage des entrées selon le schéma JSON
    
    Performance:
    - Génération résumé: <3s (avec Archiviste)
    - Extraction tags: <100ms
    - Validation entrée: <50ms
    """
    
    def __init__(self, archiviste_controller, config):
        """Initialise le générateur avec l'Archiviste"""
        self.archiviste = archiviste_controller
        self.config = config
        
        # Paramètres de génération
        self.generation_settings = self.config.get_generation_settings()
        self.min_tokens = self.generation_settings["min_tokens"]
        self.max_tokens = self.generation_settings["max_tokens"]
        self.style = self.generation_settings["style"]
        self.auto_tags = self.generation_settings["auto_tags"]
        self.importance_detection = self.generation_settings["importance_detection"]
        
        # Templates de prompts selon le style
        self.prompt_templates = {
            "formal": self._get_formal_prompt_template(),
            "casual": self._get_casual_prompt_template(),
            "technical": self._get_technical_prompt_template(),
            "balanced": self._get_balanced_prompt_template()
        }
        
        # Patterns pour extraction métadonnées
        self.tag_patterns = [
            r"(?:tags?|sujets?|thèmes?)\s*:?\s*(.+)",
            r"(?:mots-clés?|keywords?)\s*:?\s*(.+)",
            r"#(\w+)",  # hashtags
        ]
        
        self.importance_keywords = {
            "critical": ["urgent", "critique", "important", "vital", "essentiel", "décisif"],
            "high": ["significatif", "notable", "remarquable", "intéressant", "pertinent"],
            "normal": ["normal", "standard", "habituel", "ordinaire"],
            "low": ["mineur", "anecdotique", "trivial", "sans importance"]
        }
        
        # Statistiques
        self.stats = {
            "total_generated": 0,
            "avg_generation_time": 0.0,
            "avg_tokens": 0,
            "success_rate": 1.0,
            "errors": 0
        }
        
        print(f"[ENTRY-GENERATOR] OK Initialisé (style: {self.style}, tokens: {self.min_tokens}-{self.max_tokens})")
    
    async def generate_entry(self, conversation_id: str = None, **metadata) -> Optional[Dict[str, Any]]:
        """
        Génère une entrée complète de journal via l'Archiviste
        
        Args:
            conversation_id: ID de la conversation à résumer
            **metadata: Métadonnées additionnelles (title, participants, etc.)
        
        Returns:
            Dict: Entrée formatée selon le schéma ou None si échec
        """
        try:
            start_time = time.time()
            
            print(f"[ENTRY-GENERATOR] 🤖 Génération entrée (conv: {conversation_id})")
            
            # Préparation du contexte de conversation
            conversation_context = await self._get_conversation_context(conversation_id, metadata)
            if not conversation_context:
                raise ValueError("Impossible de récupérer le contexte de conversation")
            
            # Génération du prompt selon le style configuré
            prompt = self._build_generation_prompt(conversation_context, metadata)
            
            # Appel à l'Archiviste pour génération
            summary_response = await self._call_archiviste(prompt)
            if not summary_response:
                raise RuntimeError("Archiviste n'a pas retourné de résumé")
            
            print(f"[ENTRY-GENERATOR] DEBUG Réponse Archiviste: {len(summary_response)} chars")
            
            # Parsing et nettoyage de la réponse
            parsed_response = self._parse_archiviste_response(summary_response)
            
            print(f"[ENTRY-GENERATOR] DEBUG Summary après parsing: {len(parsed_response['summary'])} chars")
            
            # Validation longueur
            token_count = self._estimate_tokens(parsed_response["summary"])
            if token_count < self.min_tokens or token_count > self.max_tokens:
                print(f"[ENTRY-GENERATOR] WARN Tokens hors limite: {token_count} (attendu: {self.min_tokens}-{self.max_tokens})")
                # Pas d'erreur bloquante, on garde le résumé
            
            # Construction de l'entrée finale
            entry_data = self._build_entry_data(
                parsed_response, 
                conversation_context, 
                metadata,
                token_count,
                conversation_id  # 🔧 FIX: Passer conversation_id explicitement
            )
            
            # Mise à jour statistiques
            generation_time = time.time() - start_time
            self._update_stats(generation_time, token_count, success=True)
            
            print(f"[ENTRY-GENERATOR] OK Entrée générée en {generation_time:.3f}s ({token_count} tokens)")
            
            return entry_data
            
        except Exception as e:
            print(f"[ENTRY-GENERATOR] ERREUR Erreur génération: {e}")
            self._update_stats(0, 0, success=False)
            return None
    
    def extract_tags_from_text(self, text: str) -> List[str]:
        """
        Extraction automatique de tags depuis un texte
        
        Args:
            text: Texte source pour extraction
        
        Returns:
            List[str]: Liste de tags extraits
        """
        if not self.auto_tags:
            return []
        
        try:
            tags = set()
            text_lower = text.lower()
            
            # 🔧 FIX: Extraction intelligente par mots-clés thématiques
            keyword_categories = {
                # Contexte personnel/relationnel
                "relationnel": ["amour", "affection", "tendresse", "intimité", "connexion", "émotionnel"],
                "soutien": ["encouragement", "motivation", "réconfort", "support", "aide"],
                
                # Contexte professionnel/apprentissage  
                "professionnel": ["travail", "emploi", "carrière", "projet", "réunion"],
                "apprentissage": ["étude", "examen", "formation", "cours", "apprentissage", "diplôme"],
                
                # Contexte technique
                "technique": ["développement", "code", "programmation", "architecture", "api"],
                "debug": ["bug", "erreur", "problème", "correction", "fix"],
                "performance": ["optimisation", "performance", "vitesse", "efficacité"],
                
                # Contexte créatif
                "créatif": ["design", "créativité", "artistique", "innovation"],
                "ui_ux": ["interface", "expérience", "ergonomie", "design"],
                
                # États/moments
                "bien-être": ["détente", "relaxation", "repos", "calme", "sérénité"],
                "stress": ["stress", "pression", "anxiété", "tension", "préoccupation"]
            }
            
            # Détection par catégories
            for category, keywords in keyword_categories.items():
                for keyword in keywords:
                    if keyword in text_lower:
                        tags.add(category)
                        break  # Une seule fois par catégorie
            
            # Extraction de mots-clés spécifiques importants
            # Chercher des noms propres, termes techniques, etc.
            important_words = re.findall(r'\b[A-ZÀ-Ÿ][a-zà-ÿ]{2,15}\b', text)  # Mots capitalisés
            for word in important_words[:5]:  # Max 5
                if word.lower() not in ["cette", "dans", "pour", "avec", "sans"]:
                    tags.add(word.lower())
            
            # Limitation nombre de tags
            return list(tags)[:10]
            
        except Exception as e:
            print(f"[ENTRY-GENERATOR] WARN Erreur extraction tags: {e}")
            return []
    
    def assess_importance(self, summary: str, metadata: Dict[str, Any] = None) -> str:
        """
        Évalue l'importance d'une conversation
        
        Args:
            summary: Résumé de la conversation
            metadata: Métadonnées additionnelles
        
        Returns:
            str: Niveau d'importance ("low", "normal", "high", "critical")
        """
        if not self.importance_detection:
            return "normal"
        
        try:
            summary_lower = summary.lower()
            scores = {"critical": 0, "high": 0, "normal": 0, "low": 0}
            
            # Scoring par mots-clés
            for importance, keywords in self.importance_keywords.items():
                for keyword in keywords:
                    if keyword in summary_lower:
                        scores[importance] += 1
            
            # Bonus selon longueur (conversations longues = plus importantes)
            if len(summary) > 1000:
                scores["high"] += 2
            elif len(summary) > 500:
                scores["high"] += 1
            
            # Bonus selon métadonnées
            if metadata:
                # Nombre de participants
                participant_count = len(metadata.get("participants", []))
                if participant_count > 2:
                    scores["high"] += 1
                
                # Durée de conversation (si disponible)
                if "duration_minutes" in metadata and metadata["duration_minutes"] > 30:
                    scores["high"] += 1
            
            # Patterns spéciaux critiques
            critical_patterns = [
                r"erreur critique", r"bug majeur", r"problème urgent",
                r"échec système", r"corruption données", r"sécurité compromise"
            ]
            
            for pattern in critical_patterns:
                if re.search(pattern, summary_lower):
                    scores["critical"] += 3
            
            # Patterns importance élevée
            high_patterns = [
                r"nouvelle fonctionnalité", r"amélioration importante",
                r"décision technique", r"architecture", r"refactoring majeur"
            ]
            
            for pattern in high_patterns:
                if re.search(pattern, summary_lower):
                    scores["high"] += 2
            
            # Retourne le niveau avec le score le plus élevé
            max_importance = max(scores.keys(), key=lambda k: scores[k])
            
            # Seuil minimum pour éviter sur-classification
            if scores[max_importance] == 0:
                return "normal"
            
            return max_importance
            
        except Exception as e:
            print(f"[ENTRY-GENERATOR] WARN Erreur évaluation importance: {e}")
            return "normal"
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de génération"""
        return self.stats.copy()
    
    # === MÉTHODES PRIVÉES ===
    
    async def _get_conversation_context(self, conversation_id: str, metadata: Dict[str, Any] = None) -> Optional[str]:
        """Récupère le contexte de conversation depuis OGMA"""
        try:
            # 🔧 FIX: Utiliser l'historique réel passé dans les métadonnées
            if metadata and "conversation_history" in metadata:
                conversation_history = metadata["conversation_history"]
                print(f"[ENTRY-GENERATOR] ✅ Historique réel récupéré: {len(conversation_history)} messages")
                
                # Formater l'historique en texte pour l'Archiviste
                context_parts = [f"Conversation ID: {conversation_id or 'current'}"]
                context_parts.append(f"Timestamp: {datetime.now().isoformat()}")
                context_parts.append(f"Nombre de messages: {len(conversation_history)}\n")
                
                # Convertir les messages en texte lisible
                for i, msg in enumerate(conversation_history, 1):
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                    
                    # Nettoyer le contenu (enlever balises système si présentes)
                    if content:
                        context_parts.append(f"\n[Message {i} - {role.upper()}]:")
                        context_parts.append(content[:2000])  # Limiter à 2000 chars par message
                
                context = "\n".join(context_parts)
                print(f"[ENTRY-GENERATOR] ✅ Contexte formaté: {len(context)} chars")
                return context.strip()
            
            # ❌ Fallback: Si pas d'historique fourni, logger l'erreur
            print(f"[ENTRY-GENERATOR] ❌ ERREUR: Aucun historique de conversation fourni dans les métadonnées")
            print(f"[ENTRY-GENERATOR] ❌ Métadonnées reçues: {list(metadata.keys()) if metadata else 'None'}")
            
            # Ne plus retourner de placeholder - retourner None pour forcer l'erreur
            return None
            
        except Exception as e:
            print(f"[ENTRY-GENERATOR] ERREUR Erreur récupération contexte: {e}")
            return None
    
    def _build_generation_prompt(self, conversation_context: str, metadata: Dict[str, Any]) -> str:
        """Construit le prompt de génération selon le style"""
        template = self.prompt_templates.get(self.style, self.prompt_templates["balanced"])
        
        # Variables de template
        variables = {
            "context": conversation_context,
            "min_tokens": self.min_tokens,
            "max_tokens": self.max_tokens,
            "participant_count": len(metadata.get("participants", [])),
            "conversation_title": metadata.get("title", "Conversation"),
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        return template.format(**variables)
    
    async def _call_archiviste(self, prompt: str) -> Optional[str]:
        """Appelle l'Archiviste pour génération"""
        try:
            # Utilisation de l'AIController Archiviste
            response, error = await self.archiviste.call_chat_api(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_tokens + 100,  # Marge pour métadonnées
                context_length=self.archiviste.context_length,
                temperature=0.7
            )
            
            if response and not error:
                return response
            elif error:
                print(f"[ENTRY-GENERATOR] WARN Erreur Archiviste: {error}")
            else:
                print("[ENTRY-GENERATOR] WARN Réponse Archiviste vide")
            return None
            
        except Exception as e:
            print(f"[ENTRY-GENERATOR] ERREUR Erreur appel Archiviste: {e}")
            return None
    
    def _parse_archiviste_response(self, response: str) -> Dict[str, Any]:
        """Parse la réponse de l'Archiviste"""
        try:
            # Nettoyage de base
            response = response.strip()
            
            # 🔧 FIX: Nettoyer les résidus JSON de l'Archiviste
            # Parfois l'Archiviste retourne du JSON brut qu'on doit parser
            if response.startswith('{"') or response.startswith('{'):
                try:
                    # Tenter de parser comme JSON
                    import json
                    json_data = json.loads(response)
                    # Extraire le champ summary si présent
                    if isinstance(json_data, dict) and "summary" in json_data:
                        response = json_data["summary"]
                        print("[ENTRY-GENERATOR] FIX JSON detecté et extrait du champ 'summary'")
                    else:
                        # Prendre tout le JSON comme texte
                        response = json.dumps(json_data, ensure_ascii=False)
                except json.JSONDecodeError:
                    # Pas du JSON valide, continuer avec le texte brut
                    pass
            
            # 🔧 FIX: Nettoyer les guillemets résiduels au début
            # Pattern: ": "Texte commence ici...
            if response.startswith('": "') or response.startswith('":'):
                response = response.lstrip('":').strip()
                print("[ENTRY-GENERATOR] FIX Guillemets résiduels supprimés")
            
            # Tentative d'extraction de sections structurées
            parsed = {
                "summary": response,
                "extracted_tags": [],
                "mood": "neutral",
                "key_points": []
            }
            
            # Recherche de sections spéciales dans la réponse
            sections = {
                "résumé": r"(?:résumé|summary)\s*:?\s*(.+?)(?=(?:\n(?:tags?|mots-clés?|humeur|mood|points clés?))|$)",
                "tags": r"(?:tags?|mots-clés?)\s*:?\s*(.+?)(?:\n|$)",  # Capture jusqu'à fin de ligne
                "humeur": r"(?:humeur|mood|ton)\s*:?\s*(.+?)(?:\n|$)",
                "points": r"(?:points clés?|key points?)\s*:?\s*(.+?)(?=(?:\n(?:résumé|tags?|mots-clés?|humeur|mood))|$)"
            }
            
            # Tentative d'extraction structurée - si aucune section trouvée, garder tout le texte
            sections_found = False
            
            for section, pattern in sections.items():
                match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
                if match:
                    content = match.group(1).strip()
                    sections_found = True
                    
                    if section == "résumé" and content:
                        parsed["summary"] = content
                    elif section == "tags" and content:
                        # 🔧 FIX: Nettoyage strict des tags
                        # Séparer par virgules, point-virgules
                        raw_tags = re.split(r'[,;]+', content)
                        clean_tags = []
                        for tag in raw_tags:
                            tag = tag.strip()
                            # Enlever les guillemets, parenthèses, etc.
                            tag = tag.strip('"\'()[]{}')
                            # Ignorer les tags trop longs (probablement du texte)
                            if tag and 2 <= len(tag) <= 30 and not tag.endswith('.'):
                                clean_tags.append(tag)
                        parsed["extracted_tags"] = clean_tags[:10]  # Limite 10 tags max
                    elif section == "humeur" and content:
                        parsed["mood"] = content.lower()
                    elif section == "points" and content:
                        parsed["key_points"] = [point.strip() for point in content.split('\n') if point.strip()]
            
            # Si aucune section structurée n'est trouvée, garder tout le texte comme résumé
            if not sections_found:
                print("[ENTRY-GENERATOR] DEBUG Aucune section structurée trouvée, utilisation du texte complet")
                parsed["summary"] = response
            
            return parsed
            
        except Exception as e:
            print(f"[ENTRY-GENERATOR] WARN Erreur parsing réponse: {e}")
            return {"summary": response, "extracted_tags": [], "mood": "neutral", "key_points": []}
    
    def _build_entry_data(self, parsed_response: Dict[str, Any], 
                         conversation_context: str, metadata: Dict[str, Any],
                         token_count: int, conversation_id: str = None) -> Dict[str, Any]:
        """Construit l'entrée finale selon le schéma"""
        
        # ID unique pour l'entrée
        timestamp = datetime.now()
        entry_id = f"entry_{timestamp.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        
        # Tags combinés
        summary_tags = self.extract_tags_from_text(parsed_response["summary"])
        extracted_tags = parsed_response.get("extracted_tags", [])
        metadata_tags = metadata.get("tags", [])
        
        all_tags = list(set(summary_tags + extracted_tags + metadata_tags))
        
        # Évaluation importance
        importance = self.assess_importance(parsed_response["summary"], metadata)
        
        # Construction entrée finale
        entry_data = {
            # Identifiants
            "id": entry_id,
            "timestamp": timestamp.isoformat() + "Z",
            
            # Contenu principal
            "summary": parsed_response["summary"],
            "tokens": token_count,
            
            # Métadonnées conversation
            "conversation_id": conversation_id or metadata.get("conversation_id", "unknown"),  # 🔧 FIX: Utiliser conversation_id passé en paramètre
            "conversation_title": metadata.get("title", "Conversation sans titre"),
            "participants": metadata.get("participants", ["utilisateur", "assistant"]),
            
            # Génération
            "generated_by": "archiviste",
            "generation_model": getattr(self.archiviste, 'current_model', 'unknown'),
            "generation_prompt": "Résumé automatique via Archiviste OGMA",
            "generation_duration": self.stats.get("last_generation_time", 0),
            
            # Classification
            "tags": all_tags[:10],  # Limite à 10 tags
            "importance": importance,
            "mood": parsed_response.get("mood", "neutral"),
            "category": self._determine_category(all_tags, parsed_response["summary"]),
            
            # Contexte
            "context_keywords": self._extract_keywords(parsed_response["summary"]),
            "related_memories": [],  # TODO: Intégration avec MemoryManager
            "related_entries": [],   # TODO: Recherche d'entrées similaires
            
            # Techniques
            "word_count": len(parsed_response["summary"].split()),
            "reading_time_seconds": max(1, len(parsed_response["summary"]) // 5),  # ~300 mots/min
            "confidence_score": self._calculate_confidence_score(parsed_response)
        }
        
        return entry_data
    
    def _determine_category(self, tags: List[str], summary: str) -> str:
        """Détermine la catégorie principale de l'entrée"""
        category_keywords = {
            "technique": ["développement", "code", "bug", "architecture", "api"],
            "créatif": ["design", "ui", "ux", "créativité", "art"],
            "personnel": ["réflexion", "personnel", "introspection", "humeur"],
            "professionnel": ["travail", "projet", "réunion", "stratégie"],
            "apprentissage": ["formation", "tutorial", "apprentissage", "documentation"],
            "général": []
        }
        
        summary_lower = summary.lower()
        category_scores = {}
        
        for category, keywords in category_keywords.items():
            score = 0
            
            # Score par mots-clés dans les tags
            for tag in tags:
                if tag.lower() in keywords:
                    score += 2
            
            # Score par mots-clés dans le résumé
            for keyword in keywords:
                if keyword in summary_lower:
                    score += 1
            
            category_scores[category] = score
        
        # Retourne la catégorie avec le score le plus élevé
        best_category = max(category_scores.keys(), key=lambda k: category_scores[k])
        
        # Fallback sur "général" si aucun score
        if category_scores[best_category] == 0:
            return "général"
        
        return best_category
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extrait les mots-clés importants du texte"""
        # Mots vides à ignorer
        stop_words = {
            "le", "la", "les", "de", "du", "des", "un", "une", "et", "ou", "mais", "donc",
            "car", "ni", "si", "que", "qui", "quoi", "dont", "où", "comment", "pourquoi",
            "est", "sont", "était", "étaient", "sera", "seront", "avoir", "être",
            "dans", "sur", "avec", "par", "pour", "sans", "sous", "vers", "chez"
        }
        
        # Extraction mots significatifs
        words = re.findall(r'\b[a-zA-ZÀ-ÿ]+\b', text.lower())
        keywords = [word for word in words 
                   if len(word) > 3 and word not in stop_words]
        
        # Compte des occurrences
        word_counts = {}
        for word in keywords:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # Top mots par fréquence
        top_keywords = sorted(word_counts.keys(), 
                            key=lambda w: word_counts[w], 
                            reverse=True)
        
        return top_keywords[:10]
    
    def _calculate_confidence_score(self, parsed_response: Dict[str, Any]) -> float:
        """Calcule un score de confiance pour l'entrée générée"""
        score = 1.0
        
        # Pénalité si résumé trop court
        summary_length = len(parsed_response["summary"])
        if summary_length < 100:
            score -= 0.3
        elif summary_length < 200:
            score -= 0.1
        
        # Bonus si métadonnées extraites
        if parsed_response.get("extracted_tags"):
            score += 0.1
        
        if parsed_response.get("key_points"):
            score += 0.1
        
        # Maintenir entre 0 et 1
        return max(0.0, min(1.0, score))
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimation approximative du nombre de tokens"""
        # Estimation grossière: ~0.75 tokens par mot pour le français
        word_count = len(text.split())
        return int(word_count * 0.75)
    
    def _update_stats(self, generation_time: float, token_count: int, success: bool):
        """Met à jour les statistiques de génération"""
        if success:
            self.stats["total_generated"] += 1
            
            # Moyenne mobile du temps de génération
            if self.stats["avg_generation_time"] == 0:
                self.stats["avg_generation_time"] = generation_time
            else:
                self.stats["avg_generation_time"] = (
                    self.stats["avg_generation_time"] * 0.9 + generation_time * 0.1
                )
            
            # Moyenne mobile des tokens
            if self.stats["avg_tokens"] == 0:
                self.stats["avg_tokens"] = token_count
            else:
                self.stats["avg_tokens"] = (
                    self.stats["avg_tokens"] * 0.9 + token_count * 0.1
                )
            
            self.stats["last_generation_time"] = generation_time
        else:
            self.stats["errors"] += 1
        
        # Taux de succès
        total_attempts = self.stats["total_generated"] + self.stats["errors"]
        self.stats["success_rate"] = self.stats["total_generated"] / max(1, total_attempts)
    
    # === TEMPLATES DE PROMPTS ===
    
    def _get_balanced_prompt_template(self) -> str:
        """Template équilibré (par défaut)"""
        return """Tu es l'Archiviste d'OGMA, spécialisé dans la création de résumés conversationnels pour le Journal de Bord.

Contexte de conversation:
{context}

Instructions:
1. Crée un résumé de {min_tokens} à {max_tokens} tokens qui capture l'essence de cette conversation
2. Identifie les points clés, les décisions prises, et les informations importantes
3. Utilise un ton naturel et informatif
4. Si possible, suggère des tags pertinents à la fin

Le résumé doit être utile pour remettre en contexte cette conversation lors de futures sessions.

Résumé:"""

    def _get_formal_prompt_template(self) -> str:
        """Template formel pour contextes professionnels"""
        return """En tant qu'Archiviste d'OGMA, vous êtes chargé de documenter cette conversation pour le Journal de Bord professionnel.

Contexte:
{context}

Consignes:
- Rédigez un compte-rendu structuré de {min_tokens} à {max_tokens} tokens
- Identifiez les objectifs, décisions, et actions à retenir
- Adoptez un style professionnel et factuel
- Mettez en évidence les éléments stratégiques ou techniques importants

Format attendu: Compte-rendu structuré avec points clés et conclusions.

Compte-rendu:"""

    def _get_casual_prompt_template(self) -> str:
        """Template décontracté pour conversations informelles"""
        return """Salut ! Tu es l'Archiviste qui aide à garder une trace des conversations cool dans le Journal de Bord.

Ce qui s'est dit:
{context}

Ce que j'attends:
- Un résumé sympa de {min_tokens} à {max_tokens} tokens de cette discussion
- Garde le côté décontracté et personnel
- Note les trucs intéressants ou amusants qui se sont passés
- N'hésite pas à mettre ta touche personnelle

Écris ça comme si tu racontais à un pote ce qui s'est passé !

Résumé:"""

    def _get_technical_prompt_template(self) -> str:
        """Template technique pour discussions spécialisées"""
        return """Archiviste OGMA - Mode Analyse Technique

Données de session:
{context}

Objectifs d'analyse:
1. Synthèse technique de {min_tokens} à {max_tokens} tokens
2. Identification des concepts, technologies, et méthodologies abordées
3. Documentation des problèmes techniques et solutions proposées
4. Extraction des patterns architecturaux et décisions de design

Focus: Précision technique, terminologie appropriée, traçabilité des solutions.

Analyse technique:"""

    async def handle_magic_phrases(self, user_input: str, json_manager=None) -> Optional[str]:
        """
        Détecte et traite les phrases magiques de consultation journal

        Args:
            user_input: Texte de l'utilisateur
            json_manager: Instance JSONManager pour accès aux données

        Returns:
            str: Réponse à la phrase magique ou None si pas détectée
        """
        try:
            if not user_input or not json_manager:
                return None

            user_lower = user_input.lower().strip()
            print(f"[ENTRY-GENERATOR] SEARCH Analyse phrase magique: '{user_input[:50]}...'")

            # Patterns de phrases magiques
            patterns = {
                # Consultation journal par date
                r"consulte le journal du (\d{4}-\d{2}-\d{2})": self._get_journal_entries,
                r"consulte le journal de la (\w+)": self._get_weekly_summary_by_period,  # Nouveau: "de la semaine"
                r"consulte le journal d[''`]?(hier|aujourd'hui|aujourdhui|avant-hier|avanthier|lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)": self._get_journal_relative_date,

                # Contexte formaté
                r"montre.*contexte.*d[''`]?(\w+)": self._get_formatted_context_relative,
                r"montre.*contexte.*(\d{4}-\d{2}-\d{2})": self._get_formatted_context,

                # Recherche
                r"journal.*recherche (.+)": self._search_journal,
                r"recherche.*journal.*[:\-] ?(.+)": self._search_journal,

                # Résumés temporels
                r"résume.*semaine.*(\d{4}-\d{2}-\d{2})": self._get_weekly_summary,
                r"résume.*mois.*(\d{4}-\d{2})": self._get_monthly_summary,

                # Interface utilisateur
                r"ouvre.*journal.*d[''`]?(\w+)": self._open_journal_ui_date,
                r"journal.*affiche (.+)": self._display_filtered_entries,

                # Création d'entrée
                r"sauvegarde.*conversation.*journal": self._create_entry_manual,
                r"ajoute.*au.*journal": self._create_entry_manual,
            }

            # Tester chaque pattern
            for pattern, handler in patterns.items():
                match = re.search(pattern, user_lower)
                if match:
                    print(f"[ENTRY-GENERATOR] OK Phrase magique détectée: {pattern}")
                    groups = match.groups() if match.groups() else []
                    result = await handler(json_manager, groups, user_input)
                    if result:
                        return result

            return None

        except Exception as e:
            print(f"[ENTRY-GENERATOR] ERREUR Erreur traitement phrase magique: {e}")
            return None

    async def _get_journal_entries(self, json_manager, groups: list, original_input: str) -> str:
        """Récupère les entrées d'une date spécifique"""
        try:
            date_str = groups[0] if groups else None
            if not date_str:
                return "ERREUR Date non spécifiée"

            print(f"[ENTRY-GENERATOR] DATE Consultation journal: {date_str}")

            entries = json_manager.get_day_entries(date_str)
            if not entries:
                return f"JOURNAL **Journal du {date_str}**\n\nAucune entrée trouvée pour cette date."

            # Formatage des entrées
            response = f"JOURNAL **Journal du {date_str}** ({len(entries)} entrée(s))\n\n"

            for i, entry in enumerate(entries, 1):
                timestamp = entry.get("timestamp", "")
                time_str = ""
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        time_str = dt.strftime("%H:%M")
                    except:
                        pass

                importance = entry.get("importance", "normal")
                importance_emoji = {"critical": "[CRITICAL]", "high": "[HIGH]", "normal": "[NORMAL]", "low": "[LOW]"}.get(importance, "[NORMAL]")

                summary = entry.get("summary", "Aucun résumé")
                tags = entry.get("tags", [])
                tags_str = " ".join([f"`{tag}`" for tag in tags[:3]])

                response += f"**{i}.** {importance_emoji} **{time_str}** {tags_str}\n"
                response += f"   {summary[:200]}{'...' if len(summary) > 200 else ''}\n\n"

            return response

        except Exception as e:
            print(f"[ENTRY-GENERATOR] ERREUR Erreur get_journal_entries: {e}")
            return f"ERREUR Erreur consultation journal: {e}"

    async def _get_journal_relative_date(self, json_manager, groups: list, original_input: str) -> str:
        """Récupère les entrées d'une date relative (hier, aujourd'hui)"""
        try:
            relative_date = groups[0] if groups else ""

            # Conversion date relative -> date absolue
            today = date.today()

            if relative_date in ["aujourd'hui", "aujourdhui"]:
                target_date = today
            elif relative_date in ["hier"]:
                target_date = today - timedelta(days=1)
            elif relative_date in ["avant-hier", "avanthier"]:
                target_date = today - timedelta(days=2)
            else:
                return f"ERREUR Date relative non reconnue: {relative_date}"

            date_str = target_date.strftime("%Y-%m-%d")
            return await self._get_journal_entries(json_manager, [date_str], original_input)

        except Exception as e:
            print(f"[ENTRY-GENERATOR] ERREUR Erreur date relative: {e}")
            return f"ERREUR Erreur date relative: {e}"

    async def _get_formatted_context(self, json_manager, groups: list, original_input: str) -> str:
        """Retourne le contexte formaté pour une date"""
        try:
            date_str = groups[0] if groups else None
            if not date_str:
                return "ERREUR Date non spécifiée"

            # Utiliser le context_provider pour formatage
            from .context_provider import ContextProvider
            from .config import get_journal_config

            config = get_journal_config()
            context_provider = ContextProvider(json_manager, config)

            context = await context_provider.get_context_for_date(date_str)

            if context:
                return f"JOURNAL **Contexte du {date_str}**\n\n{context}"
            else:
                return f"JOURNAL **Contexte du {date_str}**\n\nAucun contexte disponible pour cette date."

        except Exception as e:
            print(f"[ENTRY-GENERATOR] ERREUR Erreur contexte formaté: {e}")
            return f"ERREUR Erreur récupération contexte: {e}"

    async def _get_formatted_context_relative(self, json_manager, groups: list, original_input: str) -> str:
        """Retourne le contexte formaté pour une date relative"""
        try:
            relative_date = groups[0] if groups else ""

            # Conversion date relative -> date absolue
            today = date.today()

            if relative_date in ["aujourd'hui", "aujourdhui"]:
                target_date = today
            elif relative_date in ["hier"]:
                target_date = today - timedelta(days=1)
            else:
                return f"ERREUR Date relative non reconnue: {relative_date}"

            date_str = target_date.strftime("%Y-%m-%d")
            return await self._get_formatted_context(json_manager, [date_str], original_input)

        except Exception as e:
            print(f"[ENTRY-GENERATOR] ERREUR Erreur contexte relatif: {e}")
            return f"ERREUR Erreur contexte relatif: {e}"

    async def _search_journal(self, json_manager, groups: list, original_input: str) -> str:
        """Effectue une recherche dans le journal"""
        try:
            query = groups[0].strip() if groups else ""
            if not query:
                return "ERREUR Terme de recherche manquant"

            print(f"[ENTRY-GENERATOR] SEARCH Recherche journal: '{query}'")

            # Recherche via json_manager
            results = json_manager.search_entries(query=query)

            if not results:
                return f"SEARCH **Recherche: '{query}'**\n\nAucun résultat trouvé."

            # Formatage des résultats
            response = f"SEARCH **Recherche: '{query}'** ({len(results)} résultat(s))\n\n"

            for i, entry in enumerate(results[:5], 1):  # Max 5 résultats
                date_str = entry.get("timestamp", "")[:10]  # YYYY-MM-DD
                importance = entry.get("importance", "normal")
                importance_emoji = {"critical": "[CRITICAL]", "high": "[HIGH]", "normal": "[NORMAL]", "low": "[LOW]"}.get(importance, "[NORMAL]")

                summary = entry.get("summary", "")
                tags = entry.get("tags", [])
                tags_str = " ".join([f"`{tag}`" for tag in tags[:2]])

                response += f"**{i}.** {importance_emoji} **{date_str}** {tags_str}\n"
                response += f"   {summary[:150]}{'...' if len(summary) > 150 else ''}\n\n"

            if len(results) > 5:
                response += f"*... et {len(results) - 5} autres résultats*"

            return response

        except Exception as e:
            print(f"[ENTRY-GENERATOR] ERREUR Erreur recherche: {e}")
            return f"ERREUR Erreur recherche: {e}"

    async def _get_weekly_summary_by_period(self, json_manager, groups: list, original_input: str) -> str:
        """Génère un résumé de période (semaine, mois)"""
        try:
            period = groups[0] if groups else ""
            
            if period == "semaine":
                # Semaine courante
                today = date.today()
                week_start = today - timedelta(days=today.weekday())  # Lundi
                return await self._get_weekly_summary(json_manager, [week_start.strftime("%Y-%m-%d")], original_input)
            elif period == "mois":
                # Mois courant
                today = date.today()
                month_str = today.strftime("%Y-%m")
                return await self._get_monthly_summary(json_manager, [month_str], original_input)
            else:
                return f"ERREUR Période non reconnue: {period}. Utilisez 'semaine' ou 'mois'."

        except Exception as e:
            print(f"[ENTRY-GENERATOR] ERREUR Erreur résumé période: {e}")
            return f"ERREUR Erreur résumé période: {e}"

    async def _get_weekly_summary(self, json_manager, groups: list, original_input: str) -> str:
        """Génère un résumé hebdomadaire"""
        try:
            date_str = groups[0] if groups else None
            if not date_str:
                return "ERREUR Date non spécifiée"

            # Calcul semaine (lundi au dimanche)
            week_start = datetime.strptime(date_str, "%Y-%m-%d").date()
            week_start = week_start - timedelta(days=week_start.weekday())  # Lundi
            week_end = week_start + timedelta(days=6)  # Dimanche

            print(f"[ENTRY-GENERATOR] DATE Résumé semaine: {week_start} à {week_end}")

            # Collecte des entrées de la semaine
            week_entries = []
            current_date = week_start

            while current_date <= week_end:
                date_key = current_date.strftime("%Y-%m-%d")
                day_entries = json_manager.get_day_entries(date_key)
                if day_entries:
                    week_entries.extend(day_entries)
                current_date += timedelta(days=1)

            if not week_entries:
                return f"DATE **Semaine du {week_start.strftime('%d/%m')} au {week_end.strftime('%d/%m/%Y')}**\n\nAucune activité cette semaine."

            # Analyse des entrées
            total_entries = len(week_entries)
            days_active = len(set(entry.get("timestamp", "")[:10] for entry in week_entries))

            importance_counts = {"critical": 0, "high": 0, "normal": 0, "low": 0}
            all_tags = []

            for entry in week_entries:
                importance = entry.get("importance", "normal")
                importance_counts[importance] += 1
                all_tags.extend(entry.get("tags", []))

            # Tags les plus fréquents
            from collections import Counter
            top_tags = Counter(all_tags).most_common(5)

            # Formatage du résumé
            response = f"DATE **Résumé semaine du {week_start.strftime('%d/%m')} au {week_end.strftime('%d/%m/%Y')}**\n\n"
            response += f"**STATS Statistiques:**\n"
            response += f"• {total_entries} entrées sur {days_active} jours actifs\n"
            response += f"• Répartition: {importance_counts['critical']}[CRITICAL] {importance_counts['high']}[HIGH] {importance_counts['normal']}[NORMAL] {importance_counts['low']}[LOW]\n\n"

            if top_tags:
                response += f"**TAGS Thèmes principaux:** {', '.join([f'`{tag}` ({count})' for tag, count in top_tags])}\n\n"

            # Top 3 entrées importantes
            important_entries = sorted(week_entries, key=lambda x: {"critical": 4, "high": 3, "normal": 2, "low": 1}.get(x.get("importance", "normal"), 2), reverse=True)[:3]

            if important_entries:
                response += f"**STAR Moments marquants:**\n"
                for i, entry in enumerate(important_entries, 1):
                    date_str = entry.get("timestamp", "")[:10]
                    importance_emoji = {"critical": "[CRITICAL]", "high": "[HIGH]", "normal": "[NORMAL]", "low": "[LOW]"}.get(entry.get("importance", "normal"), "[NORMAL]")
                    summary = entry.get("summary", "")
                    response += f"{i}. {importance_emoji} **{date_str}** - {summary[:100]}{'...' if len(summary) > 100 else ''}\n"

            return response

        except Exception as e:
            print(f"[ENTRY-GENERATOR] ERREUR Erreur résumé hebdomadaire: {e}")
            return f"ERREUR Erreur résumé hebdomadaire: {e}"

    async def _get_monthly_summary(self, json_manager, groups: list, original_input: str) -> str:
        """Génère un résumé mensuel"""
        try:
            month_str = groups[0] if groups else None  # Format: YYYY-MM
            if not month_str:
                return "ERREUR Mois non spécifié (format: YYYY-MM)"

            print(f"[ENTRY-GENERATOR] DATE Résumé mois: {month_str}")

            # Collecte des entrées du mois
            month_entries = []
            year, month = map(int, month_str.split('-'))

            # Tous les jours du mois
            import calendar
            days_in_month = calendar.monthrange(year, month)[1]

            for day in range(1, days_in_month + 1):
                date_key = f"{year}-{month:02d}-{day:02d}"
                day_entries = json_manager.get_day_entries(date_key)
                if day_entries:
                    month_entries.extend(day_entries)

            if not month_entries:
                month_name = calendar.month_name[month]
                return f"DATE **{month_name} {year}**\n\nAucune activité ce mois."

            # Analyse similaire à la semaine mais sur le mois
            total_entries = len(month_entries)
            days_active = len(set(entry.get("timestamp", "")[:10] for entry in month_entries))

            month_name = calendar.month_name[month]
            response = f"DATE **{month_name} {year}**\n\n"
            response += f"**STATS Activité:** {total_entries} entrées sur {days_active}/{days_in_month} jours\n"
            response += f"**STATS Taux d'activité:** {round(days_active/days_in_month*100)}%\n\n"

            # Répartition par semaines
            weekly_counts = [0, 0, 0, 0, 0]  # Max 5 semaines
            for entry in month_entries:
                entry_date = datetime.strptime(entry.get("timestamp", "")[:10], "%Y-%m-%d").date()
                week_of_month = (entry_date.day - 1) // 7
                if week_of_month < 5:
                    weekly_counts[week_of_month] += 1

            response += f"**STATS Par semaine:** {' | '.join([f'S{i+1}: {count}' for i, count in enumerate(weekly_counts) if count > 0])}\n\n"

            # Top entrées du mois
            important_entries = sorted(month_entries, key=lambda x: {"critical": 4, "high": 3, "normal": 2, "low": 1}.get(x.get("importance", "normal"), 2), reverse=True)[:5]

            if important_entries:
                response += f"**STAR Highlights du mois:**\n"
                for i, entry in enumerate(important_entries, 1):
                    date_str = entry.get("timestamp", "")[:10]
                    importance_emoji = {"critical": "[CRITICAL]", "high": "[HIGH]", "normal": "[NORMAL]", "low": "[LOW]"}.get(entry.get("importance", "normal"), "[NORMAL]")
                    summary = entry.get("summary", "")
                    response += f"{i}. {importance_emoji} **{date_str}** - {summary[:80]}{'...' if len(summary) > 80 else ''}\n"

            return response

        except Exception as e:
            print(f"[ENTRY-GENERATOR] ERREUR Erreur résumé mensuel: {e}")
            return f"ERREUR Erreur résumé mensuel: {e}"

    async def _open_journal_ui_date(self, json_manager, groups: list, original_input: str) -> str:
        """Ouvre l'interface journal pour une date spécifique"""
        try:
            relative_date = groups[0] if groups else ""

            # Pour le moment, retourne une indication
            # TODO: Implémenter ouverture UI avec navigation automatique vers date

            return f"TARGET **Interface Journal**\n\nOuverture de l'interface journal pour '{relative_date}'.\n\n*Fonctionnalité complète disponible via le bouton JOURNAL Journal dans le header.*"

        except Exception as e:
            print(f"[ENTRY-GENERATOR] ERREUR Erreur ouverture UI: {e}")
            return f"ERREUR Erreur ouverture interface: {e}"

    async def _display_filtered_entries(self, json_manager, groups: list, original_input: str) -> str:
        """Affiche les entrées filtrées selon critères"""
        try:
            criteria = groups[0].strip() if groups else ""

            if "importantes" in criteria or "important" in criteria:
                # Filtre par importance
                all_entries = []

                # Récupérer toutes les entrées (approche simple)
                # TODO: Optimiser avec une méthode get_all_entries dans json_manager
                today = date.today()
                for i in range(30):  # 30 derniers jours
                    check_date = today - timedelta(days=i)
                    date_str = check_date.strftime("%Y-%m-%d")
                    day_entries = json_manager.get_day_entries(date_str)
                    if day_entries:
                        all_entries.extend(day_entries)

                # Filtrer par importance
                important_entries = [entry for entry in all_entries if entry.get("importance") in ["high", "critical"]]

                if not important_entries:
                    return "📋 **Entrées importantes**\n\nAucune entrée importante trouvée dans les 30 derniers jours."

                response = f"📋 **Entrées importantes** ({len(important_entries)} trouvée(s))\n\n"

                for i, entry in enumerate(important_entries[:10], 1):  # Max 10
                    date_str = entry.get("timestamp", "")[:10]
                    importance_emoji = {"critical": "[CRITICAL]", "high": "[HIGH]"}.get(entry.get("importance"), "[HIGH]")
                    summary = entry.get("summary", "")

                    response += f"**{i}.** {importance_emoji} **{date_str}**\n"
                    response += f"   {summary[:150]}{'...' if len(summary) > 150 else ''}\n\n"

                return response

            else:
                return f"ERREUR Critère de filtrage non reconnu: '{criteria}'\n\nCritères supportés: importantes, récentes"

        except Exception as e:
            print(f"[ENTRY-GENERATOR] ERREUR Erreur affichage filtré: {e}")
            return f"ERREUR Erreur filtrage: {e}"

    async def _create_entry_manual(self, json_manager, groups: list, original_input: str) -> str:
        """Crée une entrée manuellement depuis une phrase magique"""
        try:
            # Déclencher création d'entrée via le core_journal
            # TODO: Accès au core_journal depuis entry_generator

            return "CREATE **Création d'entrée**\n\nCréation d'une nouvelle entrée de journal en cours...\n\n*Utilisez le bouton JOURNAL Journal > CREATE Capturer conversation pour une création complète.*"

        except Exception as e:
            print(f"[ENTRY-GENERATOR] ERREUR Erreur création manuelle: {e}")
            return f"ERREUR Erreur création d'entrée: {e}"
    
    # =========================================================================
    # DÉTECTION AUTOMATIQUE D'ÉTATS ACTIFS (v2.0)
    # =========================================================================
    
    async def detect_active_states(self, conversation_context: str, entry_id: str, json_manager) -> List[Dict[str, Any]]:
        """
        Analyse le contexte de conversation pour détecter automatiquement des états actifs
        
        Args:
            conversation_context: Texte de la conversation à analyser
            entry_id: ID de l'entrée journal liée
            json_manager: Instance JSONManager pour sauvegarder les états
        
        Returns:
            list: Liste des états détectés et créés
        """
        try:
            if not self.config.get("enable_active_states", False):
                return []
            
            print("[ENTRY-GENERATOR] 🔍 Détection états actifs...")
            
            # Prompt pour l'Archiviste spécialisé détection d'états
            detection_prompt = f"""Tu es l'Archiviste d'OGMA. Analyse cette conversation et identifie les ÉTATS ACTIFS importants qui doivent être suivis dans le temps.

Contexte conversation:
{conversation_context[:2000]}

ÉTATS ACTIFS à identifier:
1. **Santé**: Problèmes médicaux, symptômes, traitements en cours
2. **Projets**: Travaux en cours, objectifs, deadlines
3. **Humeur**: États émotionnels significatifs prolongés
4. **Apprentissage**: Formations, compétences en acquisition
5. **Technique**: Bugs à corriger, features à implémenter
6. **Personnel**: Situations personnelles importantes

Format de réponse (JSON strict):
{{
  "états_détectés": [
    {{
      "category": "santé|projet|humeur|apprentissage|technique|personnel",
      "description": "Description concise de l'état (max 100 chars)",
      "importance": "low|medium|high",
      "confidence": 0.0-1.0
    }}
  ]
}}

RÈGLES STRICTES:
- NE détecte que les états ACTUELS et SIGNIFICATIFS
- Pas d'états résolus ou passés
- Pas d'états triviaux (conversations normales)
- Minimum confidence: 0.6
- Maximum: 3 états par conversation

Réponds UNIQUEMENT avec le JSON, sans texte additionnel."""

            # Appel Archiviste
            response = await self._call_archiviste(detection_prompt)
            if not response:
                print("[ENTRY-GENERATOR] ⚠️ Archiviste n'a pas répondu (détection états)")
                return []
            
            # Parse JSON
            import json
            
            # Nettoyer la réponse (supprimer markdown code blocks si présents)
            cleaned_response = response.strip()
            if cleaned_response.startswith("```"):
                # Supprimer ```json et ```
                lines = cleaned_response.split('\n')
                cleaned_response = '\n'.join(lines[1:-1] if len(lines) > 2 else lines)
            
            try:
                detection_data = json.loads(cleaned_response)
            except json.JSONDecodeError as e:
                print(f"[ENTRY-GENERATOR] ⚠️ Erreur parsing JSON détection: {e}")
                print(f"[ENTRY-GENERATOR] DEBUG Response: {response[:200]}")
                return []
            
            états_détectés = detection_data.get("états_détectés", [])
            
            if not états_détectés:
                print("[ENTRY-GENERATOR] ℹ️ Aucun état actif détecté")
                return []
            
            # Filtrer et créer les états
            created_states = []
            
            for état in états_détectés:
                confidence = état.get("confidence", 0.0)
                
                # Filtre confidence minimum
                if confidence < 0.6:
                    print(f"[ENTRY-GENERATOR] SKIP État rejeté (confidence {confidence} < 0.6)")
                    continue
                
                # Créer l'état via json_manager
                success = json_manager.update_active_state(
                    category=état.get("category", "général"),
                    new_state={
                        "description": état.get("description", ""),
                        "importance": état.get("importance", "medium"),
                        "source_entry_id": entry_id
                    }
                )
                
                if success:
                    created_states.append(état)
                    print(f"[ENTRY-GENERATOR] ✅ État créé: {état.get('category')} - {état.get('description')[:50]}")
            
            print(f"[ENTRY-GENERATOR] ✅ {len(created_states)} états actifs créés")
            return created_states
        
        except Exception as e:
            print(f"[ENTRY-GENERATOR] ERROR detect_active_states: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def generate_micro_entry(self, conversation_id: str, conversation_history: List[Dict], json_manager, **metadata) -> Optional[Dict[str, Any]]:
        """
        Génère une micro-entrée automatique (résumé minimal)
        
        Args:
            conversation_id: ID conversation
            conversation_history: Historique messages
            json_manager: Instance JSONManager
            **metadata: Métadonnées additionnelles
        
        Returns:
            dict: Micro-entrée créée ou None
        """
        try:
            if not self.config.get("auto_archive_enabled", False):
                return None
            
            print("[ENTRY-GENERATOR] 🤏 Génération micro-entrée auto...")
            
            # Vérifier minimum de tokens pour archivage
            min_tokens = self.config.get("auto_archive_min_tokens", 50)
            
            # Estimer tokens de la conversation
            conversation_text = " ".join([msg.get("content", "") for msg in conversation_history])
            token_count = self._estimate_tokens(conversation_text)
            
            if token_count < min_tokens:
                print(f"[ENTRY-GENERATOR] SKIP Conversation trop courte ({token_count} < {min_tokens} tokens)")
                return None
            
            # Détection continuation de conversation (window 2h)
            window_hours = self.config.get("same_conversation_window_hours", 2)
            
            if self.config.get("update_same_conversation", True):
                # Vérifier si continuation
                last_entries = json_manager.search_entries(
                    start_date=(datetime.now() - timedelta(hours=window_hours)).strftime("%Y-%m-%d"),
                    end_date=datetime.now().strftime("%Y-%m-%d"),
                    limit=10
                )
                
                # Chercher entrée même conversation_id
                for entry in last_entries:
                    if entry.get("conversation_id") == conversation_id:
                        # Continuation détectée - mettre à jour l'entrée existante
                        print(f"[ENTRY-GENERATOR] 🔄 Continuation détectée - MAJ entrée {entry.get('entry_id')}")
                        
                        # Générer nouveau résumé fusionné
                        updated_entry = await self._update_existing_entry(
                            entry, 
                            conversation_history, 
                            json_manager
                        )
                        
                        return updated_entry
            
            # Nouvelle micro-entrée
            prompt = f"""Tu es l'Archiviste d'OGMA. Génère un MICRO-RÉSUMÉ ultra-concis de cette conversation.

Conversation ({len(conversation_history)} messages):
{conversation_text[:1500]}

RÈGLES MICRO-RÉSUMÉ:
- Maximum 50 tokens (environ 1-2 phrases)
- Capte UNIQUEMENT l'essentiel
- Ton factuel et neutre
- Pas de détails superflus

Micro-résumé:"""

            summary_response = await self._call_archiviste(prompt)
            
            if not summary_response:
                print("[ENTRY-GENERATOR] ⚠️ Échec génération micro-résumé")
                return None
            
            # Construction micro-entrée
            entry_id = str(uuid.uuid4())[:8]
            
            micro_entry = {
                "id": entry_id,  # Champ obligatoire pour json_manager
                "timestamp": datetime.now().isoformat(),
                "conversation_id": conversation_id,
                "summary": summary_response.strip(),
                "tokens": token_count,  # Champ obligatoire
                "tags": ["auto-archived"],
                "importance": "low",
                "category": "général",
                "participants": metadata.get("participants", ["user", "assistant"]),
                "message_count": len(conversation_history),
                "token_estimate": token_count,
                "auto_generated": True,  # FLAG v2.0
                "reading_time_seconds": 10,
                "metadata": {
                    "auto_archive": True,
                    "generation_timestamp": datetime.now().isoformat()
                }
            }
            
            # Sauvegarde
            success = json_manager.save_entry(micro_entry)
            
            if success:
                print(f"[ENTRY-GENERATOR] ✅ Micro-entrée créée: {entry_id}")
                
                # Détection états actifs
                if self.config.get("enable_active_states", False):
                    await self.detect_active_states(
                        conversation_context=conversation_text,
                        entry_id=entry_id,
                        json_manager=json_manager
                    )
                
                return micro_entry
            else:
                print("[ENTRY-GENERATOR] ❌ Échec sauvegarde micro-entrée")
                return None
        
        except Exception as e:
            print(f"[ENTRY-GENERATOR] ERROR generate_micro_entry: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def _update_existing_entry(self, existing_entry: Dict, new_messages: List[Dict], json_manager) -> Optional[Dict]:
        """
        Met à jour une entrée existante avec nouveaux messages (continuation conversation)
        
        Args:
            existing_entry: Entrée journal existante
            new_messages: Nouveaux messages à intégrer
            json_manager: Instance JSONManager
        
        Returns:
            dict: Entrée mise à jour ou None
        """
        try:
            print(f"[ENTRY-GENERATOR] 🔄 MAJ entrée existante {existing_entry.get('entry_id')}")
            
            # Fusion résumés
            old_summary = existing_entry.get("summary", "")
            new_context = " ".join([msg.get("content", "") for msg in new_messages])
            
            update_prompt = f"""Tu es l'Archiviste d'OGMA. Mets à jour ce résumé avec les nouveaux messages.

RÉSUMÉ EXISTANT:
{old_summary}

NOUVEAUX MESSAGES:
{new_context[:1000]}

RÈGLES MAJ:
- Fusionne intelligemment les informations
- Garde la concision (max 100 tokens)
- Préserve les infos importantes de l'ancien résumé
- Intègre naturellement les nouvelles infos

Résumé mis à jour:"""

            updated_summary = await self._call_archiviste(update_prompt)
            
            if not updated_summary:
                print("[ENTRY-GENERATOR] ⚠️ Échec MAJ résumé")
                return None
            
            # Mise à jour entrée
            existing_entry["summary"] = updated_summary.strip()
            existing_entry["message_count"] = existing_entry.get("message_count", 0) + len(new_messages)
            existing_entry["metadata"]["last_update"] = datetime.now().isoformat()
            existing_entry["metadata"]["update_count"] = existing_entry["metadata"].get("update_count", 0) + 1
            
            # Sauvegarde (remplacer l'ancienne)
            # TODO: json_manager.update_entry() method
            # Pour l'instant on resauve avec même entry_id
            success = json_manager.save_entry(existing_entry)
            
            if success:
                print(f"[ENTRY-GENERATOR] ✅ Entrée {existing_entry.get('entry_id')} mise à jour")
                return existing_entry
            else:
                print("[ENTRY-GENERATOR] ❌ Échec sauvegarde MAJ")
                return None
        
        except Exception as e:
            print(f"[ENTRY-GENERATOR] ERROR _update_existing_entry: {e}")
            return None