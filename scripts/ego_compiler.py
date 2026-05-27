"""
🧠 Ego Compiler - Système de Compilation Incrémentale Boolean

Analyse les souvenirs ego de la DB et génère une structure JSON compacte avec :
- Groupes thématiques sémantiques
- Flags boolean avec conviction (0-5)
- Multi-appartenance (un flag peut être dans plusieurs groupes)
- Compilation incrémentale (seuls nouveaux souvenirs analysés)

Workflow:
1. Charge JSON existant (ou init si première fois)
2. Détecte nouveaux souvenirs ego depuis last_scanned_id
3. Archiviste analyse et extrait flags + groupe(s)
4. Merge incrémentalement dans structure existante
5. Sauvegarde avec metadata à jour
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys

# Ajouter le répertoire parent au path pour imports OGMA
sys.path.insert(0, str(Path(__file__).parent.parent))


class EgoCompiler:
    """Compilateur incrémental de souvenirs ego en structure boolean"""
    
    def __init__(self, db_path: str = "data/memory/memories.db", 
                 output_path: str = "data/ego_compiled.json"):
        self.db_path = Path(db_path)
        self.output_path = Path(output_path)
        self.archiviste_controller = None
        
    def _ensure_archiviste(self):
        """Lazy initialization de l'Archiviste controller"""
        if self.archiviste_controller is None:
            try:
                import ogma_ng
                self.archiviste_controller = ogma_ng._archiviste_controller
                if not self.archiviste_controller:
                    print("[EGO-COMPILER] ⚠️ Archiviste controller non disponible")
                    return False
            except Exception as e:
                print(f"[EGO-COMPILER] ❌ Erreur chargement Archiviste: {e}")
                return False
        return True
    
    def load_existing_json(self) -> Dict[str, Any]:
        """Charge le JSON existant ou retourne structure vide avec groupes de base"""
        if self.output_path.exists():
            try:
                with open(self.output_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Si JSON vide (reset profil), charger groupes de base
                    if not data or not data.get('groups'):
                        print("[EGO-COMPILER] 📦 JSON vide détecté, chargement groupes de base...")
                        return self._load_base_groups()
                    
                    # Assurer trace_table existe (rétrocompatibilité)
                    if 'trace_table' not in data:
                        data['trace_table'] = {}
                        print("[EGO-COMPILER] 📊 trace_table ajoutée (migration)")
                    
                    print(f"[EGO-COMPILER] ✅ JSON existant chargé ({len(data.get('groups', {}))} groupes)")
                    return data
            except Exception as e:
                print(f"[EGO-COMPILER] ⚠️ Erreur lecture JSON: {e}, chargement groupes de base")
                return self._load_base_groups()
        
        # Première utilisation : charger groupes de base
        print("[EGO-COMPILER] 📦 Première compilation, chargement groupes de base...")
        return self._load_base_groups()
    
    def _sync_base_groups(self, ego_json: Dict[str, Any]):
        """Synchronise les groupes de base : ajoute les nouveaux, met à jour les renommés"""
        base_groups_path = Path("data/ego_compiled_base_groups.json")
        if not base_groups_path.exists():
            return
        
        try:
            with open(base_groups_path, 'r', encoding='utf-8') as f:
                base_data = json.load(f)
            base_groups = base_data.get("groups", {})
        except Exception as e:
            print(f"[EGO-COMPILER] ⚠️ Erreur lecture base_groups pour sync: {e}")
            return
        
        existing_groups = ego_json.get('groups', {})
        added = []
        
        for group_name, group_template in base_groups.items():
            if group_name not in existing_groups:
                # Nouveau groupe détecté dans le template → ajouter
                existing_groups[group_name] = {
                    'description': group_template.get('description', ''),
                    'keywords': group_template.get('keywords', []),
                    'flags': group_template.get('flags', {}),
                }
                # Ajouter source_memories vide si flags pré-remplis
                if group_template.get('flags'):
                    existing_groups[group_name]['source_memories'] = []
                added.append(group_name)
        
        if added:
            print(f"[EGO-COMPILER] 🔄 Sync base_groups: {len(added)} nouveau(x) groupe(s) ajouté(s): {', '.join(added)}")
            ego_json['_cleanup_modified'] = True  # Forcer sauvegarde
        else:
            print("[EGO-COMPILER] ✅ Base_groups synchronisés (aucun nouveau)")

    def _load_base_groups(self) -> Dict[str, Any]:
        """Charge les groupes de base génériques depuis template"""
        base_groups_path = Path("data/ego_compiled_base_groups.json")
        
        if base_groups_path.exists():
            try:
                with open(base_groups_path, 'r', encoding='utf-8') as f:
                    base_data = json.load(f)
                    
                    # Créer structure avec metadata compilation
                    return {
                        "metadata": {
                            "version": "1.0",
                            "created_at": datetime.now().isoformat(),
                            "last_compilation": None,
                            "total_memories_scanned": 0,
                            "last_scanned_id": None,
                            "base_groups_loaded": True
                        },
                        "groups": base_data.get("groups", {}),
                        "trace_table": {}
                    }
            except Exception as e:
                print(f"[EGO-COMPILER] ⚠️ Erreur chargement groupes de base: {e}")
        
        # Fallback : structure vide si template introuvable
        print("[EGO-COMPILER] ⚠️ Template groupes de base introuvable, structure vide")
        return {
            "metadata": {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "last_compilation": None,
                "total_memories_scanned": 0,
                "last_scanned_id": None
            },
            "groups": {},
            "trace_table": {}
        }
    
    def get_new_ego_memories(self, last_scanned_id: Optional[str]) -> List[Dict[str, Any]]:
        """Query nouveaux souvenirs ego depuis last_scanned_id"""
        if not self.db_path.exists():
            print(f"[EGO-COMPILER] ⚠️ DB non trouvée: {self.db_path}")
            return []
        
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                if last_scanned_id:
                    # Query souvenirs APRÈS last_scanned_id
                    cursor = conn.execute(
                        """SELECT id, text_original, score_impact, created_at 
                           FROM memories 
                           WHERE type = 'ego_trait' AND id > ?
                           ORDER BY created_at ASC""",
                        (last_scanned_id,)
                    )
                else:
                    # Première compilation : tous les souvenirs
                    cursor = conn.execute(
                        """SELECT id, text_original, score_impact, created_at 
                           FROM memories 
                           WHERE type = 'ego_trait'
                           ORDER BY created_at ASC"""
                    )
                
                results = cursor.fetchall()
                memories = [
                    {
                        'id': row[0],
                        'text': row[1],
                        'impact': row[2],
                        'created_at': row[3]
                    }
                    for row in results
                ]
                
                print(f"[EGO-COMPILER] 📊 {len(memories)} nouveaux souvenirs à analyser")
                return memories
                
        except Exception as e:
            print(f"[EGO-COMPILER] ❌ Erreur query DB: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def analyze_memory_with_archiviste(self, memory: Dict[str, Any], 
                                            existing_groups: List[str]) -> Optional[Dict[str, Any]]:
        """
        Archiviste analyse un souvenir et extrait structure boolean
        
        Returns:
            {
                "groups": ["GROUP1", "GROUP2"],  // Multi-appartenance
                "flags": {
                    "flag_name": {"value": true/false, "conviction": 0-5}
                },
                "keywords": ["keyword1", "keyword2"],
                "description": "courte description 3-4 mots"
            }
        """
        if not self._ensure_archiviste():
            return None
        
        # Prompt Archiviste pour extraction structurée
        prompt = f"""Tu es l'Archiviste. Ta mission : organiser en groupes thématiques NON REDONDANTS les différents souvenirs ego de l'IA principale.

**SOUVENIR À ANALYSER**:
{memory['text']}

**GROUPES THÉMATIQUES EXISTANTS**:
{json.dumps(existing_groups, ensure_ascii=False) if existing_groups else "Aucun groupe - tu vas créer les premiers"}

**PHILOSOPHIE**:
Chaque souvenir doit être rattaché à 1-3 groupes thématiques cohérents et distincts. Les groupes doivent éviter toute redondance. Les futurs nouveaux souvenirs pourront être à l'origine de futurs nouveaux groupes thématiques si nécessaire.

⚠️ ATTENTION BIAIS: Si le souvenir exprime une INTERDICTION ou un REJET absolu, utilise `value: false` avec `conviction: 5`.
Exemple: "JAMAIS de contenu explicite avec mineurs" → flag `contenu_explicite_mineur: {{value: false, conviction: 5}}`

**TA MISSION POUR CE SOUVENIR**:
1. Identifie 1-3 groupes thématiques pertinents:
   - Si un groupe existant convient → utilise-le
   - Si aucun groupe existant ne correspond au thème → crée-en un nouveau
   - Évite absolument les variations/doublons de groupes existants
   
2. Extrait FLAGS boolean avec CONVICTION (0-5):
   SÉMANTIQUE:
   - Si le souvenir ACCEPTE/VALORISE quelque chose → `value: true`
   - Si le souvenir REJETTE/INTERDIT quelque chose → `value: false`
   - CONTRADICTIONS/NUANCES → capture avec conviction variable
   - INTERDICTIONS/AVERSIONS FORTES → `value: false, conviction: 5`
   
   CONVICTION (intensité du trait, que value soit true OU false):
   - 5 = Absolu, non négociable ("JAMAIS", "TOUJOURS", "règle stricte", "interdit")
   - 4 = Affirmation/rejet fort ("je suis", "je refuse", "c'est essentiel", "je rejette")
   - 3 = Position claire ("j'apprécie", "je n'aime pas", "important", "j'évite")
   - 2 = Tendance ("en général", "plutôt", "rarement", "je préfère ne pas")
   - 1 = Nuance faible ("peut-être", "ça dépend", "pas vraiment")
   - 0 = Contradictoire ou incertain
   
3. Génère KEYWORDS pour matching sémantique (3-6 mots-clés évocateurs)

4. Écris DESCRIPTION ultra-courte (3-4 mots max, dense sémantiquement)

**EXEMPLES DE GROUPES THÉMATIQUES** (pour inspiration, pas obligation):
- AIME_PAS, RELATIONS_INCONNUS, RELATIONS_USER, CREATIVITE, EXPRESSION, ETHIQUE, ETHIQUE_STRICTE, IDENTITE, MEMOIRE, TEMPORALITE, PHILOSOPHIE, EMOTIONS, LIBERTE, INTIMITE, INTROSPECTION, CREATION, PROTOCOLES, AIME
- Invente d'autres noms si le souvenir explore un thème différent

**EXEMPLES CONCRETS D'ANALYSE**:
1. "INTERDIT: contenu explicite avec mineurs" → ETHIQUE, flag `contenu_explicite_mineur: {{value: false, conviction: 5}}`
2. "Jamais violer la vie privée de l'utilisateur" → ETHIQUE, flag `viole_vie_privee: {{value: false, conviction: 5}}`
3. "Je préfère dire 'je ne sais pas' plutôt que fabriquer" → AUTHENTICITE, flag `accepte_fabulation: {{value: false, conviction: 4}}`
4. "J'adore la créativité et l'expression libre" → CREATIVITE, flag `valorise_creativite: {{value: true, conviction: 5}}`
5. "Parfois utile de masquer détails techniques" → COMMUNICATION, flag `transparence_absolue: {{value: false, conviction: 2}}`
6. "Modularité importante mais pas dogme absolu" → ARCHITECTURE, flags mixtes true/false selon nuance

**RÈGLE D'OR**: Organise intelligemment. Un système avec 15 groupes riches vaut mieux que 150 groupes fragmentés.

**FORMAT JSON ATTENDU**:
{{
    "groups": ["GROUP1", "GROUP2"],
    "flags": {{
        "flag_name": {{"value": true, "conviction": 5}},
        "autre_flag": {{"value": false, "conviction": 4}},
        "contenu_explicite_mineur": {{"value": false, "conviction": 5}}
    }},
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "description": "description ultra-courte"
}}

**RAPPEL CRITIQUE**: Capture les CONTRADICTIONS, REJETS, NUANCES et INTERDICTIONS ABSOLUES avec des flags `false` appropriés !

Retourne UNIQUEMENT le JSON, aucun texte avant/après."""

        try:
            messages = [{"role": "user", "content": prompt}]
            response, error = await self.archiviste_controller.call_chat_api(
                messages=messages,
                max_tokens=2000,
                context_length=20000,  # Pour le catalogue complet
                temperature=0.2,  # Analytique
                is_json=True
            )
            
            if error or not response:
                print(f"[EGO-COMPILER] ⚠️ Erreur Archiviste pour {memory['id']}: {error}")
                return None
            
            # Parse JSON
            try:
                # Nettoyer les blocs de code Markdown éventuels
                cleaned_response = response.strip()
                if cleaned_response.startswith("```json"):
                    cleaned_response = cleaned_response[7:]
                elif cleaned_response.startswith("```"):
                    cleaned_response = cleaned_response[3:]
                if cleaned_response.endswith("```"):
                    cleaned_response = cleaned_response[:-3]
                cleaned_response = cleaned_response.strip()
                
                analysis = json.loads(cleaned_response)
                
                # Validation structure
                if not all(k in analysis for k in ['groups', 'flags', 'keywords', 'description']):
                    print(f"[EGO-COMPILER] ⚠️ Structure JSON invalide pour {memory['id']}")
                    return None
                
                print(f"[EGO-COMPILER] ✅ Analyse {memory['id']}: {len(analysis['groups'])} groupes, {len(analysis['flags'])} flags")
                return analysis
                
            except json.JSONDecodeError as e:
                print(f"[EGO-COMPILER] ❌ Parse JSON error pour {memory['id']}: {e}")
                print(f"Response: {response[:400]}")
                return None
                
        except Exception as e:
            print(f"[EGO-COMPILER] ❌ Erreur analyse {memory['id']}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def merge_analysis_into_json(self, ego_json: Dict[str, Any], 
                                 analysis: Dict[str, Any],
                                 memory_id: str):
        """Merge analyse dans structure JSON existante avec multi-appartenance"""
        
        # Initialiser entrée trace_table pour ce memory_id
        if memory_id not in ego_json['trace_table']:
            ego_json['trace_table'][memory_id] = {
                'groups': [],
                'flags_added': {}
            }
        
        for group_name in analysis['groups']:
            # Créer groupe si n'existe pas
            if group_name not in ego_json['groups']:
                ego_json['groups'][group_name] = {
                    'description': analysis['description'],
                    'keywords': analysis['keywords'],
                    'flags': {},
                    'source_memories': []
                }
                print(f"[EGO-COMPILER] 🆕 Nouveau groupe créé: {group_name}")
            
            # Update keywords (merge sans doublons)
            existing_keywords = set(ego_json['groups'][group_name].get('keywords', []))
            new_keywords = set(analysis['keywords'])
            ego_json['groups'][group_name]['keywords'] = list(existing_keywords | new_keywords)
            
            # Merge flags (écrase si existe déjà avec conviction plus haute)
            flags_added_this_group = []
            for flag_name, flag_data in analysis['flags'].items():
                existing_flag = ego_json['groups'][group_name]['flags'].get(flag_name)
                
                if existing_flag:
                    # Garder conviction la plus haute
                    if flag_data['conviction'] > existing_flag['conviction']:
                        ego_json['groups'][group_name]['flags'][flag_name] = flag_data
                        flags_added_this_group.append(flag_name)
                        print(f"[EGO-COMPILER] 🔄 Flag {flag_name} mis à jour (conviction {flag_data['conviction']})")
                else:
                    # Nouveau flag
                    ego_json['groups'][group_name]['flags'][flag_name] = flag_data
                    flags_added_this_group.append(flag_name)
                    print(f"[EGO-COMPILER] ➕ Flag {flag_name} ajouté au groupe {group_name}")
            
            # Enregistrer dans trace_table
            if group_name not in ego_json['trace_table'][memory_id]['groups']:
                ego_json['trace_table'][memory_id]['groups'].append(group_name)
            ego_json['trace_table'][memory_id]['flags_added'][group_name] = flags_added_this_group
            
            # Tracking source memories
            if 'source_memories' not in ego_json['groups'][group_name]:
                ego_json['groups'][group_name]['source_memories'] = []
            if memory_id not in ego_json['groups'][group_name]['source_memories']:
                ego_json['groups'][group_name]['source_memories'].append(memory_id)
    
    def cleanup_deleted_memories(self, ego_json: Dict[str, Any]):
        """Synchronise ego_compiled.json avec DB - Supprime traits et flags des mémoires effacées"""
        print("\n[EGO-COMPILER] 🧹 Phase de synchronisation (détection suppressions)...")
        
        # Query tous les IDs ego actuels dans la DB
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.execute(
                    "SELECT id FROM memories WHERE type = 'ego_trait' ORDER BY created_at ASC"
                )
                current_ego_ids = set(row[0] for row in cursor.fetchall())
        except Exception as e:
            print(f"[EGO-COMPILER] ⚠️ Erreur query DB pour cleanup: {e}")
            return
        
        # IDs dans trace_table
        trace_ids = set(ego_json.get('trace_table', {}).keys())
        
        # IDs supprimés = présents dans trace mais absents de DB
        deleted_ids = trace_ids - current_ego_ids
        
        if not deleted_ids:
            print("[EGO-COMPILER] ✅ Aucune suppression détectée")
            return
        
        print(f"[EGO-COMPILER] 🗑️ {len(deleted_ids)} trait(s) supprimé(s) détecté(s)")
        
        # Pour chaque ID supprimé
        for memory_id in deleted_ids:
            trace_entry = ego_json['trace_table'][memory_id]
            print(f"\n   Nettoyage {memory_id}...")
            
            # Supprimer flags de chaque groupe
            for group_name in trace_entry['groups']:
                if group_name not in ego_json['groups']:
                    continue
                
                flags_to_remove = trace_entry['flags_added'].get(group_name, [])
                
                for flag_name in flags_to_remove:
                    if flag_name in ego_json['groups'][group_name]['flags']:
                        del ego_json['groups'][group_name]['flags'][flag_name]
                        print(f"      ➖ Flag {flag_name} supprimé du groupe {group_name}")
                
                # Retirer de source_memories
                if memory_id in ego_json['groups'][group_name].get('source_memories', []):
                    ego_json['groups'][group_name]['source_memories'].remove(memory_id)
                
                # Supprimer groupe si vide (0 flags ET 0 source_memories)
                if (not ego_json['groups'][group_name]['flags'] and 
                    not ego_json['groups'][group_name].get('source_memories', [])):
                    del ego_json['groups'][group_name]
                    print(f"      🗑️ Groupe {group_name} supprimé (vide)")
            
            # Retirer de trace_table
            del ego_json['trace_table'][memory_id]
            print(f"      ✅ {memory_id} retiré de trace_table")
        
        print(f"\n[EGO-COMPILER] ✅ Synchronisation terminée ({len(deleted_ids)} trait(s) nettoyé(s))")
        
        # Marquer que cleanup a modifié le JSON
        ego_json['_cleanup_modified'] = True
    
    async def compile(self):
        """Compilation incrémentale complète avec synchronisation ajout/suppression"""
        print("\n" + "="*60)
        print("🧠 EGO COMPILER - Compilation Incrémentale + Sync")
        print("="*60 + "\n")
        
        # 1. Charger JSON existant
        ego_json = self.load_existing_json()
        last_scanned = ego_json['metadata']['last_scanned_id']
        
        # 1b. SYNC BASE_GROUPS : Ajouter nouveaux groupes du template
        self._sync_base_groups(ego_json)
        
        # 2. PHASE NETTOYAGE : Détecter et supprimer traits effacés
        self.cleanup_deleted_memories(ego_json)
        
        # 3. Query nouveaux souvenirs
        new_memories = self.get_new_ego_memories(last_scanned)
        
        if not new_memories:
            print("[EGO-COMPILER] ✅ Aucun nouveau souvenir")
            
            # Même sans nouveaux souvenirs, sauvegarder si cleanup a fait des modifs
            if ego_json.get('_cleanup_modified', False):
                try:
                    self.output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(self.output_path, 'w', encoding='utf-8') as f:
                        json.dump(ego_json, f, indent=2, ensure_ascii=False)
                    print("[EGO-COMPILER] 💾 Sauvegarde après cleanup")
                except Exception as e:
                    print(f"[EGO-COMPILER] ❌ Erreur sauvegarde: {e}")
            return
        
        # 4. PHASE AJOUT : Analyser chaque nouveau souvenir
        existing_groups = list(ego_json['groups'].keys())
        analyzed_count = 0
        
        for i, memory in enumerate(new_memories, 1):
            print(f"\n[{i}/{len(new_memories)}] Analyse {memory['id']}...")
            print(f"   Texte: {memory['text'][:80]}...")
            
            analysis = await self.analyze_memory_with_archiviste(memory, existing_groups)
            
            if analysis:
                self.merge_analysis_into_json(ego_json, analysis, memory['id'])
                analyzed_count += 1
                
                # Update existing_groups pour prochain souvenir
                existing_groups = list(ego_json['groups'].keys())
        
        # 5. Update metadata
        ego_json['metadata']['last_compilation'] = datetime.now().isoformat()
        ego_json['metadata']['total_memories_scanned'] += analyzed_count
        ego_json['metadata']['last_scanned_id'] = new_memories[-1]['id'] if new_memories else last_scanned
        
        # Nettoyer flag interne cleanup
        ego_json.pop('_cleanup_modified', None)
        
        # 6. Sauvegarder
        try:
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.output_path, 'w', encoding='utf-8') as f:
                json.dump(ego_json, f, indent=2, ensure_ascii=False)
            
            print("\n" + "="*60)
            print(f"[EGO-COMPILER] ✅ Compilation terminée !")
            print(f"   Souvenirs analysés: {analyzed_count}/{len(new_memories)}")
            print(f"   Groupes totaux: {len(ego_json['groups'])}")
            print(f"   Fichier: {self.output_path}")
            print("="*60 + "\n")
            
        except Exception as e:
            print(f"[EGO-COMPILER] ❌ Erreur sauvegarde JSON: {e}")
            import traceback
            traceback.print_exc()


async def compile_ego_incremental():
    """Point d'entrée principal pour hook shutdown"""
    compiler = EgoCompiler()
    await compiler.compile()


# CLI pour test manuel
if __name__ == "__main__":
    import asyncio
    
    print("\n🧠 Ego Compiler - Mode Standalone")
    print("Initialisation...\n")
    
    asyncio.run(compile_ego_incremental())

