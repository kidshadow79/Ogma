"""
ARCHIVISTE LOGGER - Système de monitoring consommation tokens
Usage: Importer et activer dans core_logic.py pour tracker consommation réelle
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from collections import defaultdict

class ArchivisteLogger:
    """Logger léger pour tracker consommation Archiviste"""
    
    def __init__(self, output_file: str = "data/archiviste_monitoring.json"):
        self.output_file = Path(output_file)
        self.jsonl_file = Path("data/archiviste_tokens_debug.jsonl")  # Nouveau: fichier JSONL en append
        self.enabled = True  # Toggle pour activer/désactiver
        self.calls = []
        self.stats = defaultdict(lambda: {"count": 0, "input_tokens": 0, "output_tokens": 0})
        self.session_start = datetime.now()
        
        # Créer le dossier data/ si nécessaire
        self.jsonl_file.parent.mkdir(parents=True, exist_ok=True)
        
    def log_call(self, 
                 source: str,
                 input_messages: list,
                 output_response: str,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Enregistre un appel Archiviste
        
        Args:
            source: Origine de l'appel (semantic_analysis, memory_synthesis, etc.)
            input_messages: Messages envoyés à l'API
            output_response: Réponse reçue
            metadata: Infos supplémentaires (model, temperature, etc.)
        """
        if not self.enabled:
            return
        
        # Estimation tokens (4 chars ≈ 1 token)
        input_text = json.dumps(input_messages, ensure_ascii=False)
        input_tokens = len(input_text) // 4
        output_tokens = len(output_response) // 4
        
        call_data = {
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "input_tokens_estimated": input_tokens,
            "output_tokens_estimated": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "input_chars": len(input_text),
            "output_chars": len(output_response),
            "metadata": metadata or {}
        }
        
        self.calls.append(call_data)
        
        # Update stats
        self.stats[source]["count"] += 1
        self.stats[source]["input_tokens"] += input_tokens
        self.stats[source]["output_tokens"] += output_tokens
        
        # ✨ NOUVEAU: Écriture immédiate dans fichier JSONL (append mode)
        try:
            with open(self.jsonl_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(call_data, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"[ARCHIVISTE-LOG] ⚠️ Erreur écriture JSONL: {e}")
        
        # Print en temps réel (optionnel)
        print(f"[ARCHIVISTE-LOG] {source}: {input_tokens} IN + {output_tokens} OUT = {input_tokens + output_tokens} tokens")
        
    def get_summary(self) -> Dict[str, Any]:
        """Génère un résumé de la session"""
        total_input = sum(s["input_tokens"] for s in self.stats.values())
        total_output = sum(s["output_tokens"] for s in self.stats.values())
        total_calls = sum(s["count"] for s in self.stats.values())
        
        return {
            "session_start": self.session_start.isoformat(),
            "session_duration_minutes": (datetime.now() - self.session_start).total_seconds() / 60,
            "total_calls": total_calls,
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "avg_tokens_per_call": (total_input + total_output) / total_calls if total_calls > 0 else 0,
            "ratio_input_output": total_input / total_output if total_output > 0 else 0,
            "by_source": dict(self.stats),
            "top_consumers": sorted(
                self.stats.items(),
                key=lambda x: x[1]["input_tokens"] + x[1]["output_tokens"],
                reverse=True
            )[:5]
        }
    
    def save_report(self):
        """Sauvegarde le rapport complet"""
        if not self.enabled or not self.calls:
            return
        
        report = {
            "summary": self.get_summary(),
            "detailed_calls": self.calls
        }
        
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Rapport sauvegardé: {self.output_file}")
        
    def print_summary(self):
        """Affiche un résumé dans la console"""
        summary = self.get_summary()
        
        print("\n" + "="*60)
        print("📊 RAPPORT CONSOMMATION ARCHIVISTE")
        print("="*60)
        print(f"Durée session: {summary['session_duration_minutes']:.1f} min")
        print(f"Total appels: {summary['total_calls']}")
        print(f"Total INPUT: {summary['total_input_tokens']:,} tokens")
        print(f"Total OUTPUT: {summary['total_output_tokens']:,} tokens")
        print(f"TOTAL GLOBAL: {summary['total_tokens']:,} tokens")
        print(f"Moyenne/appel: {summary['avg_tokens_per_call']:.0f} tokens")
        print(f"Ratio INPUT/OUTPUT: {summary['ratio_input_output']:.1f}:1")
        
        print("\n🔥 TOP CONSOMMATEURS:")
        for source, stats in summary['top_consumers']:
            total = stats['input_tokens'] + stats['output_tokens']
            percent = (total / summary['total_tokens'] * 100) if summary['total_tokens'] > 0 else 0
            print(f"  {source}: {total:,} tokens ({percent:.1f}%) - {stats['count']} appels")
        
        print("="*60 + "\n")


# Instance globale singleton
_archiviste_logger: Optional[ArchivisteLogger] = None

def get_archiviste_logger() -> ArchivisteLogger:
    """Récupère l'instance singleton du logger"""
    global _archiviste_logger
    if _archiviste_logger is None:
        _archiviste_logger = ArchivisteLogger()
    return _archiviste_logger

def enable_logging():
    """Active le logging"""
    logger = get_archiviste_logger()
    logger.enabled = True
    print("✅ Archiviste logging ACTIVÉ")

def disable_logging():
    """Désactive le logging"""
    logger = get_archiviste_logger()
    logger.enabled = False
    print("⏸️ Archiviste logging DÉSACTIVÉ")

def save_and_print_report():
    """Sauvegarde et affiche le rapport final"""
    logger = get_archiviste_logger()
    logger.save_report()
    logger.print_summary()
