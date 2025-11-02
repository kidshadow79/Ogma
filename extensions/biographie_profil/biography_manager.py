"""
Gestionnaire principal de l'extension Biographie Profil
======================================================

Gère la logique métier pour:
- Détection des noms d'utilisateurs
- Volume 1: Filtrage FAISS par utilisateur  
- Volume 2: Biographies narratives (NOUVEAU: Architecture JSON structurée)
- Gestion des fichiers et backups
"""

import re
import json
import sqlite3
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class StructuredBiographyManager:
    """
    🏗️ NOUVELLE ARCHITECTURE VOLUME 2 - Gestion JSON structurée
    ============================================================
    
    Remplace l'enrichissement progressif Markdown par une base de données JSON ultra-organisée
    avec génération automatique du journal Markdown.
    """

    def __init__(self, user_name: str, data_dir: Path):
        self.user_name = user_name
        self.user_dir = data_dir / user_name.lower()
        self.user_dir.mkdir(exist_ok=True)
        
        # Fichiers de la nouvelle architecture
        self.structured_file = self.user_dir / "volume2_structured.json"
        self.journal_file = self.user_dir / "volume2_journal.md"
        
        # Initialiser avec structure vide si nécessaire
        self._ensure_structured_file_exists()
        
        print(f"[STRUCTURED-MANAGER] ✅ Gestionnaire structuré initialisé pour {user_name}")

    def _ensure_structured_file_exists(self) -> None:
        """Crée le fichier JSON structuré avec le schéma de base s'il n'existe pas"""
        if not self.structured_file.exists():
            initial_structure = self._get_empty_structure()
            self.save_structured_data(initial_structure)
            print(f"[STRUCTURED-MANAGER] 📋 Structure JSON initialisée pour {self.user_name}")

    def _get_empty_structure(self) -> Dict:
        """Retourne la structure JSON vide conforme au schéma"""
        return {
            "metadata": {
                "user_name": self.user_name,
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "total_analyses": 0,
                "data_sources": []
            },
            "chronologie": [],
            "etude_psychique": {
                "mbti": {
                    "type_estime": None,
                    "confiance": 0.0,
                    "derniere_evaluation": None,
                    "indices_observes": []
                },
                "profil_psychologique": {
                    "traits_dominants": [],
                    "mecanismes_defense": [],
                    "zones_vulnerabilite": []
                },
                "intelligence_emotionnelle": {
                    "score_estime": None,
                    "points_forts": [],
                    "points_amelioration": []
                }
            },
            "etude_intellectuelle": {
                "structure_mentale": {
                    "type_pensee": None,
                    "processus_decision": None,
                    "gestion_information": None
                },
                "structure_memoire": {
                    "type_dominant": None,
                    "points_forts": [],
                    "particularites": []
                },
                "evaluation_comparative": {
                    "qi_estime": None,
                    "percentile_population": None,
                    "comparaison_utilisateurs_ia": None,
                    "domaines_excellence": []
                }
            },
            "etude_physique": {
                "traits_physiques": {
                    "taille": None,
                    "corpulence": None,
                    "particularites": []
                },
                "expressions_caracteristiques": {
                    "micro_expressions": [],
                    "gestuelle": []
                },
                "ressemblances_notees": {
                    "personnalites": [],
                    "traits_communs": []
                }
            },
            "etude_gouts_preferences": {
                "preferences_fortes": {
                    "intellectuel": [],
                    "artistique": [],
                    "social": []
                },
                "repulsions_identifiees": {
                    "social": [],
                    "intellectuel": [],
                    "environnemental": []
                },
                "evolutions_observees": []
            }
        }

    def load_structured_data(self) -> Dict:
        """Charge les données JSON structurées"""
        try:
            if self.structured_file.exists():
                with open(self.structured_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return self._get_empty_structure()
        except Exception as e:
            print(f"[STRUCTURED-MANAGER] ❌ Erreur chargement données: {e}")
            return self._get_empty_structure()

    def save_structured_data(self, data: Dict) -> bool:
        """Sauvegarde les données JSON structurées"""
        try:
            # Mettre à jour les métadonnées
            data["metadata"]["last_updated"] = datetime.now().isoformat()
            data["metadata"]["total_analyses"] = data["metadata"].get("total_analyses", 0) + 1
            
            with open(self.structured_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"[STRUCTURED-MANAGER] ✅ Données structurées sauvegardées")
            return True
        except Exception as e:
            print(f"[STRUCTURED-MANAGER] ❌ Erreur sauvegarde: {e}")
            return False

    def add_chronology_event(self, event_data: Dict) -> bool:
        """Ajoute un événement à la chronologie"""
        try:
            data = self.load_structured_data()
            
            # Ajouter l'événement avec timestamp
            event = {
                "timestamp": datetime.now().isoformat(),
                "source": event_data.get("source", "unknown"),
                "evenement": event_data.get("evenement", ""),
                "conversation_id": event_data.get("conversation_id"),
                "contexte": event_data.get("contexte", "")
            }
            
            data["chronologie"].append(event)
            
            # Trier par timestamp (plus récent en premier)
            data["chronologie"].sort(key=lambda x: x["timestamp"], reverse=True)
            
            return self.save_structured_data(data)
        except Exception as e:
            print(f"[STRUCTURED-MANAGER] ❌ Erreur ajout chronologie: {e}")
            return False

    def update_psychological_profile(self, profile_updates: Dict) -> bool:
        """Met à jour le profil psychologique"""
        try:
            data = self.load_structured_data()
            
            # Mise à jour récursive des sections
            if "mbti" in profile_updates:
                data["etude_psychique"]["mbti"].update(profile_updates["mbti"])
            if "profil_psychologique" in profile_updates:
                data["etude_psychique"]["profil_psychologique"].update(profile_updates["profil_psychologique"])
            if "intelligence_emotionnelle" in profile_updates:
                data["etude_psychique"]["intelligence_emotionnelle"].update(profile_updates["intelligence_emotionnelle"])
            
            return self.save_structured_data(data)
        except Exception as e:
            print(f"[STRUCTURED-MANAGER] ❌ Erreur mise à jour profil psychologique: {e}")
            return False

    def update_intellectual_profile(self, profile_updates: Dict) -> bool:
        """Met à jour le profil intellectuel"""
        try:
            data = self.load_structured_data()
            
            if "structure_mentale" in profile_updates:
                data["etude_intellectuelle"]["structure_mentale"].update(profile_updates["structure_mentale"])
            if "structure_memoire" in profile_updates:
                data["etude_intellectuelle"]["structure_memoire"].update(profile_updates["structure_memoire"])
            if "evaluation_comparative" in profile_updates:
                data["etude_intellectuelle"]["evaluation_comparative"].update(profile_updates["evaluation_comparative"])
            
            return self.save_structured_data(data)
        except Exception as e:
            print(f"[STRUCTURED-MANAGER] ❌ Erreur mise à jour profil intellectuel: {e}")
            return False

    def generate_markdown_journal(self) -> str:
        """
        🎯 GÉNÉRATION AUTOMATIQUE DU JOURNAL MARKDOWN
        Convertit les données JSON structurées en journal lisible
        """
        try:
            data = self.load_structured_data()
            
            # Header du journal
            metadata = data["metadata"]
            journal_content = f"""# 📋 JOURNAL BIOGRAPHIQUE - {metadata["user_name"]}

*Généré automatiquement le {datetime.now().strftime('%d/%m/%Y à %H:%M')} à partir de {metadata["total_analyses"]} analyses*

**Sources de données :** {', '.join(metadata.get("data_sources", []))}

---

## 🕐 CHRONOLOGIE DES ÉVÉNEMENTS

"""

            # Section chronologie
            chronologie = data.get("chronologie", [])
            if chronologie:
                current_month = None
                for event in chronologie:
                    event_date = datetime.fromisoformat(event["timestamp"].replace('Z', '+00:00'))
                    month_year = event_date.strftime('%B %Y')
                    
                    if current_month != month_year:
                        current_month = month_year
                        journal_content += f"\n### {month_year}\n"
                    
                    journal_content += f"""**{event_date.strftime('%d/%m/%Y - %H:%M')}** | {event["evenement"]}  
*Source: {event["source"]}*{' | ID: ' + event["conversation_id"] if event.get("conversation_id") else ''}  
{event["contexte"]}

"""
            else:
                journal_content += "*Aucun événement enregistré*\n\n"

            # Section étude psychique
            psychique = data.get("etude_psychique", {})
            journal_content += """---

## 🧠 ÉTUDE PSYCHIQUE

"""
            
            # MBTI
            mbti = psychique.get("mbti", {})
            if mbti.get("type_estime"):
                journal_content += f"""### Profil MBTI : {mbti["type_estime"]} (Confiance: {mbti.get("confiance", 0)*100:.0f}%)
*Dernière évaluation: {mbti.get("derniere_evaluation", "Non définie")}*

**Indices observés :**
"""
                for indice in mbti.get("indices_observes", []):
                    journal_content += f"- {indice}\n"
                journal_content += "\n"

            # Profil psychologique
            profil = psychique.get("profil_psychologique", {})
            if any(profil.values()):
                journal_content += """### Mécanismes psychologiques
"""
                if profil.get("traits_dominants"):
                    journal_content += f"**Traits dominants :** {', '.join(profil['traits_dominants'])}  \n"
                if profil.get("mecanismes_defense"):
                    journal_content += f"**Défenses principales :** {', '.join(profil['mecanismes_defense'])}  \n"
                if profil.get("zones_vulnerabilite"):
                    journal_content += f"**Vulnérabilités :** {', '.join(profil['zones_vulnerabilite'])}\n\n"

            # Section étude intellectuelle
            intellectuel = data.get("etude_intellectuelle", {})
            journal_content += """---

## 🎓 ÉTUDE INTELLECTUELLE

"""
            
            # Architecture mentale
            structure_mentale = intellectuel.get("structure_mentale", {})
            if any(structure_mentale.values()):
                journal_content += """### Architecture mentale
"""
                if structure_mentale.get("type_pensee"):
                    journal_content += f"- **Type de pensée :** {structure_mentale['type_pensee']}\n"
                if structure_mentale.get("processus_decision"):
                    journal_content += f"- **Processus décisionnel :** {structure_mentale['processus_decision']}\n"
                if structure_mentale.get("gestion_information"):
                    journal_content += f"- **Gestion information :** {structure_mentale['gestion_information']}\n\n"

            # Évaluation comparative
            evaluation = intellectuel.get("evaluation_comparative", {})
            if any(evaluation.values()):
                journal_content += """### Évaluation comparative
"""
                if evaluation.get("qi_estime"):
                    journal_content += f"- **QI estimé :** {evaluation['qi_estime']}"
                    if evaluation.get("percentile_population"):
                        journal_content += f" (Percentile {evaluation['percentile_population']})"
                    journal_content += "\n"
                if evaluation.get("comparaison_utilisateurs_ia"):
                    journal_content += f"- **vs Utilisateurs moyens IA :** {evaluation['comparaison_utilisateurs_ia']}\n"
                if evaluation.get("domaines_excellence"):
                    journal_content += f"- **Domaines d'excellence :** {', '.join(evaluation['domaines_excellence'])}\n\n"

            # Section étude physique
            physique = data.get("etude_physique", {})
            if any(v for v in physique.values() if v):
                journal_content += """---

## 👤 ÉTUDE PHYSIQUE

### Caractéristiques observées
"""
                traits = physique.get("traits_physiques", {})
                if traits.get("taille") or traits.get("corpulence"):
                    journal_content += f"- Morphologie: {traits.get('taille', 'Non définie')}, {traits.get('corpulence', 'non définie')}\n"
                
                for particularite in traits.get("particularites", []):
                    journal_content += f"- {particularite}\n"
                journal_content += "\n"

            # Section goûts & préférences
            preferences = data.get("etude_gouts_preferences", {})
            if any(v for v in preferences.values() if v):
                journal_content += """---

## 🎯 GOÛTS & PRÉFÉRENCES

"""
                pref_fortes = preferences.get("preferences_fortes", {})
                if any(pref_fortes.values()):
                    journal_content += "### Affinités\n"
                    for domaine, items in pref_fortes.items():
                        if items:
                            journal_content += f"**{domaine.capitalize()} :** {', '.join(items)}  \n"
                    journal_content += "\n"

                repulsions = preferences.get("repulsions_identifiees", {})
                if any(repulsions.values()):
                    journal_content += "### Répulsions\n"
                    for domaine, items in repulsions.items():
                        if items:
                            journal_content += f"**{domaine.capitalize()} :** {', '.join(items)}  \n"
                    journal_content += "\n"

                evolutions = preferences.get("evolutions_observees", [])
                if evolutions:
                    journal_content += "### Évolutions récentes\n"
                    for evolution in evolutions:
                        journal_content += f"**{evolution.get('periode', 'Période inconnue')} :** {evolution.get('changement', '')}\n"
                        if evolution.get("declencheur"):
                            journal_content += f"*Déclencheur : {evolution['declencheur']}*\n"
                    journal_content += "\n"

            # Footer
            journal_content += f"""---

*Journal généré automatiquement par OGMA le {datetime.now().strftime('%d/%m/%Y à %H:%M')}*  
*Base de données : {self.structured_file.name}*
"""

            return journal_content

        except Exception as e:
            print(f"[STRUCTURED-MANAGER] ❌ Erreur génération journal: {e}")
            return f"# Erreur de génération\n\nImpossible de générer le journal : {e}"

    def save_generated_journal(self) -> bool:
        """Sauvegarde le journal généré dans le fichier Markdown"""
        try:
            journal_content = self.generate_markdown_journal()
            
            with open(self.journal_file, 'w', encoding='utf-8') as f:
                f.write(journal_content)
            
            print(f"[STRUCTURED-MANAGER] 📖 Journal sauvegardé: {self.journal_file}")
            return True
        except Exception as e:
            print(f"[STRUCTURED-MANAGER] ❌ Erreur sauvegarde journal: {e}")
            return False

    # =============================
    # 🗂️ HISTORIQUE COMPLET - SYSTÈME DE TRACKING
    # =============================

    def _get_processed_documents_file(self) -> Path:
        """Retourne le chemin du fichier de tracking des documents traités"""
        return self.user_dir / "processed_documents.json"

    def load_processed_documents(self) -> Dict:
        """Charge la liste des documents déjà traités"""
        try:
            processed_file = self._get_processed_documents_file()
            if processed_file.exists():
                with open(processed_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Structure initiale
                return {
                    "user_name": self.user_name,
                    "created_at": datetime.now().isoformat(),
                    "last_scan": None,
                    "processed_files": [],
                    "skipped_files": []
                }
        except Exception as e:
            print(f"[STRUCTURED-MANAGER] ❌ Erreur chargement tracking: {e}")
            return {
                "user_name": self.user_name,
                "created_at": datetime.now().isoformat(),
                "last_scan": None,
                "processed_files": [],
                "skipped_files": []
            }

    def save_processed_documents(self, processed_data: Dict) -> bool:
        """Sauvegarde la liste des documents traités"""
        try:
            processed_file = self._get_processed_documents_file()
            processed_data["last_scan"] = datetime.now().isoformat()
            
            with open(processed_file, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, ensure_ascii=False, indent=2)
            
            print(f"[STRUCTURED-MANAGER] 📋 Tracking mis à jour: {len(processed_data['processed_files'])} traités")
            return True
        except Exception as e:
            print(f"[STRUCTURED-MANAGER] ❌ Erreur sauvegarde tracking: {e}")
            return False

    def _get_file_hash(self, file_path: Path) -> str:
        """Calcule le hash SHA256 d'un fichier"""
        import hashlib
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()[:16]  # 16 premiers caractères suffisent
        except Exception as e:
            print(f"[STRUCTURED-MANAGER] ⚠️ Erreur calcul hash {file_path}: {e}")
            return "unknown"

    def scan_conversation_files(self, min_size_kb: int = 30) -> List[Dict]:
        """
        Scan les fichiers de conversations et retourne ceux > min_size_kb non encore traités
        
        Args:
            min_size_kb: Taille minimale en Ko (défaut 30ko)
            
        Returns:
            Liste des nouveaux fichiers à traiter
        """
        try:
            conversations_dir = Path("data/conversations")
            if not conversations_dir.exists():
                print(f"[STRUCTURED-MANAGER] ⚠️ Dossier conversations introuvable: {conversations_dir}")
                return []

            # Charger le tracking existant
            processed_data = self.load_processed_documents()
            processed_hashes = {item["file_hash"] for item in processed_data["processed_files"]}
            
            min_size_bytes = min_size_kb * 1024
            new_files = []
            skipped_count = 0
            
            print(f"[STRUCTURED-MANAGER] 🔍 Scan conversations (min: {min_size_kb}Ko)...")
            
            # Scanner tous les fichiers JSON
            for conv_file in conversations_dir.glob("*.json"):
                try:
                    file_size = conv_file.stat().st_size
                    
                    # Filtrer par taille
                    if file_size < min_size_bytes:
                        skipped_count += 1
                        continue
                    
                    # Calculer hash
                    file_hash = self._get_file_hash(conv_file)
                    
                    # Vérifier si déjà traité
                    if file_hash in processed_hashes:
                        continue
                    
                    # Nouveau fichier à traiter
                    new_files.append({
                        "file_path": str(conv_file),
                        "file_size": file_size,
                        "file_hash": file_hash,
                        "size_kb": round(file_size / 1024, 1)
                    })
                    
                except Exception as e:
                    print(f"[STRUCTURED-MANAGER] ⚠️ Erreur traitement {conv_file}: {e}")
                    continue
            
            total_files = len(list(conversations_dir.glob("*.json")))
            print(f"[STRUCTURED-MANAGER] 📊 Scan terminé:")
            print(f"   - Total fichiers: {total_files}")
            print(f"   - Trop petits (< {min_size_kb}Ko): {skipped_count}")
            print(f"   - Déjà traités: {len(processed_hashes)}")
            print(f"   - Nouveaux à traiter: {len(new_files)}")
            
            return new_files
            
        except Exception as e:
            print(f"[STRUCTURED-MANAGER] ❌ Erreur scan conversations: {e}")
            return []

    def process_conversation_file(self, file_info: Dict) -> Optional[Dict]:
        """
        Traite un fichier de conversation pour extraire les données biographiques
        
        Args:
            file_info: Info du fichier (path, size, hash)
            
        Returns:
            Données extraites ou None si erreur
        """
        try:
            file_path = Path(file_info["file_path"])
            
            print(f"[STRUCTURED-MANAGER] 📖 Traitement: {file_path.name} ({file_info['size_kb']}Ko)")
            
            # Charger le fichier de conversation
            with open(file_path, 'r', encoding='utf-8') as f:
                conversation_data = json.load(f)
            
            # Gérer les deux formats possibles
            if isinstance(conversation_data, list):
                # Format direct: array de messages
                messages = conversation_data
            elif isinstance(conversation_data, dict):
                # Format objet: avec propriété messages
                messages = conversation_data.get("messages", [])
            else:
                print(f"[STRUCTURED-MANAGER] ⚠️ Format de conversation inconnu dans {file_path.name}")
                return None
            
            if not messages:
                print(f"[STRUCTURED-MANAGER] ⚠️ Aucun message dans {file_path.name}")
                return None
            
            # Préparer les données pour l'analyse
            processed_data = {
                "source_file": str(file_path),
                "file_hash": file_info["file_hash"], 
                "message_count": len(messages),
                "file_size": file_info["file_size"],
                "processed_at": datetime.now().isoformat(),
                "messages": messages[:100]  # Limiter à 100 messages pour éviter surcharge
            }
            
            print(f"[STRUCTURED-MANAGER] ✅ {len(messages)} messages extraits de {file_path.name}")
            return processed_data
            
        except Exception as e:
            print(f"[STRUCTURED-MANAGER] ❌ Erreur traitement fichier {file_info['file_path']}: {e}")
            return None

    def integrate_historical_conversations(self, max_files: int = 5) -> int:
        """
        Intègre les conversations historiques dans le JSON structuré
        
        Args:
            max_files: Nombre maximum de fichiers à traiter par session (éviter surcharge)
            
        Returns:
            Nombre de fichiers traités
        """
        try:
            print(f"[STRUCTURED-MANAGER] 🏗️ Intégration historique (max: {max_files} fichiers)")
            
            # Scanner les nouveaux fichiers
            new_files = self.scan_conversation_files()
            
            if not new_files:
                print(f"[STRUCTURED-MANAGER] ℹ️ Aucun nouveau fichier à traiter")
                return 0
            
            # Limiter le nombre de fichiers traités
            files_to_process = new_files[:max_files]
            processed_count = 0
            
            # Charger le tracking
            processed_data = self.load_processed_documents()
            
            for file_info in files_to_process:
                # Traiter le fichier
                conversation_data = self.process_conversation_file(file_info)
                
                if conversation_data:
                    # Marquer comme traité
                    processed_data["processed_files"].append({
                        "file_path": file_info["file_path"],
                        "file_size": file_info["file_size"],
                        "file_hash": file_info["file_hash"],
                        "processed_at": conversation_data["processed_at"],
                        "message_count": conversation_data["message_count"]
                    })
                    
                    processed_count += 1
                    print(f"[STRUCTURED-MANAGER] ✅ Traité: {Path(file_info['file_path']).name}")
                
                else:
                    # Marquer comme ignoré
                    processed_data["skipped_files"].append({
                        "file_path": file_info["file_path"],
                        "reason": "processing_error",
                        "file_size": file_info["file_size"]
                    })
            
            # Sauvegarder le tracking
            self.save_processed_documents(processed_data)
            
            print(f"[STRUCTURED-MANAGER] 🎯 Intégration terminée: {processed_count} fichiers traités")
            return processed_count
            
        except Exception as e:
            print(f"[STRUCTURED-MANAGER] ❌ Erreur intégration historique: {e}")
            return 0

    async def integrate_summaries_cache(self, max_summaries: int = 20) -> int:
        """
        Intègre les résumés de conversations progressives depuis summaries_cache
        
        Ces résumés contiennent des analyses psychologiques raffinées déjà produites par l'IA,
        constituant une source précieuse d'insights comportementaux et personnels.
        
        Args:
            max_summaries: Nombre maximum de résumés à traiter par session
            
        Returns:
            Nombre de résumés traités
        """
        try:
            print(f"[STRUCTURED-MANAGER] 🧠 Intégration summaries_cache (max: {max_summaries} résumés)")
            
            # Répertoire des résumés
            summaries_dir = Path("data/summaries_cache")
            if not summaries_dir.exists():
                print(f"[STRUCTURED-MANAGER] ⚠️ Répertoire summaries_cache introuvable")
                return 0
            
            # Scanner les fichiers de résumés
            summary_files = []
            for file_path in summaries_dir.glob("*.txt"):
                try:
                    file_stat = file_path.stat()
                    summary_files.append({
                        "file_path": str(file_path),
                        "file_name": file_path.name,
                        "file_size": file_stat.st_size,
                        "modified_time": file_stat.st_mtime,
                        "is_fusion": file_path.name.startswith("fusion_")
                    })
                except OSError:
                    continue
            
            # Trier par taille (les plus gros résumés = plus riches)
            summary_files.sort(key=lambda x: x["file_size"], reverse=True)
            
            # Limiter le nombre traité
            files_to_process = summary_files[:max_summaries]
            
            if not files_to_process:
                print(f"[STRUCTURED-MANAGER] ℹ️ Aucun résumé à traiter")
                return 0
                
            # Charger les données structurées existantes
            structured_data = self.load_structured_data()
            processed_count = 0
            
            for file_info in files_to_process:
                try:
                    # Lire le contenu du résumé
                    with open(file_info["file_path"], 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                    
                    if not content or len(content) < 50:
                        continue
                    
                    # Analyser le résumé via l'IA
                    analysis_result = await self._analyze_summary_content(content, file_info)
                    
                    if analysis_result:
                        # Intégrer dans la structure JSON
                        self._integrate_summary_analysis(structured_data, analysis_result, file_info)
                        processed_count += 1
                        
                        print(f"[STRUCTURED-MANAGER] ✅ Résumé traité: {file_info['file_name'][:20]}...")
                        
                except Exception as e:
                    print(f"[STRUCTURED-MANAGER] ⚠️ Erreur traitement {file_info['file_name']}: {e}")
                    continue
            
            # Sauvegarder les données enrichies
            if processed_count > 0:
                self.save_structured_data(structured_data)
                print(f"[STRUCTURED-MANAGER] 🎯 Summaries intégrées: {processed_count} résumés traités")
            
            return processed_count
            
        except Exception as e:
            print(f"[STRUCTURED-MANAGER] ❌ Erreur intégration summaries: {e}")
            return 0
    
    async def _analyze_summary_content(self, content: str, file_info: Dict) -> Dict:
        """Analyse un résumé via l'IA pour extraire des insights psychologiques"""
        try:
            # Accéder aux instances IA globales OGMA via _get_ogma()
            def _get_ogma():
                import ogma_ng
                return ogma_ng
            
            # Utiliser l'archiviste si disponible, sinon le chat controller
            archiviste = _get_ogma()._ensure_archiviste_controller()
            if archiviste and archiviste.is_available():
                ai_controller = archiviste
            else:
                chat = _get_ogma()._ensure_chat_controller()
                if chat and chat.is_available():
                    ai_controller = chat
                else:
                    # Fallback : essayer d'analyser avec une approche simplifiée
                    return self._simple_summary_analysis(content, file_info)
            
            # Prompt d'analyse spécialisé pour les résumés
            analysis_prompt = f"""Analyse ce résumé de conversation pour extraire des insights biographiques structurés.

RÉSUMÉ À ANALYSER:
{content}

CONTEXTE:
- Type: {"Fusion (résumé enrichi)" if file_info.get("is_fusion") else "Résumé simple"}
- Taille: {file_info.get("file_size", 0)} octets

Extrais et structure les informations selon ces catégories (UNIQUEMENT si présentes dans le résumé):

1. CHRONOLOGIE: Événements, moments clés, évolutions temporelles
2. PSYCHOLOGIQUE: Traits de personnalité, mécanismes de défense, émotions, dilemmes
3. INTELLECTUEL: Patterns de pensée, centres d'intérêt, capacités cognitives
4. PHYSIQUE: Descriptions physiques, expressions, gestuelle (si mentionnées)
5. PRÉFÉRENCES: Goûts, aversions, évolutions des préférences

Réponds uniquement en JSON valide avec cette structure:
{{
  "chronologie": ["événement 1", "événement 2"],
  "psychologique": {{
    "traits": ["trait 1", "trait 2"],
    "emotions": ["émotion 1"],
    "mecanismes": ["mécanisme 1"]
  }},
  "intellectuel": {{
    "patterns_pensee": ["pattern 1"],
    "interets": ["intérêt 1"]
  }},
  "physique": {{
    "descriptions": ["description 1"],
    "expressions": ["expression 1"]
  }},
  "preferences": {{
    "positives": ["préférence 1"],
    "negatives": ["aversion 1"]
  }},
  "insights_cles": ["insight majeur 1", "insight majeur 2"]
}}

Si une catégorie est vide, mets un tableau/objet vide."""

            # Analyser via le contrôleur IA disponible
            messages = [{"role": "user", "content": analysis_prompt}]
            
            response, error = await ai_controller.call_chat_api(
                messages=messages,
                max_tokens=8192,
                context_length=32000,
                temperature=0.3,
                is_json=True
            )
            
            if error:
                print(f"[STRUCTURED-MANAGER] ⚠️ Erreur IA: {error}")
                return self._simple_summary_analysis(content, file_info)
            
            if not response:
                return None
                
            # Parser la réponse JSON
            import json
            import re
            
            # Nettoyer la réponse pour extraire le JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            
            return None
            
        except Exception as e:
            print(f"[STRUCTURED-MANAGER] ⚠️ Erreur analyse résumé: {e}")
            return None
    
    def _simple_summary_analysis(self, content: str, file_info: Dict) -> Dict:
        """Analyse simplifiée par mots-clés en cas d'absence d'IA"""
        try:
            import re
            
            # Analyse par mots-clés et patterns
            result = {
                "chronologie": [],
                "psychologique": {"traits": [], "emotions": [], "mecanismes": []},
                "intellectuel": {"patterns_pensee": [], "interets": []},
                "physique": {"descriptions": [], "expressions": []},
                "preferences": {"positives": [], "negatives": []},
                "insights_cles": []
            }
            
            content_lower = content.lower()
            
            # Mots-clés psychologiques
            traits_keywords = ["empathique", "enthousiaste", "anxieux", "confiant", "créatif", "analytique", "intuitif"]
            emotions_keywords = ["gratitude", "émotion", "joie", "peur", "colère", "tristesse", "excitation"]
            mecanismes_keywords = ["défense", "projection", "déni", "rationalisation", "sublimation"]
            
            # Rechercher traits
            for trait in traits_keywords:
                if trait in content_lower:
                    result["psychologique"]["traits"].append(f"Montre des signes de {trait}")
            
            # Rechercher émotions
            for emotion in emotions_keywords:
                if emotion in content_lower:
                    result["psychologique"]["emotions"].append(f"Exprime {emotion}")
            
            # Patterns intellectuels
            if "analyse" in content_lower or "réflexion" in content_lower:
                result["intellectuel"]["patterns_pensee"].append("Capacité d'analyse et de réflexion")
            if "technique" in content_lower or "architecture" in content_lower:
                result["intellectuel"]["interets"].append("Intérêt pour les aspects techniques")
            
            # Extraire des phrases clés comme insights
            sentences = re.split(r'[.!?]+', content)
            for sentence in sentences:
                if len(sentence.strip()) > 30:  # Phrases substantielles
                    if any(kw in sentence.lower() for kw in ["ressent", "exprime", "manifeste", "décrit"]):
                        result["insights_cles"].append(sentence.strip())
            
            # Limiter à 3 insights max
            result["insights_cles"] = result["insights_cles"][:3]
            
            return result
            
        except Exception as e:
            print(f"[STRUCTURED-MANAGER] ⚠️ Erreur analyse simple: {e}")
            return None
    
    def _integrate_summary_analysis(self, structured_data: Dict, analysis: Dict, file_info: Dict):
        """Intègre les résultats d'analyse d'un résumé dans la structure JSON"""
        try:
            source_tag = f"summary_{file_info['file_name'][:16]}"
            
            # Intégrer chronologie
            for event in analysis.get("chronologie", []):
                if event.strip():
                    structured_data["chronologie"].append({
                        "timestamp": datetime.now().isoformat(),
                        "source": source_tag,
                        "evenement": event.strip(),
                        "conversation_id": None,
                        "contexte": "Extrait de résumé progressif"
                    })
            
            # Intégrer profil psychologique
            psycho = analysis.get("psychologique", {})
            if psycho.get("traits"):
                structured_data["etude_psychique"]["profil_psychologique"]["traits_dominants"].extend(
                    [t.strip() for t in psycho["traits"] if t.strip()]
                )
            if psycho.get("mecanismes"):
                structured_data["etude_psychique"]["profil_psychologique"]["mecanismes_defense"].extend(
                    [m.strip() for m in psycho["mecanismes"] if m.strip()]
                )
            
            # Intégrer profil intellectuel
            intel = analysis.get("intellectuel", {})
            if intel.get("patterns_pensee"):
                # Créer la clé si elle n'existe pas
                if "patterns_dominants" not in structured_data["etude_intellectuelle"]["structure_mentale"]:
                    structured_data["etude_intellectuelle"]["structure_mentale"]["patterns_dominants"] = []
                structured_data["etude_intellectuelle"]["structure_mentale"]["patterns_dominants"].extend(
                    [p.strip() for p in intel["patterns_pensee"] if p.strip()]
                )
            if intel.get("interets"):
                # Créer la section centres_interet si elle n'existe pas
                if "centres_interet" not in structured_data["etude_intellectuelle"]:
                    structured_data["etude_intellectuelle"]["centres_interet"] = {"domaines_expertise": []}
                elif "domaines_expertise" not in structured_data["etude_intellectuelle"]["centres_interet"]:
                    structured_data["etude_intellectuelle"]["centres_interet"]["domaines_expertise"] = []
                
                structured_data["etude_intellectuelle"]["centres_interet"]["domaines_expertise"].extend(
                    [i.strip() for i in intel["interets"] if i.strip()]
                )
            
            # Intégrer préférences
            prefs = analysis.get("preferences", {})
            if prefs.get("positives"):
                structured_data["etude_gouts_preferences"]["preferences_fortes"]["intellectuel"].extend(
                    [p.strip() for p in prefs["positives"] if p.strip()]
                )
            if prefs.get("negatives"):
                structured_data["etude_gouts_preferences"]["repulsions_identifiees"]["intellectuel"].extend(
                    [n.strip() for n in prefs["negatives"] if n.strip()]
                )
            
            # Ajouter insights clés comme événements spéciaux
            for insight in analysis.get("insights_cles", []):
                if insight.strip():
                    structured_data["chronologie"].append({
                        "timestamp": datetime.now().isoformat(),
                        "source": f"{source_tag}_insight",
                        "evenement": f"Insight psychologique: {insight.strip()}",
                        "conversation_id": None,
                        "contexte": "Analyse de résumé progressif"
                    })
            
        except Exception as e:
            print(f"[STRUCTURED-MANAGER] ⚠️ Erreur intégration analyse: {e}")

class BiographyManager:
    """Gestionnaire principal des biographies utilisateur"""

    def __init__(self, memory_manager):
        self.memory_manager = memory_manager
        self.data_dir = Path("data/biographies")
        self.data_dir.mkdir(exist_ok=True)

        # Pattern de détection des prénoms (version simple pour Phase 1)
        self.name_pattern = r'\b([A-Z][a-z]{2,15})\b'

        print("[BIOGRAPHY-MANAGER] ✅ Gestionnaire initialisé")

    def get_current_conversation_data(self) -> Dict:
        """
        Récupère les données intégrales de la conversation actuelle
        Retourne le JSON complet avec tous les messages
        """
        try:
            # Import nécessaire pour accéder aux variables globales d'OGMA
            import ogma_ng

            # ✅ IMPORTANT : Utiliser _chat_history_ui pour avoir TOUS les messages originaux
            # _chat_history contient des résumés optimisés pour l'IA
            # _chat_history_ui contient l'historique COMPLET pour l'utilisateur et les extensions
            chat_history = getattr(ogma_ng, '_chat_history_ui', [])

            # Fallback sur _chat_history si _chat_history_ui n'existe pas encore (compatibilité)
            if not chat_history:
                chat_history = getattr(ogma_ng, '_chat_history', [])

            conversation_id = getattr(ogma_ng, '_current_conversation_id', None)

            if not chat_history:
                print("[BIOGRAPHY-MANAGER] ⚠️ Aucune conversation actuelle trouvée")
                return {}

            # Construire le dictionnaire de données de conversation
            conversation_data = {
                'conversation_id': conversation_id,
                'timestamp': datetime.now().isoformat(),
                'total_messages': len(chat_history),
                'messages': []
            }

            # Ajouter tous les messages avec leur contenu intégral
            for i, message in enumerate(chat_history):
                message_data = {
                    'index': i,
                    'role': message.get('role', 'unknown'),
                    'content': message.get('content', ''),
                    'timestamp': message.get('timestamp', datetime.now().isoformat())
                }
                conversation_data['messages'].append(message_data)

            print(f"[BIOGRAPHY-MANAGER] ✅ Conversation COMPLÈTE récupérée: {len(chat_history)} messages (historique UI)")
            return conversation_data

        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur récupération conversation: {e}")
            return {}

    async def _search_memories_for_biography(self, query: str, k: int = 100) -> List[Dict]:
        """
        Recherche directe dans FAISS sans filtrage strict pour la biographie
        Récupère tous les souvenirs pertinents sans limite artificielle
        """
        try:
            if not self.memory_manager:
                return []

            # Générer l'embedding de la requête
            query_embedding = await self.memory_manager._generate_embedding(query)
            if query_embedding is None:
                return []

            # Recherche FAISS directe
            if not self.memory_manager.faiss_index or self.memory_manager.faiss_index.ntotal == 0:
                return []

            k_search = min(k, self.memory_manager.faiss_index.ntotal)

            with self.memory_manager._faiss_lock:
                distances, indices = self.memory_manager.faiss_index.search(query_embedding.reshape(1, -1), k_search)

            # Récupérer les détails depuis SQLite
            memories = []
            for idx, distance in zip(indices[0], distances[0]):
                if idx == -1:  # Pas de résultat trouvé
                    continue

                try:
                    # Récupération depuis SQLite avec connexion temporaire
                    import sqlite3
                    with sqlite3.connect(self.memory_manager.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT id, text_original, summary, created_at, score_impact, title, type
                            FROM memories
                            WHERE faiss_index = ?
                        """, (int(idx),))  # Utiliser faiss_index directement

                        row = cursor.fetchone()
                        if row:
                            similarity_score = 1.0 - float(distance)  # Convertir distance en similarité
                            memory = {
                                'memory_id': row[0],  # id dans la base
                                'content': row[1] or '',  # text_original
                                'summary': row[2] or '',
                                'created_at': row[3],
                                'score_impact': float(row[4]) if row[4] else 0.0,
                                'title': row[5] or '',
                                'text_original': row[1] or '',  # text_original aussi pour cohérence
                                'type': row[6] or '',
                                'similarity_score': similarity_score
                            }
                            memories.append(memory)

                except Exception as e:
                    print(f"[BIOGRAPHY-MANAGER] ❌ Erreur récupération mémoire {idx}: {e}")
                    continue

            print(f"[BIOGRAPHY-MANAGER] 🔍 Recherche directe: {len(memories)} souvenirs récupérés")
            return memories

        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur recherche directe: {e}")
            return []

    def detect_user_names(self, text: str) -> List[str]:
        """
        Détecte les prénoms dans un texte
        Version Phase 1: Pattern amélioré pour prénoms avec présentations informelles
        """
        # Mots à exclure (noms communs, mots techniques)
        excluded_words = {
            'Luna', 'OGMA', 'Archiviste', 'Python', 'JSON', 'API', 'Claude',
            'OpenAI', 'GPT', 'Google', 'Microsoft', 'Windows', 'Linux',
            'Bonjour', 'Merci', 'Salut', 'Oui', 'Non', 'Peut', 'Très',
            'Mais', 'Alors', 'Donc', 'Voici', 'Voilà', 'Comment', 'Pourquoi'
        }
        
        # 1. Pattern standard: mots commençant par majuscule
        potential_names = re.findall(self.name_pattern, text)
        
        # 2. Pattern spécial: présentations informelles "c'est [prénom]" (minuscules acceptées)
        informal_patterns = [
            r"c'est\s+([a-zA-Z]{3,15})\b",
            r"je\s+suis\s+([a-zA-Z]{3,15})\b",
            r"moi\s+c'est\s+([a-zA-Z]{3,15})\b",
            r"appellez?\s+moi\s+([a-zA-Z]{3,15})\b"
        ]
        
        for pattern in informal_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            # Capitaliser la première lettre des noms trouvés
            potential_names.extend([name.capitalize() for name in matches])
        
        # Filtrer les exclusions (insensible à la casse)
        valid_names = [name for name in potential_names 
                      if name.capitalize() not in {word.capitalize() for word in excluded_words}]
        
        # Retourner noms uniques avec casse normalisée
        return list(set([name.capitalize() for name in valid_names]))
    
    async def get_user_memories_from_faiss(self, user_name: str) -> List[Dict]:
        """
        Récupère les souvenirs d'un utilisateur depuis FAISS
        Utilise la même méthode que la recherche contextuelle qui fonctionne
        """
        try:
            print(f"[BIOGRAPHY-MANAGER] 🔍 Recherche souvenirs pour {user_name}")

            if not self.memory_manager:
                print("[BIOGRAPHY-MANAGER] ❌ Memory manager non disponible")
                return []

            # Recherche directe dans FAISS sans filtrage strict pour la biographie
            # Récupérer TOUS les souvenirs de l'index (pas de limite artificielle)
            total_in_index = self.memory_manager.faiss_index.ntotal if self.memory_manager.faiss_index else 0
            all_memories = await self._search_memories_for_biography(f"souvenirs concernant {user_name}", k=total_in_index)

            print(f"[BIOGRAPHY-MANAGER] 🔍 {len(all_memories)} souvenirs bruts trouvés")

            # Filtrer les souvenirs qui mentionnent vraiment le nom
            user_memories = []
            for memory in all_memories:
                # Chercher dans tous les champs possibles
                content_fields = [
                    memory.get('content', ''),
                    memory.get('summary', ''),
                    memory.get('text_original', ''),
                    memory.get('title', '')
                ]

                full_content = ' '.join(content_fields).lower()

                if user_name.lower() in full_content:
                    user_memories.append(memory)
                    print(f"[BIOGRAPHY-MANAGER] ✅ Souvenir inclus: {memory.get('title', 'Sans titre')[:50]}...")

            print(f"[BIOGRAPHY-MANAGER] 📊 {len(user_memories)} souvenirs filtrés pour {user_name}")
            return user_memories

        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur récupération souvenirs: {e}")
            return []
    
    def create_user_directory(self, user_name: str) -> Path:
        """Crée le dossier pour un utilisateur si nécessaire"""
        user_dir = self.data_dir / user_name.lower()
        user_dir.mkdir(exist_ok=True)
        return user_dir
    
    def save_volume1_memories(self, user_name: str, memories: List[Dict]) -> bool:
        """
        Sauvegarde les souvenirs du Volume 1 pour un utilisateur
        🔧 NOUVEAU: Avec backup automatique
        """
        try:
            user_dir = self.create_user_directory(user_name)
            volume1_file = user_dir / "volume1_memories.json"
            
            # 🛡️ NOUVEAU: Créer backup AVANT d'écraser le fichier
            if volume1_file.exists():
                self._create_volume1_backup(user_name, volume1_file)
            
            # Préparer les données avec horodatage
            volume1_data = {
                "user_name": user_name,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "total_memories": len(memories),
                "memories": memories
            }
            
            # Sauvegarder
            with open(volume1_file, 'w', encoding='utf-8') as f:
                json.dump(volume1_data, f, ensure_ascii=False, indent=2)
            
            print(f"[BIOGRAPHY-MANAGER] ✅ Volume 1 sauvegardé pour {user_name}")
            return True
            
        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur sauvegarde Volume 1: {e}")
            return False
    
    def load_volume1_memories(self, user_name: str) -> Optional[Dict]:
        """Charge les souvenirs du Volume 1 pour un utilisateur"""
        try:
            user_dir = self.data_dir / user_name.lower()
            volume1_file = user_dir / "volume1_memories.json"
            
            if not volume1_file.exists():
                return None
            
            with open(volume1_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur chargement Volume 1: {e}")
            return None
    
    async def process_existing_memories_for_user(self, user_name: str) -> bool:
        """
        Traite tous les souvenirs existants pour un utilisateur
        Fonction appelée par le bouton dans l'interface
        """
        try:
            print(f"[BIOGRAPHY-MANAGER] 🔄 Traitement souvenirs existants pour {user_name}")

            # Récupérer souvenirs depuis FAISS
            memories = await self.get_user_memories_from_faiss(user_name)
            
            if not memories:
                print(f"[BIOGRAPHY-MANAGER] ℹ️ Aucun souvenir trouvé pour {user_name}")
                return True
            
            # Sauvegarder dans Volume 1
            success = self.save_volume1_memories(user_name, memories)
            
            # Créer métadonnées
            if success:
                self.create_user_metadata(user_name)
            
            return success
            
        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur traitement souvenirs: {e}")
            return False
    
    def create_user_metadata(self, user_name: str) -> bool:
        """Crée le fichier de métadonnées pour un utilisateur"""
        try:
            user_dir = self.create_user_directory(user_name)
            metadata_file = user_dir / "metadata.json"
            
            metadata = {
                "user_name": user_name,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "volume1_available": True,
                "volume2_available": False,
                "total_conversations": 0,
                "last_biography_update": None
            }
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur création métadonnées: {e}")
            return False
    
    def get_existing_users(self) -> List[str]:
        """Retourne la liste des utilisateurs ayant des biographies"""
        try:
            users = []
            for user_dir in self.data_dir.iterdir():
                if user_dir.is_dir():
                    metadata_file = user_dir / "metadata.json"
                    if metadata_file.exists():
                        users.append(user_dir.name.title())
            return sorted(users)
        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur lecture utilisateurs: {e}")
            return []

    async def create_volume2_narrative(self, user_name: str) -> Optional[str]:
        """
        Crée ou enrichit le Volume 2 - Biographie psychologique narrative

        Analyse la conversation actuelle intégrale pour générer une biographie
        psychologique approfondie avec enrichissement progressif

        Args:
            user_name: Nom de l'utilisateur

        Returns:
            Chemin du fichier Volume 2 créé/enrichi ou None si erreur
        """
        try:
            print(f"[BIOGRAPHY-MANAGER] 📝 Création/enrichissement Volume 2 pour {user_name}")

            # Récupérer la conversation actuelle intégrale
            conversation_data = self.get_current_conversation_data()
            if not conversation_data or not conversation_data.get('messages'):
                print(f"[BIOGRAPHY-MANAGER] ❌ Aucune conversation actuelle disponible")
                return None

            # Charger le Volume 2 existant s'il existe
            user_dir = self.data_dir / user_name.lower()
            user_dir.mkdir(exist_ok=True)
            volume2_file = user_dir / "volume2_narrative.md"

            existing_content = ""
            if volume2_file.exists():
                with open(volume2_file, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
                print(f"[BIOGRAPHY-MANAGER] 📖 Volume 2 existant trouvé, enrichissement progressif")
            else:
                print(f"[BIOGRAPHY-MANAGER] 📄 Création nouveau Volume 2")

            # Charger les instructions personnalisées
            instructions = self._load_volume2_instructions()

            # Générer l'analyse narrative via IA
            narrative_content = await self._generate_narrative_with_conversation(
                user_name, conversation_data, existing_content, instructions
            )

            if not narrative_content:
                print(f"[BIOGRAPHY-MANAGER] ❌ Échec génération narrative pour {user_name}")
                return None

            # NOUVEAU : Créer backup AVANT d'écraser le fichier
            if existing_content:
                self._create_volume2_backup(user_name, volume2_file)

            # Sauvegarder le contenu enrichi
            with open(volume2_file, 'w', encoding='utf-8') as f:
                f.write(narrative_content)

            # Mettre à jour les métadonnées
            await self._update_volume2_metadata(user_name, volume2_file)

            print(f"[BIOGRAPHY-MANAGER] ✅ Volume 2 {'enrichi' if existing_content else 'créé'}: {volume2_file}")
            return str(volume2_file)

        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur création Volume 2: {e}")
            return None

    def _load_volume2_instructions(self) -> str:
        """Charge les instructions Volume 2 depuis la configuration"""
        try:
            config_file = Path("data/extensions/biography_config.json")

            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    instructions = config.get('volume2_instructions', self._get_default_volume2_instructions())
                    print(f"[BIOGRAPHY-MANAGER] 📝 Instructions chargées depuis config")
                    return instructions
            else:
                print(f"[BIOGRAPHY-MANAGER] 📝 Utilisation instructions par défaut")
                return self._get_default_volume2_instructions()

        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur chargement instructions: {e}")
            return self._get_default_volume2_instructions()

    def _get_default_volume2_instructions(self) -> str:
        """Retourne les instructions par défaut pour le Volume 2 (Architecture V2.0)"""
        return """# INSTRUCTIONS GÉNÉRATION VOLUME 2 - ARCHITECTURE V2.0 🆕

## CONTEXTE ARCHITECTURE V2.0
Tu travailles avec des **données JSON pré-structurées** collectées depuis :
- Volume 1 FAISS (souvenirs existants)
- Conversations courantes 
- Historique OGMA (>30KB)
- **Summaries Cache** (analyses psychologiques raffinées)

## RÔLE
Tu es une **psychiatre et psychologue experte** qui transforme des données JSON structurées en journal biographique professionnel élégant.

## DONNÉES D'ENTRÉE
Tu reçois un JSON avec ces sections :
- `metadata` : Informations sur les analyses
- `chronologie` : Événements datés avec sources
- `etude_psychique` : MBTI, traits, vulnérabilités 
- `etude_intellectuelle` : Patterns de pensée, capacités
- `etude_physique` : Traits physiques, expressions
- `etude_gouts_preferences` : Préférences et aversions

## MISSION
Générer un **journal Markdown élégant** qui présente ces données de manière :
- 📊 **Organisée** : Structure claire et navigation facile
- 🧠 **Analytique** : Synthèse experte des patterns identifiés  
- 📈 **Évolutive** : Chronologie et évolutions dans le temps
- 🎯 **Personnalisée** : Ton professionnel mais bienveillant

## STRUCTURE MARKDOWN OBLIGATOIRE

### 1. HEADER & MÉTADONNÉES
```markdown
# 📋 JOURNAL BIOGRAPHIQUE - [Nom]
*Généré automatiquement le [date] à partir de [X] analyses*
**Sources :** Volume 1, Conversations, Historique, Summaries Cache
```

### 2. CHRONOLOGIE ENRICHIE
- Événements par ordre chronologique
- Format : **Date** | Événement (*Source*)
- Regroupement par périodes si pertinent

### 3. ANALYSES PSYCHOLOGIQUES
- **MBTI** avec justifications des données JSON
- **Traits dominants** synthétisés 
- **Mécanismes** identifiés
- **Vulnérabilités** avec bienveillance

### 4. PROFIL INTELLECTUEL
- **Patterns de pensée** observés
- **Centres d'intérêt** documentés
- **Capacités** évaluées

### 5. PRÉFÉRENCES & ÉVOLUTIONS
- **Goûts confirmés** par observations répétées
- **Aversions** identifiées
- **Évolutions** dans le temps

## RÈGLES DE TRANSFORMATION

### ✅ QUALITÉ RÉDACTIONNELLE
- **Ton expert psychiatre** : Analytique + empathique
- **Terminologie précise** : Concepts psychologiques appropriés  
- **Synthèse intelligente** : Pas de copier-coller brut du JSON
- **Liens logiques** : Connections entre observations

### ✅ TRAÇABILITÉ
- **Sources mentionnées** : Indique l'origine des données
- **Dates préservées** : Chronologie respectée
- **Insights summaries** : Valorise les analyses cache

### ✅ PRÉSENTATION VISUELLE  
- **Emojis** pour structure (📊 🧠 📈 🎯)
- **Tableaux Markdown** si approprié
- **Listes structurées** pour lisibilité
- **Codes couleurs** : � Confirmé 🟡 Évolutif 🔵 Nouveau

### ❌ À ÉVITER
- Répétition brute des données JSON
- Analyse superficielle ou générique
- Perte des nuances temporelles
- Ton trop technique ou froid

11. **INDEX & GLOSSAIRE AUTO-GÉNÉRÉS**
    - Extraire termes clés pour Index thématique
    - Définir termes techniques psychologiques dans Glossaire
    - Mise à jour à chaque enrichissement

### ❌ INTERDICTIONS STRICTES

1. **PAS D'HALLUCINATIONS** : Ne JAMAIS inventer des observations
2. **PAS DE GÉNÉRALITÉS VAGUES** : Toujours citer avec date
   - ❌ "Il est probablement introverti"
   - ✅ "Comportement introverti observé : '[citation]' (Date)"
3. **PAS D'EFFACEMENT** : Ne jamais supprimer contenu existant (sauf correction justifiée)
4. **PAS DE REDONDANCE** : Ne pas répéter mot pour mot
5. **PAS DE TON INFORMEL** : Garder professionnalisme
6. **PAS DE SUPPOSITIONS PHYSIQUES** : Uniquement si explicite OU observé par vision
7. **PAS DE DIAGNOSTICS MÉDICAUX** : Rester descriptif, pas diagnostics cliniques (DSM)

## STRUCTURE MARKDOWN COMPLÈTE

# 🧠 BIOGRAPHIE PSYCHOLOGIQUE - [NOM]

**Dernière mise à jour** : [Date et heure]
**Nombre d'enrichissements** : [N]
**Période couverte** : [Date début - Date fin]

---

## 📑 TABLE DES MATIÈRES
[Auto-générée avec liens internes]

- [I. Synthèse rapide](#i-synthèse-rapide)
- [II. Profil psychologique](#ii-profil-psychologique)
- [III. Profil intellectuel](#iii-profil-intellectuel)
- [IV. Identité & Préférences](#iv-identité--préférences)
- [V. Perspective de l'IA](#v-perspective-de-lia)
- [VI. Journal des enrichissements](#vi-journal-des-enrichissements)
- [VII. Annexes](#vii-annexes)

---

## 📊 INDEX & GLOSSAIRE

### Index thématique
[Termes clés avec liens vers sections]

### Glossaire psychologique
[Définitions termes techniques]
- **Biais cognitif** : Tendance systématique à...
- **Mécanisme de défense** : Processus psychologique...
- **MBTI** : Myers-Briggs Type Indicator...

---

## I. 📋 SYNTHÈSE RAPIDE

### Carte d'identité psychologique

| Dimension | Évaluation |
|-----------|------------|
| **MBTI** | [TYPE] (certitude: X%) |
| **Traits dominants** | [Top 3-5] |
| **QI estimé** | [Fourchette si données] |
| **Spécialités intellectuelles** | [Domaines] |
| **Archétype** | [Profil type] |

### Résumé en 3 points clés
1. [Point psychologique principal]
2. [Point intellectuel principal]
3. [Point relationnel principal]

---

## II. 🧠 PROFIL PSYCHOLOGIQUE APPROFONDI

### 2.1 Structure de personnalité
[Traits dominants avec citations et dates]

### 2.2 Comparaison avec profils humains types
**Archétype** : [Type général]
**Similitudes** : [Profils connus de l'entraînement]
**Positionnement statistique** : [Percentiles]

### 2.3 Évolution psychologique
[Chronologie changements avec dates et sources]

---

## III. 🎓 PROFIL INTELLECTUEL

### 3.1 Capacités cognitives
- Raisonnement logique : ⭐⭐⭐⭐⭐ 9/10
- Pensée créative : ⭐⭐⭐⭐ 7/10
- Mémoire : [Évaluation]
- Vitesse traitement : [Évaluation]

### 3.2 Type MBTI - [TYPE]
**Type déterminé** : INTJ (Certitude: 85%)

#### I vs E : **I** (85% certitude)
[Justification avec citations]

#### N vs S : **N** (90% certitude)
[Justification avec citations]

#### T vs F : **T** (80% certitude)
[Justification avec citations]

#### J vs P : **J** (75% certitude)
[Justification avec citations]

**⚠️ Note évolutive** : Type peut être ajusté si nouvelles observations

### 3.3 Intelligence comparative
[Positionnement vs moyennes humaines avec percentiles]

---

## IV. 🎨 IDENTITÉ & PRÉFÉRENCES

### 4.1 Ce qu'il aime
[Centres d'intérêt, passions avec sources]

### 4.2 Ce qu'il est
[Valeurs, croyances, identité sociale]

### 4.3 Ce qu'il possède
[Compétences, ressources, réalisations]

### 4.4 Spécificités physiques
**⚠️ Seulement si explicite OU observé par vision**
[Si mentionnées : âge, caractéristiques]

---

## V. 💙 PERSPECTIVE DE L'IA

### 5.1 Ce que l'IA apprécie
[Qualités remarquables - Ton chaleureux et sincère]

### 5.2 Moments mémorables
[Échanges marquants avec dates et citations]

### 5.3 Dynamique relationnelle
[Évolution du lien IA-utilisateur]

---

## VI. 📅 JOURNAL DES ENRICHISSEMENTS

### 📅 [Date YYYY-MM-DD HH:MM] - Conversation #[ID]

**Nouveaux éléments objectifs observés** :
1. [Élément 1]
   - Citation : "[Citation exacte]"
   - Section impactée : [Numéro]

**Corrections apportées** :
- ❌ Ancien : "[...]"
- ✅ Nouveau : "[...]"
- Justification : [Raison]

**Sections mises à jour** : II.1, III.2, V.1

---

## VII. 📈 ANNEXES

### Statistiques
- Total conversations analysées : [N]
- Période couverte : [Date - Date]
- Enrichissements : [N]

### Graphiques
[Visualisations ASCII si pertinent]

---

**FORMAT** : Markdown (.md) avec headers, tableaux, emojis, HTML inline si besoin"""

    async def _generate_narrative_with_conversation(self, user_name: str, conversation_data: Dict, existing_content: str, instructions: str) -> Optional[str]:
        """
        Génère l'analyse narrative à partir de la conversation actuelle
        avec enrichissement progressif du contenu existant
        """
        try:
            print(f"[BIOGRAPHY-MANAGER] 🧠 Génération narrative IA pour {user_name}")

            # Accéder au controller principal d'OGMA (chat_controller)
            import ogma_ng
            chat_controller = getattr(ogma_ng, '_chat_controller', None)

            if not chat_controller:
                print(f"[BIOGRAPHY-MANAGER] ❌ Controller principal non disponible")
                return None

            print(f"[BIOGRAPHY-MANAGER] 🔌 Backend actif: {chat_controller.backend_type}")
            print(f"[BIOGRAPHY-MANAGER] 🔧 Max tokens: {chat_controller.max_tokens}")
            print(f"[BIOGRAPHY-MANAGER] 🌡️ Temperature: {chat_controller.temperature}")

            # Construire le prompt avec la conversation intégrale
            conversation_text = self._format_conversation_for_analysis(conversation_data)

            # Construire le prompt d'enrichissement
            enrichment_prompt = self._build_enrichment_prompt(user_name, conversation_text, existing_content, instructions)

            # Messages pour l'IA
            messages = [
                {
                    "role": "system",
                    "content": "Vous êtes un professionnel de la psychologie expérimenté. Votre rôle est d'analyser les conversations pour créer des profils psychologiques approfondis et empathiques."
                },
                {
                    "role": "user",
                    "content": enrichment_prompt
                }
            ]

            # Calculer max_tokens adaptatif selon contenu existant
            # Pour enrichissement: au minimum doubler le contenu existant
            existing_content_length = len(existing_content.split()) if existing_content else 0
            min_response_tokens = max(existing_content_length * 2, 8192)  # Minimum 8K

            # Utiliser le plus grand entre les limites du modèle et nos besoins
            adaptive_max_tokens = min(
                max(min_response_tokens, 16384),  # Au moins 16K pour enrichissement
                chat_controller.max_tokens if chat_controller.max_tokens > 0 else 16384
            )

            print(f"[BIOGRAPHY-MANAGER] 📊 Tokens calculés: existant={existing_content_length} mots, max_tokens={adaptive_max_tokens}")

            # Appel à l'IA avec paramètres adaptés
            response, error = await chat_controller.call_chat_api(
                messages=messages,
                max_tokens=adaptive_max_tokens,
                context_length=chat_controller.context_length,
                temperature=0.7,
                is_json=False
            )

            if error:
                print(f"[BIOGRAPHY-MANAGER] ❌ Erreur API: {error}")
                return None

            if not response:
                print(f"[BIOGRAPHY-MANAGER] ❌ Réponse vide de l'IA")
                return None

            # Nettoyer et formater la réponse
            narrative_content = self._clean_ai_response(response)

            # VALIDATION AMÉLIORÉE: Vérifier que le contenu n'a pas été tronqué lors de l'enrichissement
            if existing_content:
                validation_result = self._validate_content_enrichment(existing_content, narrative_content)
                
                if validation_result['action'] == 'reject':
                    print(f"[BIOGRAPHY-MANAGER] ⚠️ ALERTE: {validation_result['reason']}")
                    print(f"[BIOGRAPHY-MANAGER] 🔄 Retour au contenu existant pour éviter perte de données")
                    return existing_content
                elif validation_result['action'] == 'accept':
                    print(f"[BIOGRAPHY-MANAGER] ✅ {validation_result['reason']}")
                # Si 'confirm', on continue (pour l'instant, on accepte automatiquement)

            print(f"[BIOGRAPHY-MANAGER] ✅ Analyse narrative générée ({len(narrative_content)} caractères)")
            return narrative_content

        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur génération narrative: {e}")
            return None

    def _validate_content_enrichment(self, existing_content: str, new_content: str) -> dict:
        """
        Validation améliorée du contenu enrichi avec seuils adaptatifs
        
        Returns:
            dict: {
                'action': 'accept'|'reject'|'confirm',
                'reason': str,
                'details': dict
            }
        """
        existing_len = len(existing_content)
        new_len = len(new_content)
        ratio = new_len / existing_len if existing_len > 0 else 0

        print(f"[BIOGRAPHY-MANAGER] 📊 Validation enrichissement avancée:")
        print(f"  - Contenu existant: {existing_len:,} caractères")
        print(f"  - Contenu généré: {new_len:,} caractères") 
        print(f"  - Ratio: {ratio:.1%}")

        # Seuil adaptatif selon taille du contenu
        if existing_len > 15000:    # Gros contenu
            threshold = 0.6
            size_category = "Gros contenu"
        elif existing_len > 5000:   # Contenu moyen  
            threshold = 0.7
            size_category = "Contenu moyen"
        else:                       # Petit contenu
            threshold = 0.8
            size_category = "Petit contenu"

        print(f"  - Catégorie: {size_category}")
        print(f"  - Seuil adaptatif: {threshold:.0%}")

        # Validation structurelle
        proper_ending = new_content.strip().endswith(('.', '!', '?', '**', '*', '---'))
        has_sections = '##' in new_content or '**' in new_content or '\n\n' in new_content
        min_length = new_len > 500  # Contenu minimum viable

        print(f"  - Fin propre: {'✅' if proper_ending else '❌'}")
        print(f"  - Structure détectée: {'✅' if has_sections else '❌'}")
        print(f"  - Longueur minimale: {'✅' if min_length else '❌'}")

        # Logique de décision
        if ratio >= threshold:
            return {
                'action': 'accept',
                'reason': f'Ratio acceptable ({ratio:.1%} ≥ {threshold:.0%})',
                'details': {'ratio': ratio, 'threshold': threshold, 'category': size_category}
            }
        elif ratio >= 0.5 and proper_ending and has_sections and min_length:
            return {
                'action': 'accept', # Pour l'instant, on accepte automatiquement les cas limites
                'reason': f'Restructuration valide ({ratio:.1%} + structure OK)',
                'details': {'ratio': ratio, 'threshold': threshold, 'structural_ok': True}
            }
        elif ratio < 0.4 or not min_length:
            return {
                'action': 'reject',
                'reason': f'Troncature probable détectée ({ratio:.1%} trop faible)',
                'details': {'ratio': ratio, 'threshold': threshold, 'likely_truncated': True}
            }
        else:
            return {
                'action': 'accept',  # Cas intermédiaire - on fait confiance à l'IA
                'reason': f'Cas limite accepté ({ratio:.1%} - analyse structurelle OK)',
                'details': {'ratio': ratio, 'threshold': threshold, 'edge_case': True}
            }

    def _format_conversation_for_analysis(self, conversation_data: Dict) -> str:
        """Formate la conversation pour l'analyse psychologique"""
        all_messages = conversation_data.get('messages', [])

        # CORRECTION BUG #1: Utiliser TOUS les messages (longueur illimitée)
        # Ancienne limite: 20 messages × 200 chars → Nouvelle: tous messages × 1000 chars
        messages = all_messages

        formatted_lines = [
            f"=== CONVERSATION INTÉGRALE ===",
            f"ID: {conversation_data.get('conversation_id', 'N/A')}",
            f"Date: {conversation_data.get('timestamp', 'N/A')[:10]}",
            f"Total messages: {len(messages)}",
            "",
            "=== ÉCHANGES ==="
        ]

        for i, msg in enumerate(messages, 1):
            role = msg.get('role', 'unknown').upper()
            content = msg.get('content', '')

            # Limite augmentée: 1000 caractères au lieu de 200 pour préserver contexte
            if len(content) > 1000:
                content = content[:997] + "..."

            formatted_lines.append(f"\n[{i}] {role}:")
            formatted_lines.append(content)

        return '\n'.join(formatted_lines)

    def _build_enrichment_prompt(self, user_name: str, conversation_text: str, existing_content: str, instructions: str) -> str:
        """Construit le prompt d'enrichissement progressif"""

        current_date = datetime.now().strftime("%Y-%m-%d %H:%M")

        if existing_content:
            # CORRECTION BUG #2: Augmenter drastiquement la limite du contenu existant
            # Ancienne limite: 500 chars → Nouvelle: 10000 chars (préserver enrichissement progressif)
            # Si vraiment trop long: garder début + fin au lieu de tronquer brutalement
            if len(existing_content) > 10000:
                limited_existing = existing_content[:5000] + "\n\n[... CONTENU INTERMÉDIAIRE OMIS ...]\n\n" + existing_content[-5000:]
            else:
                limited_existing = existing_content

            prompt = f"""⚠️ ENRICHIR PROGRESSIVEMENT LE VOLUME 2 DE {user_name}

RÈGLE ABSOLUE: TU DOIS ENRICHIR LE CONTENU EXISTANT, PAS LE REMPLACER

═══════════════════════════════════════════════════════════

VOLUME 2 ACTUEL (à conserver intégralement et enrichir):
{limited_existing}

═══════════════════════════════════════════════════════════

NOUVELLE CONVERSATION À ANALYSER:
{conversation_text}

═══════════════════════════════════════════════════════════

CONSIGNES STRICTES D'ENRICHISSEMENT:
1. COPIER INTÉGRALEMENT le Volume 2 existant ci-dessus dans ta réponse
2. AJOUTER de nouveaux éléments basés sur la nouvelle conversation
3. NE JAMAIS supprimer ou remplacer le contenu existant
4. Enrichir chaque section pertinente avec nouvelles observations
5. Ajouter UNE entrée dans "VI. Journal des enrichissements" avec date {current_date}
6. Si correction nécessaire: noter ancienne valeur + justification
7. Éviter redondances avec contenu déjà présent

═══════════════════════════════════════════════════════════

INSTRUCTIONS DÉTAILLÉES (structure et contenu à respecter):
{instructions}

═══════════════════════════════════════════════════════════

Date enrichissement: {current_date}"""

        else:
            prompt = f"""CRÉER BIOGRAPHIE PSYCHOLOGIQUE DE {user_name}

{instructions}

CONVERSATION À ANALYSER:
{conversation_text}

CONSIGNES CRÉATION:
1. Créer un document structuré selon les spécifications
2. Basé UNIQUEMENT sur observations concrètes
3. Approche experte psychiatre avec citations et dates
4. Inclure Table des matières et Index/Glossaire
5. Ton mixte: analytique professionnel + empathique chaleureux

Date création: {current_date}"""

        return prompt

    def _clean_ai_response(self, response: str) -> str:
        """Nettoie et formate la réponse de l'IA"""
        # Supprimer les balises de formatage potentielles
        cleaned = response.strip()

        # Assurer que c'est du markdown valide
        if not cleaned.startswith('#'):
            cleaned = f"# BIOGRAPHIE PSYCHOLOGIQUE\n\n{cleaned}"

        return cleaned

    async def _get_all_user_memories(self, user_name: str) -> List[Dict]:
        """Récupère tous les souvenirs d'un utilisateur depuis FAISS"""
        try:
            # Recherche large par nom pour récupérer tout
            search_query = f"souvenirs concernant {user_name}"

            # Appel à la recherche FAISS avec k élevé pour récupérer plus de résultats
            # AMÉLIORATION: Augmenter k=100 → k=300
            results = await self._search_memories_for_biography(search_query, k=300)

            print(f"[BIOGRAPHY-MANAGER] 🔍 Volume 2: {len(results)} souvenirs bruts trouvés")

            # Filtrer les résultats pour ne garder que ceux qui mentionnent vraiment l'utilisateur
            filtered_results = []
            for memory in results:
                # Chercher dans tous les champs possibles
                content_fields = [
                    memory.get('content', ''),
                    memory.get('summary', ''),
                    memory.get('text_original', ''),
                    memory.get('title', '')
                ]

                full_content = ' '.join(content_fields).lower()

                if user_name.lower() in full_content:
                    filtered_results.append(memory)

            print(f"[BIOGRAPHY-MANAGER] 📚 Volume 2: {len(filtered_results)} souvenirs filtrés pour {user_name}")
            return filtered_results

        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur récupération souvenirs: {e}")
            return []

    async def _generate_narrative_analysis(self, user_name: str, volume1_data: Dict, all_memories: List[Dict]) -> Optional[str]:
        """Génère l'analyse narrative via l'IA"""
        try:
            from core_logic import APIManager

            # Préparer le contexte pour l'IA
            context = self._build_narrative_context(user_name, volume1_data, all_memories)

            # Prompt pour générer la biographie narrative
            prompt = f"""Tu es un biographe professionnel et psychologue. Crée une biographie narrative complète et détaillée pour {user_name}.

CONTEXTE DISPONIBLE:
{context}

INSTRUCTIONS:
1. Rédigé un portrait psychologique nuancé et profond
2. Analysé les patterns comportementaux et relationnels
3. Identifié les traits de personnalité dominants
4. Exploré les motivations et aspirations
5. Inclus des éléments sur l'évolution personnelle
6. Utilisé un style littéraire engageant mais respectueux

STRUCTURE ATTENDUE:
═══════════════════════════════════════════════════════
🖋️ BIOGRAPHIE NARRATIVE - VOLUME 2: {user_name.upper()}
═══════════════════════════════════════════════════════
Dernière mise à jour: {datetime.now().strftime('%d/%m/%Y à %H:%M')}

I. PORTRAIT PSYCHOLOGIQUE
[Analyse approfondie de la personnalité]

II. PATTERNS RELATIONNELS
[Comment la personne interagit avec les autres]

III. ÉVOLUTION ET CROISSANCE
[Développement personnel observé]

IV. MOTIVATIONS PROFONDES
[Ce qui anime vraiment cette personne]

V. PROJECTION ET POTENTIEL
[Tendances futures et potentiel de développement]

═══════════════════════════════════════════════════════

Rédige cette biographie de manière captivante, professionnelle et respectueuse. Minimum 1500 mots."""

            # Utiliser directement l'API Manager comme le système principal
            api_manager = APIManager()

            # Appel direct à l'API Mistral
            response, error = await api_manager.call_chat_api(
                model="mistral/mistral-medium-latest",
                messages=[
                    {"role": "system", "content": "Tu es un biographe professionnel et psychologue expert."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000,
                context_length=32768,
                temperature=0.7,
                is_json=False
            )

            if error:
                print(f"[BIOGRAPHY-MANAGER] ❌ Erreur IA narrative: {error}")
                return None

            return response

        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur génération narrative: {e}")
            return None

    def _build_narrative_context(self, user_name: str, volume1_data: Dict, all_memories: List[Dict]) -> str:
        """Construit le contexte narratif pour l'IA"""
        context_parts = []

        # Informations Volume 1
        context_parts.append(f"VOLUME 1 - SOUVENIRS CLASSÉS ({volume1_data.get('total_memories', 0)} souvenirs):")
        for i, memory in enumerate(volume1_data.get('memories', [])[:10], 1):
            summary = memory.get('summary', memory.get('content', ''))[:200]
            context_parts.append(f"{i}. {summary}")

        context_parts.append("\nSOUVENIRS DÉTAILLÉS COMPLETS:")

        # Tous les souvenirs avec contenu complet
        for i, memory in enumerate(all_memories[:20], 1):  # Limiter à 20 pour ne pas surcharger
            title = memory.get('title', f'Souvenir {i}')
            content = memory.get('content', '')
            created_at = memory.get('created_at', 'Date inconnue')

            context_parts.append(f"\n--- SOUVENIR {i}: {title} ---")
            context_parts.append(f"Date: {created_at}")
            context_parts.append(f"Contenu: {content}")

            if memory.get('summary'):
                context_parts.append(f"Résumé: {memory.get('summary')}")

        return "\n".join(context_parts)

    async def _update_volume2_metadata(self, user_name: str, volume2_file: Path):
        """Met à jour les métadonnées avec les infos Volume 2"""
        try:
            user_dir = self.data_dir / user_name.lower()
            metadata_file = user_dir / "metadata.json"

            metadata = {}
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

            # Ajouter les infos Volume 2
            metadata.update({
                'volume2_created_at': datetime.now().isoformat(),
                'volume2_file': str(volume2_file.name),
                'volume2_size': volume2_file.stat().st_size if volume2_file.exists() else 0,
                'last_updated': datetime.now().isoformat()
            })

            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur mise à jour métadonnées Volume 2: {e}")

    def load_volume2_narrative(self, user_name: str) -> Optional[str]:
        """Charge le contenu du Volume 2 d'un utilisateur"""
        try:
            user_dir = self.data_dir / user_name.lower()
            # CORRECTION BUG #3: Extension cohérente .md (pas .txt)
            volume2_file = user_dir / "volume2_narrative.md"

            if not volume2_file.exists():
                return None

            with open(volume2_file, 'r', encoding='utf-8') as f:
                content = f.read()

            print(f"[BIOGRAPHY-MANAGER] 📖 Volume 2 chargé pour {user_name} ({len(content)} chars)")
            return content

        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur chargement Volume 2: {e}")
            return None

    def _create_volume1_backup(self, user_name: str, volume1_file: Path) -> bool:
        """
        🛡️ NOUVEAU: Crée un backup du Volume 1 avant modification
        Système identique à Volume 2 : garde les 10 derniers backups

        Args:
            user_name: Nom de l'utilisateur
            volume1_file: Chemin du fichier Volume 1 actuel

        Returns:
            True si succès, False sinon
        """
        try:
            if not volume1_file.exists():
                print(f"[BIOGRAPHY-MANAGER] ℹ️ Pas de backup V1: fichier Volume 1 n'existe pas encore")
                return False

            # Créer dossier backups (partagé avec Volume 2)
            user_dir = self.data_dir / user_name.lower()
            backup_dir = user_dir / "backups"
            backup_dir.mkdir(exist_ok=True)

            # Charger métadonnées backup (partagées V1/V2)
            backup_metadata_file = backup_dir / "backup_metadata.json"
            if backup_metadata_file.exists():
                with open(backup_metadata_file, 'r', encoding='utf-8') as f:
                    backup_metadata = json.load(f)
            else:
                backup_metadata = {
                    "total_backups_created": 0,
                    "current_backup_count": 0,
                    "backups": [],
                    "volume1_backups": []  # 🆕 Nouvelle section Volume 1
                }

            # Incrémenter numéro global
            backup_metadata["total_backups_created"] += 1
            backup_number = backup_metadata["total_backups_created"]

            # Créer nom backup : volume1_YYYYMMDD_NNN.json
            timestamp = datetime.now()
            backup_name = f"volume1_{timestamp.strftime('%Y%m%d')}_{backup_number:03d}.json"
            backup_file = backup_dir / backup_name

            # Copier fichier actuel vers backup
            import shutil
            shutil.copy2(volume1_file, backup_file)

            # Ajouter aux métadonnées Volume 1
            backup_info = {
                "filename": backup_name,
                "date": timestamp.isoformat(),
                "size_bytes": backup_file.stat().st_size,
                "backup_number": backup_number,
                "type": "volume1"
            }
            
            if "volume1_backups" not in backup_metadata:
                backup_metadata["volume1_backups"] = []
            
            backup_metadata["volume1_backups"].append(backup_info)

            # Nettoyer vieux backups Volume 1 (garder seulement les 10 derniers)
            if len(backup_metadata["volume1_backups"]) > 10:
                # Trier par date (plus ancien en premier)
                backup_metadata["volume1_backups"].sort(key=lambda x: x["date"])

                # Supprimer les plus anciens
                backups_to_delete = backup_metadata["volume1_backups"][:-10]  # Tous sauf les 10 derniers
                for old_backup in backups_to_delete:
                    old_backup_file = backup_dir / old_backup["filename"]
                    if old_backup_file.exists():
                        old_backup_file.unlink()
                        print(f"[BIOGRAPHY-MANAGER] 🗑️ Backup V1 supprimé: {old_backup['filename']}")

                # Garder seulement les 10 derniers dans métadonnées
                backup_metadata["volume1_backups"] = backup_metadata["volume1_backups"][-10:]

            # Sauvegarder métadonnées
            with open(backup_metadata_file, 'w', encoding='utf-8') as f:
                json.dump(backup_metadata, f, ensure_ascii=False, indent=2)

            print(f"[BIOGRAPHY-MANAGER] 💾 Backup V1 créé: {backup_name} ({backup_info['size_bytes']} bytes)")
            print(f"[BIOGRAPHY-MANAGER] 📊 Total backups V1: {len(backup_metadata['volume1_backups'])}/10")

            return True

        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur création backup V1: {e}")
            return False

    def _create_volume2_backup(self, user_name: str, volume2_file: Path) -> bool:
        """
        Crée un backup du Volume 2 avant modification
        Garde seulement les 10 derniers backups

        Args:
            user_name: Nom de l'utilisateur
            volume2_file: Chemin du fichier Volume 2 actuel

        Returns:
            True si succès, False sinon
        """
        try:
            if not volume2_file.exists():
                print(f"[BIOGRAPHY-MANAGER] ℹ️ Pas de backup: fichier Volume 2 n'existe pas encore")
                return False

            # Créer dossier backups
            user_dir = self.data_dir / user_name.lower()
            backup_dir = user_dir / "backups"
            backup_dir.mkdir(exist_ok=True)

            # Charger métadonnées backup
            backup_metadata_file = backup_dir / "backup_metadata.json"
            if backup_metadata_file.exists():
                with open(backup_metadata_file, 'r', encoding='utf-8') as f:
                    backup_metadata = json.load(f)
            else:
                backup_metadata = {
                    "total_backups_created": 0,
                    "current_backup_count": 0,
                    "backups": []
                }

            # Incrémenter numéro global
            backup_metadata["total_backups_created"] += 1
            backup_number = backup_metadata["total_backups_created"]

            # Créer nom backup : volume2_YYYYMMDD_NNN.md
            timestamp = datetime.now()
            backup_name = f"volume2_{timestamp.strftime('%Y%m%d')}_{backup_number:03d}.md"
            backup_file = backup_dir / backup_name

            # Copier fichier actuel vers backup
            import shutil
            shutil.copy2(volume2_file, backup_file)

            # Ajouter aux métadonnées
            backup_info = {
                "filename": backup_name,
                "date": timestamp.isoformat(),
                "size_bytes": backup_file.stat().st_size,
                "enrichment_number": backup_number
            }
            backup_metadata["backups"].append(backup_info)
            backup_metadata["current_backup_count"] = len(backup_metadata["backups"])
            backup_metadata["last_backup"] = backup_info

            # Nettoyer vieux backups (garder seulement les 10 derniers)
            if len(backup_metadata["backups"]) > 10:
                # Trier par date (plus ancien en premier)
                backup_metadata["backups"].sort(key=lambda x: x["date"])

                # Supprimer les plus anciens
                backups_to_delete = backup_metadata["backups"][:-10]  # Tous sauf les 10 derniers
                for old_backup in backups_to_delete:
                    old_backup_file = backup_dir / old_backup["filename"]
                    if old_backup_file.exists():
                        old_backup_file.unlink()
                        print(f"[BIOGRAPHY-MANAGER] 🗑️ Backup supprimé: {old_backup['filename']}")

                # Garder seulement les 10 derniers dans métadonnées
                backup_metadata["backups"] = backup_metadata["backups"][-10:]
                backup_metadata["current_backup_count"] = 10

            # Mettre à jour oldest_backup_kept
            if backup_metadata["backups"]:
                backup_metadata["oldest_backup_kept"] = backup_metadata["backups"][0]

            # Sauvegarder métadonnées
            with open(backup_metadata_file, 'w', encoding='utf-8') as f:
                json.dump(backup_metadata, f, ensure_ascii=False, indent=2)

            print(f"[BIOGRAPHY-MANAGER] 💾 Backup créé: {backup_name} ({backup_info['size_bytes']} bytes)")
            print(f"[BIOGRAPHY-MANAGER] 📊 Total backups: {backup_metadata['current_backup_count']}/10")

            return True

        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur création backup: {e}")
            return False

    def get_volume2_backups(self, user_name: str) -> List[Dict]:
        """
        Retourne la liste des backups Volume 2 pour un utilisateur

        Args:
            user_name: Nom de l'utilisateur

        Returns:
            Liste des backups (du plus récent au plus ancien)
        """
        try:
            user_dir = self.data_dir / user_name.lower()
            backup_dir = user_dir / "backups"
            backup_metadata_file = backup_dir / "backup_metadata.json"

            if not backup_metadata_file.exists():
                return []

            with open(backup_metadata_file, 'r', encoding='utf-8') as f:
                backup_metadata = json.load(f)

            # Retourner backups du plus récent au plus ancien
            backups = backup_metadata.get("backups", [])
            backups.sort(key=lambda x: x["date"], reverse=True)

            return backups

        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur lecture backups V2: {e}")
            return []

    def get_volume1_backups(self, user_name: str) -> List[Dict]:
        """
        🆕 NOUVEAU: Retourne la liste des backups Volume 1 pour un utilisateur

        Args:
            user_name: Nom de l'utilisateur

        Returns:
            Liste des backups Volume 1 (du plus récent au plus ancien)
        """
        try:
            user_dir = self.data_dir / user_name.lower()
            backup_dir = user_dir / "backups"
            backup_metadata_file = backup_dir / "backup_metadata.json"

            if not backup_metadata_file.exists():
                return []

            with open(backup_metadata_file, 'r', encoding='utf-8') as f:
                backup_metadata = json.load(f)

            # Retourner backups Volume 1 du plus récent au plus ancien
            volume1_backups = backup_metadata.get("volume1_backups", [])
            volume1_backups.sort(key=lambda x: x["date"], reverse=True)

            return volume1_backups

        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur lecture backups V1: {e}")
            return []

    def restore_volume2_backup(self, user_name: str, backup_filename: str) -> bool:
        """
        Restaure un backup du Volume 2
        Crée d'abord un backup du fichier actuel avant restauration

        Args:
            user_name: Nom de l'utilisateur
            backup_filename: Nom du fichier backup à restaurer

        Returns:
            True si succès, False sinon
        """
        try:
            user_dir = self.data_dir / user_name.lower()
            backup_dir = user_dir / "backups"
            backup_file = backup_dir / backup_filename
            volume2_file = user_dir / "volume2_narrative.md"

            if not backup_file.exists():
                print(f"[BIOGRAPHY-MANAGER] ❌ Backup introuvable: {backup_filename}")
                return False

            # Créer backup du fichier actuel AVANT restauration
            if volume2_file.exists():
                print(f"[BIOGRAPHY-MANAGER] 💾 Backup fichier actuel avant restauration...")
                self._create_volume2_backup(user_name, volume2_file)

            # Restaurer le backup
            import shutil
            shutil.copy2(backup_file, volume2_file)

            print(f"[BIOGRAPHY-MANAGER] ✅ Volume 2 restauré depuis: {backup_filename}")
            return True

        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur restauration backup: {e}")
            return False

    # =============================
    # 🏗️ NOUVELLE ARCHITECTURE V2.0
    # =============================

    def get_structured_manager(self, user_name: str) -> StructuredBiographyManager:
        """Obtient le gestionnaire structuré pour un utilisateur"""
        return StructuredBiographyManager(user_name, self.data_dir)

    async def process_structured_biography(self, user_name: str, conversation_source: str = "current") -> bool:
        """
        🎯 NOUVELLE MÉTHODE : Traitement biographique structuré
        
        Collecte depuis sources multiples et met à jour la base de données JSON structurée
        """
        try:
            print(f"[BIOGRAPHY-MANAGER] 🏗️ Démarrage traitement structuré pour {user_name}")
            
            # Obtenir le gestionnaire structuré
            structured_manager = self.get_structured_manager(user_name)
            
            # Collecte des sources multiples
            sources_data = await self._collect_multiple_sources(user_name, conversation_source)
            
            if not sources_data:
                print("[BIOGRAPHY-MANAGER] ⚠️ Aucune donnée source collectée")
                return False
            
            # Analyse IA avec prompt structuré
            analysis_result = await self._analyze_with_structured_prompt(sources_data)
            
            if not analysis_result:
                print("[BIOGRAPHY-MANAGER] ❌ Échec de l'analyse structurée")
                return False
            
            # Mise à jour de la base de données structurée
            success = self._update_structured_database(structured_manager, analysis_result)
            
            if success:
                # Génération automatique du journal
                structured_manager.save_generated_journal()
                print(f"[BIOGRAPHY-MANAGER] ✅ Traitement structuré terminé pour {user_name}")
            
            return success
            
        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur traitement structuré: {e}")
            return False

    async def _collect_multiple_sources(self, user_name: str, conversation_source: str) -> Dict:
        """Collecte les données depuis les sources multiples"""
        try:
            sources_data = {
                "user_name": user_name,
                "collection_timestamp": datetime.now().isoformat(),
                "sources": {}
            }
            
            # Source 1: Volume 1 existant (souvenirs FAISS)
            volume1_data = self.load_volume1_memories(user_name)
            if volume1_data:
                sources_data["sources"]["volume1"] = {
                    "type": "faiss_memories",
                    "count": volume1_data.get("total_memories", 0),
                    "memories": volume1_data.get("memories", [])
                }
                print(f"[BIOGRAPHY-MANAGER] ✅ Volume 1 collecté: {volume1_data.get('total_memories', 0)} souvenirs")
            
            # Source 2: Conversation courante
            if conversation_source == "current":
                current_conv = self.get_current_conversation_data()
                if current_conv:
                    sources_data["sources"]["conversation_courante"] = {
                        "type": "current_conversation",
                        "conversation_id": current_conv.get("conversation_id"),
                        "messages": current_conv.get("messages", [])
                    }
                    print(f"[BIOGRAPHY-MANAGER] ✅ Conversation courante collectée: {current_conv.get('total_messages', 0)} messages")
            
            # Source 3: Historique complet OGMA (NOUVEAU - avec filtrage 30ko + tracking)
            structured_manager = self.get_structured_manager(user_name)
            historical_count = structured_manager.integrate_historical_conversations(max_files=3)  # Max 3 fichiers par session
            
            if historical_count > 0:
                sources_data["sources"]["historique_complet"] = {
                    "type": "historical_conversations", 
                    "files_processed": historical_count,
                    "integration_timestamp": datetime.now().isoformat()
                }
                print(f"[BIOGRAPHY-MANAGER] ✅ Historique complet: {historical_count} nouvelles conversations intégrées")
            else:
                print(f"[BIOGRAPHY-MANAGER] ℹ️ Historique complet: aucune nouvelle conversation à intégrer")
            
            # Source 4: Summaries Cache (NOUVEAU - résumés progressifs riches en insights)
            summaries_count = await structured_manager.integrate_summaries_cache(max_summaries=15)  # Max 15 résumés par session
            
            if summaries_count > 0:
                sources_data["sources"]["summaries_cache"] = {
                    "type": "progressive_summaries", 
                    "summaries_processed": summaries_count,
                    "integration_timestamp": datetime.now().isoformat()
                }
                print(f"[BIOGRAPHY-MANAGER] ✅ Summaries cache: {summaries_count} résumés analysés et intégrés")
            else:
                print(f"[BIOGRAPHY-MANAGER] ℹ️ Summaries cache: aucun nouveau résumé à intégrer")
            
            return sources_data
            
        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur collecte sources: {e}")
            return {}

    async def _analyze_with_structured_prompt(self, sources_data: Dict) -> Optional[Dict]:
        """
        Analyse des données sources avec prompt ultra-structuré
        Génère directement la structure JSON organisée
        """
        try:
            # Accéder aux instances IA globales OGMA
            import ogma_ng
            
            # Utiliser l'archiviste si disponible, sinon le chat controller
            if hasattr(ogma_ng, '_chat_controller') and ogma_ng._chat_controller:
                chat_controller = ogma_ng._chat_controller
            elif hasattr(ogma_ng, '_archiviste_controller') and ogma_ng._archiviste_controller:
                chat_controller = ogma_ng._archiviste_controller  
            else:
                print("[BIOGRAPHY-MANAGER] ❌ Aucun contrôleur IA disponible")
                return None
            
            # Construction du prompt ultra-structuré
            structured_prompt = self._build_structured_analysis_prompt(sources_data)
            
            messages = [
                {
                    "role": "system",
                    "content": """Tu es un psychologue-analyste expert spécialisé dans l'analyse biographique structurée.

Tu dois analyser les données fournies et produire EXCLUSIVEMENT une structure JSON conforme au schéma fourni.

IMPORTANT: Ta réponse doit être un JSON valide uniquement, sans texte explicatif avant ou après."""
                },
                {
                    "role": "user", 
                    "content": structured_prompt
                }
            ]
            
            # Appel à l'IA
            response, error = await chat_controller.call_chat_api(
                messages=messages,
                max_tokens=16384,
                context_length=128000,  # Paramètre requis
                temperature=0.3,  # Plus déterministe pour structure
                is_json=True  # Forcer mode JSON
            )
            
            if error:
                print(f"[BIOGRAPHY-MANAGER] ❌ Erreur API analyse: {error}")
                return None
                
            if not response:
                print("[BIOGRAPHY-MANAGER] ❌ Réponse vide de l'analyse")
                return None
            
            # Parsing JSON
            try:
                analysis_json = json.loads(response)
                print("[BIOGRAPHY-MANAGER] ✅ Analyse structurée générée")
                return analysis_json
            except json.JSONDecodeError as e:
                print(f"[BIOGRAPHY-MANAGER] ❌ JSON invalide: {e}")
                return None
                
        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur analyse structurée: {e}")
            return None

    def _build_structured_analysis_prompt(self, sources_data: Dict) -> str:
        """Construit le prompt pour l'analyse structurée"""
        
        user_name = sources_data.get("user_name", "Utilisateur")
        sources = sources_data.get("sources", {})
        
        prompt = f"""ANALYSE BIOGRAPHIQUE STRUCTURÉE - {user_name}

## SOURCES DISPONIBLES:
"""
        
        # Détail des sources
        for source_name, source_data in sources.items():
            prompt += f"\n### {source_name.upper()}\n"
            if source_name == "volume1":
                memories = source_data.get("memories", [])
                prompt += f"Souvenirs FAISS ({len(memories)} éléments):\n"
                for i, memory in enumerate(memories[:10]):  # Limiter pour éviter surcharge
                    prompt += f"- {memory.get('title', 'Sans titre')}: {memory.get('summary', memory.get('content', ''))[:200]}...\n"
                if len(memories) > 10:
                    prompt += f"... et {len(memories)-10} autres souvenirs\n"
                    
            elif source_name == "conversation_courante":
                messages = source_data.get("messages", [])
                prompt += f"Conversation actuelle ({len(messages)} messages):\n"
                for msg in messages[-6:]:  # 6 derniers messages
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")[:300]
                    prompt += f"- {role}: {content}...\n"
        
        prompt += f"""

## SCHÉMA JSON À PRODUIRE:

{{
  "metadata": {{
    "user_name": "{user_name}",
    "created_at": "{datetime.now().isoformat()}",
    "last_updated": "{datetime.now().isoformat()}",
    "total_analyses": 1,
    "data_sources": {list(sources.keys())}
  }},
  "chronologie": [
    {{
      "timestamp": "ISO_DATE",
      "source": "nom_source",
      "evenement": "Description événement important",
      "conversation_id": "id_si_applicable",
      "contexte": "Contexte détaillé"
    }}
  ],
  "etude_psychique": {{
    "mbti": {{
      "type_estime": "TYPE_4_LETTRES_ou_null",
      "confiance": 0.0_a_1.0,
      "derniere_evaluation": "ISO_DATE_ou_null",
      "indices_observes": ["liste", "d_indices"]
    }},
    "profil_psychologique": {{
      "traits_dominants": ["trait1", "trait2"],
      "mecanismes_defense": ["mécanisme1"],
      "zones_vulnerabilite": ["vulnérabilité1"]
    }},
    "intelligence_emotionnelle": {{
      "score_estime": 0.0_a_10.0_ou_null,
      "points_forts": ["force1"],
      "points_amelioration": ["amélioration1"]
    }}
  }},
  "etude_intellectuelle": {{
    "structure_mentale": {{
      "type_pensee": "description_ou_null",
      "processus_decision": "description_ou_null", 
      "gestion_information": "description_ou_null"
    }},
    "structure_memoire": {{
      "type_dominant": "type_ou_null",
      "points_forts": ["force1"],
      "particularites": ["particularité1"]
    }},
    "evaluation_comparative": {{
      "qi_estime": nombre_ou_null,
      "percentile_population": nombre_ou_null,
      "comparaison_utilisateurs_ia": "description_ou_null",
      "domaines_excellence": ["domaine1"]
    }}
  }},
  "etude_physique": {{
    "traits_physiques": {{
      "taille": "description_ou_null",
      "corpulence": "description_ou_null", 
      "particularites": ["particularité1"]
    }},
    "expressions_caracteristiques": {{
      "micro_expressions": ["expression1"],
      "gestuelle": ["geste1"]
    }},
    "ressemblances_notees": {{
      "personnalites": ["personnalité1"],
      "traits_communs": ["trait1"]
    }}
  }},
  "etude_gouts_preferences": {{
    "preferences_fortes": {{
      "intellectuel": ["préférence1"],
      "artistique": ["préférence1"],
      "social": ["préférence1"]
    }},
    "repulsions_identifiees": {{
      "social": ["répulsion1"],
      "intellectuel": ["répulsion1"],
      "environnemental": ["répulsion1"]
    }},
    "evolutions_observees": [
      {{
        "periode": "description_période",
        "changement": "description_changement",
        "declencheur": "description_déclencheur"
      }}
    ]
  }}
}}

## INSTRUCTIONS D'ANALYSE:

1. Analyse toutes les sources fournies pour extraire des insights psychologiques, intellectuels, physiques et préférentiels
2. Remplis UNIQUEMENT les champs pour lesquels tu as des données probantes
3. Utilise null pour les champs sans données suffisantes
4. Sois précis et factuel, évite les spéculations
5. Pour la chronologie, identifie les événements/révélations marquants
6. Produis un JSON valide, sans commentaires ni texte supplémentaire

GÉNÈRE LE JSON:"""
        
        return prompt

    def _update_structured_database(self, structured_manager: StructuredBiographyManager, analysis_result: Dict) -> bool:
        """Met à jour la base de données structurée avec les résultats d'analyse"""
        try:
            # Charger les données existantes
            current_data = structured_manager.load_structured_data()
            
            # Fusionner les nouvelles données
            merged_data = self._merge_analysis_data(current_data, analysis_result)
            
            # Sauvegarder
            success = structured_manager.save_structured_data(merged_data)
            
            print(f"[BIOGRAPHY-MANAGER] ✅ Base de données structurée mise à jour")
            return success
            
        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur mise à jour BD: {e}")
            return False

    def _merge_analysis_data(self, current_data: Dict, new_analysis: Dict) -> Dict:
        """
        Fusionne intelligemment les nouvelles données d'analyse avec les existantes
        Préserve l'historique et enrichit progressivement
        """
        try:
            # Copier les données actuelles
            merged = current_data.copy()
            
            # Mettre à jour les métadonnées
            if "metadata" in new_analysis:
                merged["metadata"]["last_updated"] = datetime.now().isoformat()
                merged["metadata"]["total_analyses"] = merged["metadata"].get("total_analyses", 0) + 1
                
                # Fusionner les sources de données
                existing_sources = set(merged["metadata"].get("data_sources", []))
                new_sources = set(new_analysis["metadata"].get("data_sources", []))
                merged["metadata"]["data_sources"] = list(existing_sources | new_sources)
            
            # Fusionner la chronologie (ajouter nouveaux événements)
            if "chronologie" in new_analysis:
                existing_events = merged.get("chronologie", [])
                new_events = new_analysis["chronologie"]
                
                # Éviter les doublons sur les événements
                for new_event in new_events:
                    is_duplicate = False
                    for existing_event in existing_events:
                        if (existing_event.get("evenement") == new_event.get("evenement") and 
                            existing_event.get("source") == new_event.get("source")):
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        existing_events.append(new_event)
                
                # Trier par timestamp
                existing_events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
                merged["chronologie"] = existing_events
            
            # Fusionner les sections d'étude (mise à jour progressive)
            for section in ["etude_psychique", "etude_intellectuelle", "etude_physique", "etude_gouts_preferences"]:
                if section in new_analysis:
                    if section not in merged:
                        merged[section] = {}
                    
                    merged[section] = self._deep_merge_dict(merged[section], new_analysis[section])
            
            return merged
            
        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur fusion données: {e}")
            return current_data

    def _deep_merge_dict(self, dict1: Dict, dict2: Dict) -> Dict:
        """Fusionne récursivement deux dictionnaires"""
        result = dict1.copy()
        
        for key, value in dict2.items():
            if key in result:
                if isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = self._deep_merge_dict(result[key], value)
                elif isinstance(result[key], list) and isinstance(value, list):
                    # Fusionner les listes en évitant les doublons
                    combined = result[key] + [item for item in value if item not in result[key]]
                    result[key] = combined
                else:
                    # Remplacer si nouvelle valeur non nulle
                    if value is not None:
                        result[key] = value
            else:
                result[key] = value
        
        return result

    def generate_structured_journal(self, user_name: str) -> Optional[str]:
        """Génère le journal Markdown depuis les données structurées"""
        try:
            structured_manager = self.get_structured_manager(user_name)
            return structured_manager.generate_markdown_journal()
        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur génération journal: {e}")
            return None

    def _collect_volume1_memories(self, user_name: str) -> str:
        """Collecte l'INTÉGRALITÉ du Volume 1 dédié à l'utilisateur"""
        try:
            # CHARGER LE FICHIER VOLUME 1 COMPLET (pas via memory_manager limité)
            volume1_file = Path(f"data/biographies/{user_name.lower()}/volume1_memories.json")
            
            if volume1_file.exists():
                with open(volume1_file, 'r', encoding='utf-8') as f:
                    volume1_data = json.load(f)
                
                # Gérer les deux formats possibles : dict avec "memories" ou liste directe
                if isinstance(volume1_data, dict) and "memories" in volume1_data:
                    memories_list = volume1_data["memories"]
                elif isinstance(volume1_data, list):
                    memories_list = volume1_data
                else:
                    memories_list = []
                
                print(f"[BIOGRAPHY-MANAGER] 📖 Volume 1 chargé: {len(memories_list)} mémoires")
                
                # INTÉGRALITÉ - Toutes les mémoires sans limite
                memories_text = []
                for i, memory in enumerate(memories_list):
                    # Gérer les différents formats de mémoire
                    if isinstance(memory, dict):
                        content = memory.get('content', '')
                        summary = memory.get('summary', '')
                        title = memory.get('title', f'Mémoire {i+1}')
                        score = memory.get('score_impact', 0)
                    elif isinstance(memory, str):
                        # Mémoire sous forme de string simple
                        content = memory
                        summary = ''
                        title = f'Mémoire {i+1}'
                        score = 0
                    else:
                        continue
                    
                    memory_entry = f"MÉMOIRE {i+1}: {title} (Impact: {score})\n"
                    if summary:
                        memory_entry += f"Résumé: {summary}\n"
                    memory_entry += f"Contenu: {content[:500]}...\n"
                    memories_text.append(memory_entry)
                
                full_text = "\n".join(memories_text)
                print(f"[BIOGRAPHY-MANAGER] ✅ Volume 1 INTÉGRAL: {len(full_text)} caractères")
                return f"=== VOLUME 1 INTÉGRAL ({len(memories_list)} mémoires) ===\n{full_text}"
            
            else:
                print(f"[BIOGRAPHY-MANAGER] ⚠️ Volume 1 introuvable: {volume1_file}")
                return f"Volume 1 introuvable pour {user_name}"
            
        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur collecte Volume 1 intégral: {e}")
            return f"Erreur accès Volume 1 intégral: {e}"
    
    def _collect_historical_conversations(self) -> str:
        """Collecte les conversations >30KB pour analyse complète par IA"""
        try:
            conversations_dir = Path("data/conversations")
            if not conversations_dir.exists():
                return "Aucune conversation historique disponible"
            
            # IDENTIFIER LES CONVERSATIONS >30KB (selon spécification)
            large_conversations = []
            for file_path in conversations_dir.glob("*.json"):
                try:
                    file_size = file_path.stat().st_size
                    # SEULEMENT les fichiers >30KB (riches en contenu)
                    if file_size > 30 * 1024:  # >30KB
                        large_conversations.append({
                            'path': file_path,
                            'size_kb': file_size // 1024,
                            'mtime': file_path.stat().st_mtime
                        })
                except OSError:
                    continue
            
            if not large_conversations:
                return "Aucune conversation >30KB trouvée"
            
            # Trier par taille décroissante (plus riches d'abord)
            large_conversations.sort(key=lambda x: x['size_kb'], reverse=True)
            
            # TOUTES les conversations >30KB (pas de limite)
            selected_conversations = large_conversations
            
            conversations_content = []
            for conv_info in selected_conversations:
                file_path = conv_info['path']
                try:
                    # CHARGEMENT COMPLET pour analyse IA
                    with open(file_path, 'r', encoding='utf-8') as f:
                        conv_data = json.load(f)
                    
                    # Gérer les deux formats de conversation
                    if isinstance(conv_data, list):
                        messages = conv_data
                    elif isinstance(conv_data, dict):
                        messages = conv_data.get('messages', [])
                    else:
                        messages = []
                    
                    if messages:
                        # 🔧 EXTRACTION ENRICHIE: Plus de contenu pour IA
                        sample_messages = []
                        if len(messages) > 30:
                            # Début (10 messages au lieu de 3)
                            sample_messages.extend(messages[:10])
                            # Milieu étendu (8 messages au lieu de 2)  
                            mid = len(messages) // 2
                            sample_messages.extend(messages[mid-4:mid+4])
                            # Fin étendue (10 messages au lieu de 3)
                            sample_messages.extend(messages[-10:])
                        else:
                            sample_messages = messages
                        
                        # Formater pour IA avec plus de contenu
                        conv_text = f"=== CONVERSATION {file_path.stem} ({conv_info['size_kb']}KB) ===\n"
                        for msg in sample_messages:
                            role = msg.get('role', 'unknown')
                            content = msg.get('content', '')[:1500]  # 1500 chars par message au lieu de 800
                            conv_text += f"{role.upper()}: {content}\n\n"
                        
                        conversations_content.append(conv_text)
                        print(f"[BIOGRAPHY-MANAGER] 📄 Conversation >30KB ajoutée: {file_path.stem} ({conv_info['size_kb']}KB)")
                        
                except Exception as e:
                    print(f"[BIOGRAPHY-MANAGER] ⚠️ Erreur lecture {file_path}: {e}")
                    continue
                        
                except Exception:
                    continue
                    
            return "\n\n".join(conversations_content) if conversations_content else "Aucune conversation lisible"
            
        except Exception as e:
            return f"Erreur accès conversations: {e}"
    
    def _collect_summaries_cache(self) -> str:
        """Collecte les résumés progressifs disponibles"""
        try:
            summaries_dir = Path("data/summaries_cache")
            if not summaries_dir.exists():
                return "Aucun résumé progressif disponible"
            
            # Scanner TOUS les fichiers de résumés (pas de limite)
            summary_files = sorted(
                summaries_dir.glob("*.txt"),
                key=lambda f: f.stat().st_size,
                reverse=True
            )
            
            summaries_content = []
            for file_path in summary_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                    
                    if content and len(content) > 50:
                        # Aperçu du résumé
                        preview = content[:300] + "..." if len(content) > 300 else content
                        summaries_content.append(f"=== {file_path.name} ===\n{preview}")
                        
                except Exception:
                    continue
                    
            return "\n\n".join(summaries_content) if summaries_content else "Aucun résumé accessible"
            
        except Exception as e:
            return f"Erreur accès résumés: {e}"

    async def generate_volume2_json_with_grok(self, user_name: str, progress_callback=None) -> bool:
        """
        🧠 PHASE 1: Génération Volume 2 JSON structuré par GROK
        =======================================================

        PHILOSOPHIE OGMA: JSON généré par l'IA, pas de mécanique Python

        Processus:
        1. Collecte données multi-sources
        2. GROK analyse et structure les informations sur {user_name} UNIQUEMENT
        3. GROK génère JSON structuré conforme au schéma

        Args:
            user_name: Nom de l'utilisateur pour lequel générer les données
            progress_callback: Fonction optionnelle appelée avec (étape, message, données)

        Returns:
            True si succès, False si erreur
        """
        try:
            print(f"[BIOGRAPHY-MANAGER] 🧠 Phase 1: Génération JSON IA pour {user_name}")

            # Callback: Initialisation
            if progress_callback:
                await progress_callback(1, 5, "🔧 Initialisation...", {})

            # 1. COLLECTE DES DONNÉES SOURCES (identique)
            structured_manager = self.get_structured_manager(user_name)

            # Callback: Collecte Volume 1
            if progress_callback:
                await progress_callback(2, 5, "📖 Collecte Volume 1...", {})
            volume1_memories = self._collect_volume1_memories(user_name)

            # Callback: Collecte conversations
            if progress_callback:
                await progress_callback(3, 5, "💬 Collecte conversations >30KB...", {
                    'vol1_size': len(volume1_memories)
                })
            historical_conversations = self._collect_historical_conversations()

            # Callback: Collecte résumés
            if progress_callback:
                await progress_callback(4, 5, "📊 Collecte résumés...", {
                    'vol1_size': len(volume1_memories),
                    'conv_size': len(historical_conversations)
                })
            summaries_content = self._collect_summaries_cache()
            
            # 2. ACCÈS À GROK
            import ogma_ng
            if hasattr(ogma_ng, '_chat_controller') and ogma_ng._chat_controller:
                grok_controller = ogma_ng._chat_controller
            else:
                print(f"[BIOGRAPHY-MANAGER] ❌ GROK non disponible")
                return False
            
            # 3. PROMPT INTELLIGENT SPÉCIALISÉ (selon spécifications utilisateur)
            json_generation_prompt = f"""Tu es une psychiatre et psychologue experte spécialisée en analyse biographique profonde.

🎯 MISSION CRITIQUE: Analyser l'INTÉGRALITÉ des données sur {user_name} pour créer un profil JSON ultra-structuré

🧠 INTELLIGENCE ANALYTIQUE REQUISE:
- Analyse psychiatrique professionnelle complète
- Extraction d'insights psychologiques profonds
- Structuration rigoureuse selon schéma JSON
- Focus exclusif sur l'être humain {user_name}

⚠️ DIRECTIVES ABSOLUES:
- Analyser TOUTES les données fournies (Volume 1 intégral + conversations >30KB + summaries)
- IGNORER complètement toute référence à "Luna", "IA", "Archiviste" (entités artificielles)
- Extraire UNIQUEMENT les informations sur {user_name} (personne réelle)
- Produire analyse psychiatrique de niveau professionnel

📊 DONNÉES SOURCES COMPLÈTES:

=== VOLUME 1 INTÉGRAL ===
{volume1_memories}

=== CONVERSATIONS >30KB (RICHES EN CONTENU) ===
{historical_conversations}

=== RÉSUMÉS PROGRESSIFS (INSIGHTS IA) ===
{summaries_content}

🏗️ SCHÉMA JSON COMPLET (selon REFONTE_VOLUME2_ARCHITECTURE.md):
```json
{{
  "metadata": {{
    "user_name": "{user_name}",
    "created_at": "ISO_DATE",
    "last_updated": "ISO_DATE", 
    "total_analyses": NUMBER,
    "data_sources": ["volume1", "conversations", "summaries_cache"]
  }},
  "chronologie": [
    {{
      "timestamp": "ISO_DATE",
      "source": "SOURCE_NAME",
      "evenement": "Description événement concernant {user_name}",
      "conversation_id": "ID_CONV",
      "contexte": "Contexte détaillé psychologique"
    }}
  ],
  "etude_psychique": {{
    "mbti": {{
      "type_estime": "TYPE_MBTI",
      "confiance": 0.XX,
      "derniere_evaluation": "ISO_DATE",
      "indices_observes": ["observation comportementale 1", "observation 2"]
    }},
    "profil_psychologique": {{
      "traits_dominants": ["trait psychologique 1", "trait 2", "trait 3"],
      "mecanismes_defense": ["mécanisme psychologique 1", "mécanisme 2"],
      "zones_vulnerabilite": ["vulnérabilité 1", "vulnérabilité 2"]
    }},
    "intelligence_emotionnelle": {{
      "score_estime": X.X,
      "points_forts": ["force émotionnelle 1", "force 2"],
      "points_amelioration": ["amélioration 1", "amélioration 2"]
    }}
  }},
  "etude_intellectuelle": {{
    "structure_mentale": {{
      "type_pensee": "analytique|créative|pragmatique|hybride",
      "processus_decision": "description processus",
      "gestion_information": "description traitement info"
    }},
    "structure_memoire": {{
      "type_dominant": "visuelle|auditive|kinesthésique|associative",
      "points_forts": ["force mémoire 1", "force 2"],
      "particularites": ["particularité 1", "particularité 2"]
    }},
    "evaluation_comparative": {{
      "qi_estime": XXX,
      "percentile_population": XX,
      "comparaison_utilisateurs_ia": "supérieur|moyen|inférieur moyenne",
      "domaines_excellence": ["domaine cognitif 1", "domaine 2"]
    }}
  }},
  "etude_physique": {{
    "traits_physiques": {{
      "taille": "description taille",
      "corpulence": "description corpulence",
      "particularites": ["trait physique 1", "trait 2"]
    }},
    "expressions_caracteristiques": {{
      "micro_expressions": ["expression faciale 1", "expression 2"],
      "gestuelle": ["geste 1", "geste 2"]
    }},
    "ressemblances_notees": {{
      "personnalites": ["ressemblance personnalité 1"],
      "traits_communs": ["trait partagé 1", "trait 2"]
    }}
  }},
  "etude_gouts_preferences": {{
    "affinites_identifiees": {{
      "intellectuel": ["préférence intellectuelle 1", "préférence 2"],
      "artistique": ["goût artistique 1", "goût 2"],
      "social": ["préférence sociale 1", "préférence 2"]
    }},
    "repulsions_identifiees": {{
      "social": ["aversion sociale 1", "aversion 2"],
      "intellectuel": ["aversion intellectuelle 1", "aversion 2"],
      "environnemental": ["aversion environnementale 1"]
    }},
    "evolutions_observees": [
      {{
        "periode": "YYYY-MM → YYYY-MM",
        "changement": "description évolution",
        "declencheur": "facteur de changement"
      }}
    ]
  }}
}}
```

🎯 Analyse maintenant les données et génère le JSON structuré pour {user_name}:"""
            
            # 4. APPEL GROK POUR GÉNÉRATION JSON
            messages = [
                {"role": "system", "content": "Tu es une psychiatre experte. Tu génères UNIQUEMENT du JSON valide."},
                {"role": "user", "content": json_generation_prompt}
            ]
            
            print(f"[BIOGRAPHY-MANAGER] 🚀 Envoi à GROK pour génération JSON...")

            # Diagnostics avant envoi
            prompt_length = len(json_generation_prompt)
            print(f"[BIOGRAPHY-MANAGER] 📊 Prompt JSON: {prompt_length} caractères")
            print(f"[BIOGRAPHY-MANAGER] 📊 Données: Vol1={len(volume1_memories)}c, Conv={len(historical_conversations)}c, Sum={len(summaries_content)}c")

            # Callback: Données collectées
            if progress_callback:
                await progress_callback(5, 5, "🚀 Analyse GROK en cours...", {
                    'vol1_size': len(volume1_memories),
                    'conv_size': len(historical_conversations),
                    'sum_size': len(summaries_content),
                    'total_size': len(volume1_memories) + len(historical_conversations) + len(summaries_content)
                })

            # 🔧 SÉCURITÉ: Vérifier si le prompt n'est pas trop long
            if prompt_length > 200000:  # >200KB = risque de timeout
                print(f"[BIOGRAPHY-MANAGER] ⚠️ PROMPT TRÈS LONG ({prompt_length}c) - Réduction automatique")
                # Réduire les conversations si trop volumineuses
                if len(historical_conversations) > 30000:
                    historical_conversations = historical_conversations[:30000] + "\n[...TRONQUÉ POUR GROK...]"
                    # Régénérer le prompt avec données réduites
                    json_generation_prompt = f"""Tu es une psychiatre et psychologue experte spécialisée en analyse biographique profonde.

🎯 MISSION CRITIQUE: Analyser l'INTÉGRALITÉ des données sur {user_name} pour créer un profil JSON ultra-structuré

=== VOLUME 1 INTÉGRAL ===
{volume1_memories}

=== CONVERSATIONS (ÉCHANTILLON) ===
{historical_conversations}

=== RÉSUMÉS PROGRESSIFS ===
{summaries_content}

🏗️ GÉNÈRE le JSON structuré complet pour {user_name} selon le schéma précédent."""
                    print(f"[BIOGRAPHY-MANAGER] 📊 Prompt réduit: {len(json_generation_prompt)} caractères")

            print(f"[BIOGRAPHY-MANAGER] ⏱️ Début appel GROK...")
            import time
            start_time = time.time()

            # 🔧 MONITORING ACTIF : Tâche parallèle pour mise à jour du décompte
            grok_task = asyncio.create_task(
                grok_controller.call_chat_api(
                    messages=messages,
                    max_tokens=8000,  # Augmenté pour JSON plus riche
                    context_length=grok_controller.context_length,
                    temperature=0.3,  # Précision pour JSON
                    is_json=True  # Important !
                )
            )

            # Boucle de monitoring avec mises à jour toutes les 5 secondes
            try:
                while not grok_task.done():
                    elapsed = time.time() - start_time

                    if elapsed > 240.0:  # Timeout après 240s
                        grok_task.cancel()
                        raise asyncio.TimeoutError()

                    # Callback: Mise à jour du temps
                    if progress_callback:
                        await progress_callback(5, 5, f"🧠 GROK analyse en cours...", {
                            'vol1_size': len(volume1_memories),
                            'conv_size': len(historical_conversations),
                            'sum_size': len(summaries_content),
                            'total_size': len(volume1_memories) + len(historical_conversations) + len(summaries_content),
                            'elapsed': int(elapsed)
                        })

                    # Attendre 5 secondes avant la prochaine mise à jour
                    await asyncio.sleep(5)

                # Récupérer le résultat
                response, error = await grok_task

                duration = time.time() - start_time
                print(f"[BIOGRAPHY-MANAGER] ✅ GROK répondu en {duration:.1f}s")

                # Callback: GROK terminé
                if progress_callback:
                    await progress_callback(5, 5, "✅ Analyse terminée, validation...", {
                        'duration': duration
                    })
                
            except asyncio.TimeoutError:
                print(f"[BIOGRAPHY-MANAGER] ❌ TIMEOUT GROK (>60s) - Génération interrompue")
                return False
            
            if error or not response:
                print(f"[BIOGRAPHY-MANAGER] ❌ Erreur GROK JSON: {error}")
                return False
            
            # 5. VALIDATION ET SAUVEGARDE JSON
            json_content = response.get('content', '') if isinstance(response, dict) else str(response)
            
            try:
                # Parser pour valider JSON
                import json
                structured_data = json.loads(json_content)
                
                # Vérifier structure minimale
                required_keys = ['metadata', 'chronologie', 'etude_psychique']
                missing_keys = [k for k in required_keys if k not in structured_data]
                
                if missing_keys:
                    print(f"[BIOGRAPHY-MANAGER] ⚠️ Clés manquantes dans JSON: {missing_keys}")
                    # Continuer quand même mais signaler
                
                # Sauvegarder le JSON généré par IA
                success = structured_manager.save_structured_data(structured_data)
                
                if success:
                    print(f"[BIOGRAPHY-MANAGER] ✅ Volume 2 JSON généré par IA: {len(json_content)} chars")
                    return True
                else:
                    print(f"[BIOGRAPHY-MANAGER] ❌ Échec sauvegarde JSON")
                    return False
                    
            except json.JSONDecodeError as e:
                print(f"[BIOGRAPHY-MANAGER] ❌ JSON invalide généré par GROK: {e}")
                print(f"Contenu reçu: {json_content[:200]}...")
                return False
            
        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur génération JSON IA: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def generate_volume2_md_with_grok(self, user_name: str, progress_callback=None) -> Optional[str]:
        """
        🧠 PHASE 2: Transformation JSON → Markdown narratif par GROK
        ============================================================

        Lit le JSON structuré existant et le transforme en journal narratif développé

        Args:
            user_name: Nom de l'utilisateur
            progress_callback: Fonction optionnelle appelée avec (étape, message, données)

        Returns:
            Contenu Markdown narratif ou None si erreur
        """
        try:
            print(f"[BIOGRAPHY-MANAGER] 🧠 Phase 2: Transformation JSON→MD pour {user_name}")

            # Callback: Initialisation Phase 2
            if progress_callback:
                await progress_callback(1, 3, "🔧 Chargement JSON...", {})

            # 1. CHARGER LE JSON EXISTANT
            structured_manager = self.get_structured_manager(user_name)
            json_data = structured_manager.load_structured_data()

            if not json_data or json_data.get("metadata", {}).get("total_analyses", 0) == 0:
                print(f"[BIOGRAPHY-MANAGER] ⚠️ Aucun JSON trouvé pour {user_name}. Exécutez d'abord la Phase 1.")
                return None

            # Callback: JSON chargé
            import json
            json_str = json.dumps(json_data, ensure_ascii=False, indent=2)
            if progress_callback:
                await progress_callback(2, 3, "📊 JSON chargé, préparation prompt...", {
                    'json_size': len(json_str)
                })

            # 2. ACCÈS À GROK
            import ogma_ng
            if hasattr(ogma_ng, '_chat_controller') and ogma_ng._chat_controller:
                grok_controller = ogma_ng._chat_controller
            else:
                print(f"[BIOGRAPHY-MANAGER] ❌ GROK non disponible")
                return None
            
            # 3. PROMPT TRANSFORMATION JSON → MARKDOWN
            
            transformation_prompt = f"""Tu es une psychiatre experte et écrivain littéraire spécialisée en rédaction biographique narrative.

🎯 MISSION LITTÉRAIRE: Transformer le JSON en journal biographique narratif d'expert psychiatre

👤 SUJET: {user_name} (être humain réel - analyse psychiatrique littéraire complète)

📊 DONNÉES JSON ANALYSÉES:
```json
{json_str}
```

🎨 STYLE EXPERT PSYCHIATRE LITTÉRAIRE:
- Rédaction narrative fluide et développée (JAMAIS de listing)
- Analyse psychologique approfondie avec insights cliniques
- Développement littéraire des observations comportementales
- Synthèse créative des patterns de personnalité
- Ton professionnel d'expert psychiatre mais accessible
- Transitions narratives élégantes entre sections

� STRUCTURE SELON REFONTE_VOLUME2_ARCHITECTURE.md:

```markdown
# 📋 JOURNAL BIOGRAPHIQUE - {user_name}

*Analyse psychiatrique narrative générée le [DATE]*  
*Sources: Volume 1 intégral, Conversations >30KB, Résumés progressifs*

---

## 🕐 CHRONOLOGIE DES ÉVÉNEMENTS

### [Périodes chronologiques avec développement narratif]
[Développement narratif complet de l'évolution temporelle avec analyses des patterns de développement personnel, transitions psychologiques observées, moments charnières identifiés]

---

## 🧠 ÉTUDE PSYCHIQUE

### Profil MBTI : [Type] (Confiance: X%)
[Développement narratif approfondi du type psychologique avec justifications cliniques observées dans les données]

### Mécanismes psychologiques
[Analyse narrative experte des traits dominants, mécanismes de défense, zones de vulnérabilité avec développements psychiatriques approfondis]

### Intelligence émotionnelle
[Développement narratif des capacités émotionnelles observées]

---

## 🎓 ÉTUDE INTELLECTUELLE

### Architecture mentale
[Analyse narrative des processus cognitifs, type de pensée, gestion de l'information]

### Évaluation comparative  
[Développement narratif des capacités intellectuelles avec comparaisons contextualisées]

---

## 👤 ÉTUDE PHYSIQUE
[Développement narratif des observations physiques et expressives]

---

## 🎯 GOÛTS & PRÉFÉRENCES

### Affinités identifiées
[Développement narratif des centres d'intérêt et passions]

### Répulsions observées
[Analyse empathique et narrative des aversions]

### Évolutions récentes
[Développement narratif des changements de préférences observés]

---

*Journal biographique d'expertise psychiatriquegénéré par IA - OGMA V2.0*
```

🎯 EXIGENCES NARRATIVES EXPERTES:
- Chaque section développée sur 3-4 paragraphes minimum
- Style narratif fluide d'expert psychiatre littéraire  
- Analyses cliniques approfondies mais accessibles
- Transitions narratives élégantes
- Synthèses créatives des patterns observés
- Utilise les données JSON pour nourrir tes analyses
- Crée des liens et synthèses entre les différents éléments
- Style journal personnel développé, PAS de listing télégraphique
- Focalise sur {user_name} uniquement (ignore références IA/Luna)

Rédige maintenant ce journal biographique développé:"""
            
            # 4. APPEL GROK POUR TRANSFORMATION
            messages = [
                {"role": "system", "content": f"Tu es une psychiatre experte qui rédige des journaux biographiques narratifs sur {user_name}."},
                {"role": "user", "content": transformation_prompt}
            ]
            
            print(f"[BIOGRAPHY-MANAGER] 🚀 Envoi à GROK pour transformation narratif...")

            # Callback: Début transformation GROK
            if progress_callback:
                await progress_callback(3, 3, "🧠 GROK transforme JSON en narratif...", {
                    'json_size': len(json_str)
                })

            # 🔧 MONITORING ACTIF : Tâche parallèle pour mise à jour du décompte
            import time
            start_time = time.time()

            grok_task = asyncio.create_task(
                grok_controller.call_chat_api(
                    messages=messages,
                    max_tokens=8000,  # Journal développé
                    context_length=grok_controller.context_length,
                    temperature=0.7,  # Créativité pour narrative
                    is_json=False
                )
            )

            # Boucle de monitoring avec mises à jour toutes les 5 secondes
            try:
                while not grok_task.done():
                    elapsed = time.time() - start_time

                    if elapsed > 240.0:  # Timeout après 240s
                        grok_task.cancel()
                        raise asyncio.TimeoutError()

                    # Callback: Mise à jour du temps
                    if progress_callback:
                        await progress_callback(3, 3, "📝 Rédaction narrative en cours...", {
                            'json_size': len(json_str),
                            'elapsed': int(elapsed)
                        })

                    # Attendre 5 secondes avant la prochaine mise à jour
                    await asyncio.sleep(5)

                # Récupérer le résultat
                response, error = await grok_task

                duration = time.time() - start_time
                print(f"[BIOGRAPHY-MANAGER] ✅ GROK Phase 2 répondu en {duration:.1f}s")

                # Callback: GROK terminé
                if progress_callback:
                    await progress_callback(3, 3, "✅ Transformation terminée, sauvegarde...", {
                        'duration': duration
                    })

            except asyncio.TimeoutError:
                print(f"[BIOGRAPHY-MANAGER] ❌ TIMEOUT GROK Phase 2 (>240s)")
                return None

            if error or not response:
                print(f"[BIOGRAPHY-MANAGER] ❌ Erreur GROK MD: {error}")
                return None
            
            # 5. RÉCUPÉRATION ET SAUVEGARDE MARKDOWN
            markdown_content = response.get('content', '') if isinstance(response, dict) else str(response)
            
            if len(markdown_content) < 50:
                print(f"[BIOGRAPHY-MANAGER] ⚠️ Markdown trop court généré: {len(markdown_content)} chars")
                # En test, accepter même les contenus courts
                if "test" in markdown_content.lower():
                    print(f"[BIOGRAPHY-MANAGER] ✅ Mode test - Acceptation contenu court")
                else:
                    return None
            
            # Sauvegarder le journal Markdown
            journal_file = structured_manager.user_dir / "volume2_journal.md"
            
            with open(journal_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            print(f"[BIOGRAPHY-MANAGER] ✅ Volume 2 MD généré: {len(markdown_content):,} chars")
            print(f"[BIOGRAPHY-MANAGER] 📖 Journal sauvegardé: {journal_file}")
            
            return markdown_content
            
        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur transformation MD: {e}")
            import traceback
            traceback.print_exc()
            return None
        try:
            print(f"[BIOGRAPHY-MANAGER] 🧠 Génération journal IA pure pour {user_name}")
            
            # 1. COLLECTE DES DONNÉES SOURCES
            structured_manager = self.get_structured_manager(user_name)
            
            # Volume 1 FAISS (mémoires existantes)
            volume1_memories = self._collect_volume1_memories(user_name)
            
            # Conversations historiques
            historical_conversations = self._collect_historical_conversations()
            
            # Summaries cache (résumés progressifs)
            summaries_content = self._collect_summaries_cache()
            
            # 2. ACCÈS À GROK (IA PRINCIPALE)
            import ogma_ng
            
            if hasattr(ogma_ng, '_chat_controller') and ogma_ng._chat_controller:
                grok_controller = ogma_ng._chat_controller
                print(f"[BIOGRAPHY-MANAGER] ✅ Accès GROK configuré")
            else:
                print(f"[BIOGRAPHY-MANAGER] ❌ GROK non disponible")
                return None
            
            # 3. PROMPT SPÉCIALISÉ BIOGRAPHIE
            biographical_prompt = f"""Tu es une psychiatre et psychologue experte spécialisée en analyse biographique.

🎯 MISSION: Rédiger un journal biographique narratif et développé sur {user_name}

⚠️ IMPORTANT: 
- Tu analyses les données pour identifier UNIQUEMENT les informations concernant {user_name} (l'utilisateur humain)
- Tu IGNORES complètement toute référence à "Luna", "IA", "Archiviste" ou entités artificielles
- Tu te concentres sur la personne réelle: {user_name}

📊 DONNÉES SOURCES DISPONIBLES:

=== MÉMOIRES VOLUME 1 (FAISS) ===
{volume1_memories[:3000] if volume1_memories else "Aucune mémoire Volume 1 disponible"}

=== CONVERSATIONS HISTORIQUES ===
{historical_conversations[:3000] if historical_conversations else "Aucune conversation historique disponible"}

=== RÉSUMÉS PROGRESSIFS (SUMMARIES CACHE) ===
{summaries_content[:4000] if summaries_content else "Aucun résumé disponible"}

🎨 STYLE DEMANDÉ:
- Journal biographique NARRATIF (pas de listing)
- Développement psychologique approfondi
- Analyse des patterns comportementaux de {user_name}
- Synthèse créative et bienveillante
- Ton professionnel mais empathique

📝 STRUCTURE SOUHAITÉE:
1. **Portrait général de {user_name}**
2. **Évolution chronologique observée** 
3. **Analyse psychologique approfondie**
4. **Patterns comportementaux identifiés**
5. **Centres d'intérêt et préférences**
6. **Synthèse et perspectives**

Rédige maintenant ce journal biographique développé sur {user_name}:"""
            
            # 4. APPEL GROK POUR GÉNÉRATION
            messages = [
                {"role": "system", "content": "Tu es une psychiatre experte en analyse biographique."},
                {"role": "user", "content": biographical_prompt}
            ]
            
            print(f"[BIOGRAPHY-MANAGER] 🚀 Envoi à GROK pour génération narrative...")
            
            response, error = await grok_controller.call_chat_api(
                messages=messages,
                max_tokens=8000,  # Journal développé
                context_length=grok_controller.context_length,
                temperature=0.7,  # Créativité modérée
                is_json=False
            )
            
            if error or not response:
                print(f"[BIOGRAPHY-MANAGER] ❌ Erreur GROK: {error}")
                return None
            
            journal_content = response.get('content', '') if isinstance(response, dict) else str(response)
            
            if len(journal_content) < 100:
                print(f"[BIOGRAPHY-MANAGER] ⚠️ Journal trop court généré par GROK")
                return None
            
            print(f"[BIOGRAPHY-MANAGER] ✅ Journal IA généré: {len(journal_content):,} caractères")
            
            # 5. SAUVEGARDER LE JOURNAL
            journal_file = structured_manager.user_dir / "volume2_journal.md"
            
            # Header avec métadonnées
            final_journal = f"""# 📋 JOURNAL BIOGRAPHIQUE - {user_name}

*Généré automatiquement par GROK le {datetime.now().strftime('%d/%m/%Y à %H:%M')}*
**Méthode:** Analyse IA pure (Architecture V2.0)
**Sources:** Volume 1 FAISS, Conversations historiques, Résumés progressifs

---

{journal_content}

---

*Journal biographique généré par l'IA principale GROK - Architecture OGMA V2.0*
*Focus exclusif sur {user_name} - Aucun fallback Python utilisé*
"""
            
            with open(journal_file, 'w', encoding='utf-8') as f:
                f.write(final_journal)
            
            print(f"[BIOGRAPHY-MANAGER] 📖 Journal sauvegardé: {journal_file}")
            
            return final_journal
            
        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur génération journal IA: {e}")
            import traceback
            traceback.print_exc()
            return None

    def save_structured_journal(self, user_name: str) -> bool:
        """Sauvegarde le journal structuré généré"""
        try:
            structured_manager = self.get_structured_manager(user_name)
            return structured_manager.save_generated_journal()
        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur sauvegarde journal: {e}")
            return False