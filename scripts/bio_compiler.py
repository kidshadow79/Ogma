"""
🧬 Bio Compiler - Compilation Incrémentale des Faits Biographiques

Analyse les faits du volume2_structured.json et génère une structure JSON
de groupes thématiques, permettant une injection ciblée par l'activation bio.

Architecture miroir de ego_compiler.py :
- Source       : facts[] dans data/biographies/{user}/volume2_structured.json
- Sortie       : data/biographies/{user}/bio_compiled.json
- Tracking     : last_scanned_index (index dans facts[])
- Archiviste   : classe chaque fait dans 1-3 groupes thématiques
- Multi-appartenance : un fait peut appartenir à plusieurs groupes

Workflow:
1. Charge bio_compiled.json existant (ou init si première fois)
2. Compare last_scanned_index avec len(facts[]) → détecte nouveaux faits
3. Archiviste analyse chaque nouveau fait → groupe(s) + keywords
4. Merge incrémentalement dans structure existante
5. Sauvegarde avec metadata à jour

Différence vs ego_compiler: pas de flags booléens — chaque groupe contient
des faits textuels. L'activation injecte les faits des groupes pertinents.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import sys

# Accès aux imports OGMA
sys.path.insert(0, str(Path(__file__).parent.parent))


class BioCompiler:
    """Compilateur incrémental de faits biographiques en groupes thématiques"""

    def __init__(self, user_name: str):
        self.user_name = user_name
        self.user_dir = Path("data/biographies") / user_name.lower()
        self.source_file = self.user_dir / "volume2_structured.json"
        self.output_path = self.user_dir / "bio_compiled.json"
        self.archiviste_controller = None

    # ──────────────────────────────────────────────────────────
    # Archiviste controller
    # ──────────────────────────────────────────────────────────

    def _ensure_archiviste(self) -> bool:
        if self.archiviste_controller is not None:
            return True
        try:
            import ogma_ng
            self.archiviste_controller = ogma_ng._archiviste_controller
            if not self.archiviste_controller:
                print("[BIO-COMPILER] Archiviste controller non disponible")
                return False
        except Exception as e:
            print(f"[BIO-COMPILER] Erreur chargement Archiviste: {e}")
            return False
        return True

    # ──────────────────────────────────────────────────────────
    # Chargement / sauvegarde
    # ──────────────────────────────────────────────────────────

    def load_compiled(self) -> Dict[str, Any]:
        """Charge bio_compiled.json ou retourne une structure vide"""
        if self.output_path.exists():
            try:
                with open(self.output_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                print(f"[BIO-COMPILER] JSON existant chargé ({len(data.get('groups', {}))} groupes)")
                return data
            except Exception as e:
                print(f"[BIO-COMPILER] Erreur lecture JSON: {e}, réinitialisation")
        return self._empty_structure()

    def _empty_structure(self) -> Dict[str, Any]:
        return {
            "metadata": {
                "user_name": self.user_name,
                "created_at": datetime.now().isoformat(),
                "last_compilation": None,
                "total_facts_scanned": 0,
                "last_scanned_index": 0,
            },
            "groups": {},
            "trace_table": {},   # {fact_index_str: {groups: ["GRP1", ...]}}
        }

    def _save(self, data: Dict[str, Any]) -> None:
        try:
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"[BIO-COMPILER] Sauvegardé: {self.output_path}")
        except Exception as e:
            print(f"[BIO-COMPILER] Erreur sauvegarde: {e}")

    # ──────────────────────────────────────────────────────────
    # Lecture source
    # ──────────────────────────────────────────────────────────

    def load_source_facts(self) -> List[Dict[str, Any]]:
        """Charge facts[] depuis volume2_structured.json"""
        if not self.source_file.exists():
            print(f"[BIO-COMPILER] Source introuvable: {self.source_file}")
            return []
        try:
            with open(self.source_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            facts = data.get("facts", [])
            print(f"[BIO-COMPILER] {len(facts)} faits dans volume2_structured.json")
            return facts
        except Exception as e:
            print(f"[BIO-COMPILER] Erreur lecture source: {e}")
            return []

    # ──────────────────────────────────────────────────────────
    # Analyse Archiviste
    # ──────────────────────────────────────────────────────────

    async def analyze_fact_with_archiviste(
        self,
        fact: Dict[str, Any],
        fact_index: int,
        existing_groups: List[str],
    ) -> Optional[Dict[str, Any]]:
        """
        Archiviste classifie un fait biographique dans des groupes thématiques.

        Returns:
            {
                "groups": ["GOUTS", "LOISIRS"],   // 1-3 groupes
                "keywords": ["film", "SF"],
                "description": "description courte"
            }
        """
        if not self._ensure_archiviste():
            return None

        prompt = f"""Tu es l'Archiviste. Ta mission : organiser les faits biographiques de {self.user_name} en groupes thématiques cohérents et NON REDONDANTS.

**FAIT BIOGRAPHIQUE À CLASSER** (index {fact_index}):
"{fact.get('content', '')}"
Catégorie source: {fact.get('category', 'inconnue')}

**GROUPES THÉMATIQUES EXISTANTS**:
{json.dumps(existing_groups, ensure_ascii=False) if existing_groups else "Aucun groupe — tu vas créer les premiers"}

**TA MISSION**:
1. Assigne ce fait à 1-3 groupes thématiques :
   - Si un groupe existant est pertinent → utilise-le
   - Si aucun groupe existant ne correspond → crée-en un nouveau (nom court, MAJUSCULES)
   - Évite les doublons/variations de noms existants

2. Génère 3-6 KEYWORDS pour le matching sémantique au runtime

3. Écrit une DESCRIPTION ultra-courte du groupe (3-4 mots max)

**EXEMPLES DE GROUPES THÉMATIQUES** (pour inspiration):
- GOUTS, LOISIRS, RELATIONS, ANIMAUX, PROJETS, COMPETENCES, HABITUDES, SANTE,
  HISTOIRE_PERSONNELLE, VIE_QUOTIDIENNE, VALEURS, FAMILLE, TRAVAIL, TECHNOLOGIE

**RÈGLE D'OR**: 10 groupes riches valent mieux que 50 groupes fragmentés.
Un fait simple comme "Yohan a une chatte" va dans ANIMAUX ou RELATIONS — pas les deux.

**FORMAT JSON ATTENDU**:
{{
    "groups": ["GROUPE1", "GROUPE2"],
    "keywords": ["mot1", "mot2", "mot3"],
    "description": "description courte"
}}

Retourne UNIQUEMENT le JSON, rien d'autre."""

        try:
            messages = [{"role": "user", "content": prompt}]
            response, error = await self.archiviste_controller.call_chat_api(
                messages=messages,
                max_tokens=200,
                context_length=8000,
                temperature=0.2,
                is_json=True,
            )

            if error or not response:
                print(f"[BIO-COMPILER] Erreur Archiviste (fait {fact_index}): {error}")
                return None

            analysis = json.loads(response)

            if not all(k in analysis for k in ["groups", "keywords", "description"]):
                print(f"[BIO-COMPILER] Structure JSON invalide (fait {fact_index})")
                return None

            print(
                f"[BIO-COMPILER] Fait {fact_index} → groupes: {analysis['groups']}"
            )
            return analysis

        except json.JSONDecodeError as e:
            print(f"[BIO-COMPILER] Parse JSON error (fait {fact_index}): {e}")
            return None
        except Exception as e:
            print(f"[BIO-COMPILER] Erreur analyse (fait {fact_index}): {e}")
            return None

    # ──────────────────────────────────────────────────────────
    # Merge
    # ──────────────────────────────────────────────────────────

    def merge_fact_into_compiled(
        self,
        compiled: Dict[str, Any],
        fact: Dict[str, Any],
        fact_index: int,
        analysis: Dict[str, Any],
    ) -> None:
        """Intègre un fait analysé dans la structure compilée"""
        fact_key = str(fact_index)

        # Trace entry
        if fact_key not in compiled["trace_table"]:
            compiled["trace_table"][fact_key] = {"groups": []}

        for group_name in analysis["groups"]:
            # Créer le groupe s'il n'existe pas
            if group_name not in compiled["groups"]:
                compiled["groups"][group_name] = {
                    "description": analysis["description"],
                    "keywords": analysis["keywords"],
                    "facts": [],
                }
                print(f"[BIO-COMPILER] Nouveau groupe créé: {group_name}")

            group = compiled["groups"][group_name]

            # Merge keywords sans doublons
            existing_kw = set(group.get("keywords", []))
            group["keywords"] = list(existing_kw | set(analysis["keywords"]))

            # Ajouter le fait s'il n'est pas déjà dans ce groupe
            existing_indices = {f["index"] for f in group.get("facts", [])}
            if fact_index not in existing_indices:
                group["facts"].append(
                    {
                        "index": fact_index,
                        "content": fact.get("content", ""),
                        "date": fact.get("date", ""),
                        "category": fact.get("category", ""),
                    }
                )
                print(
                    f"[BIO-COMPILER] Fait {fact_index} ajouté au groupe {group_name}"
                )

            # Trace
            if group_name not in compiled["trace_table"][fact_key]["groups"]:
                compiled["trace_table"][fact_key]["groups"].append(group_name)

    # ──────────────────────────────────────────────────────────
    # Reset si volume supprimé et recréé
    # ──────────────────────────────────────────────────────────

    def _should_reset(self, compiled: Dict[str, Any], facts: List) -> bool:
        """Si le volume2 a été supprimé/recréé, le compiled est obsolète"""
        last_index = compiled["metadata"].get("last_scanned_index", 0)
        if last_index > len(facts):
            print(
                f"[BIO-COMPILER] Volume2 réinitialisé détecté "
                f"(last_scanned={last_index} > facts={len(facts)}), reset."
            )
            return True
        return False

    # ──────────────────────────────────────────────────────────
    # Point d'entrée compilation
    # ──────────────────────────────────────────────────────────

    async def compile(self) -> None:
        print("\n" + "=" * 60)
        print(f"🧬 BIO COMPILER — {self.user_name}")
        print("=" * 60 + "\n")

        # 1. Charger source
        facts = self.load_source_facts()
        if not facts:
            print("[BIO-COMPILER] Aucun fait source, skip.")
            return

        # 2. Charger compiled existant
        compiled = self.load_compiled()

        # 3. Reset si volume recréé depuis zéro
        if self._should_reset(compiled, facts):
            compiled = self._empty_structure()

        last_index = compiled["metadata"].get("last_scanned_index", 0)
        new_facts = facts[last_index:]

        if not new_facts:
            print(f"[BIO-COMPILER] Aucun nouveau fait depuis l'index {last_index}.")
            return

        print(f"[BIO-COMPILER] {len(new_facts)} nouveau(x) fait(s) à analyser.")

        # 4. Analyser chaque nouveau fait
        existing_groups = list(compiled["groups"].keys())
        analyzed_count = 0

        for i, fact in enumerate(new_facts):
            fact_index = last_index + i
            print(f"\n[{i+1}/{len(new_facts)}] Analyse fait {fact_index}...")
            print(f"   Contenu: {fact.get('content', '')[:80]}")

            analysis = await self.analyze_fact_with_archiviste(
                fact, fact_index, existing_groups
            )

            if analysis:
                self.merge_fact_into_compiled(compiled, fact, fact_index, analysis)
                existing_groups = list(compiled["groups"].keys())
                analyzed_count += 1

        # 5. Mettre à jour metadata
        compiled["metadata"]["last_compilation"] = datetime.now().isoformat()
        compiled["metadata"]["total_facts_scanned"] += analyzed_count
        compiled["metadata"]["last_scanned_index"] = last_index + len(new_facts)

        # 6. Sauvegarder
        self._save(compiled)

        print("\n" + "=" * 60)
        print(f"[BIO-COMPILER] Compilation terminée !")
        print(f"   Faits analysés : {analyzed_count}/{len(new_facts)}")
        print(f"   Groupes totaux : {len(compiled['groups'])}")
        print("=" * 60 + "\n")


# ──────────────────────────────────────────────────────────────
# Point d'entrée pour hook dream engine / shutdown
# ──────────────────────────────────────────────────────────────

async def compile_bio_incremental(user_name: str = None) -> None:
    """
    Point d'entrée principal pour hook dream engine et shutdown.

    Args:
        user_name: Nom de l'utilisateur. Si None, tente de récupérer l'utilisateur actif.
    """
    if not user_name:
        try:
            from identity_manager import get_current_user_name
            user_name = get_current_user_name()
        except Exception:
            pass

    if not user_name:
        print("[BIO-COMPILER] Aucun utilisateur actif, skip.")
        return

    compiler = BioCompiler(user_name)
    await compiler.compile()


# CLI pour test manuel
if __name__ == "__main__":
    import asyncio

    print("\n🧬 Bio Compiler - Mode Standalone")
    print("Utilisation: python bio_compiler.py [nom_utilisateur]")

    import sys as _sys
    _user = _sys.argv[1] if len(_sys.argv) > 1 else None
    asyncio.run(compile_bio_incremental(_user))
