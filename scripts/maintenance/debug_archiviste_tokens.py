#!/usr/bin/env python3
"""
Debug Tool: Mesure Consommation Tokens Archiviste en Temps Réel
================================================================

Ajoute des hooks de mesure pour compter EXACTEMENT les tokens consommés
par l'Archiviste sur une session réelle.

Usage:
    1. Lancer OGMA normalement
    2. Activer ce debug via settings ou variable environnement
    3. Faire 5-10 interactions normales
    4. Consulter le rapport généré

Ou exécuter ce script standalone pour analyse logs GROK (si disponibles)
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from collections import defaultdict


class ArchivisteTokenCounter:
    """Compteur tokens Archiviste avec catégorisation par source"""
    
    def __init__(self):
        self.calls = []
        self.totals_by_source = defaultdict(lambda: {'input': 0, 'output': 0, 'count': 0})
        
    def log_call(self, source: str, input_tokens: int, output_tokens: int, context: str = ""):
        """Enregistre un appel Archiviste"""
        call_data = {
            'timestamp': datetime.now().isoformat(),
            'source': source,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': input_tokens + output_tokens,
            'context': context[:100]  # Tronqué pour lisibilité
        }
        
        self.calls.append(call_data)
        
        # Cumul par source
        self.totals_by_source[source]['input'] += input_tokens
        self.totals_by_source[source]['output'] += output_tokens
        self.totals_by_source[source]['count'] += 1
        
        print(f"[TOKEN-COUNTER] {source}: {input_tokens} IN + {output_tokens} OUT = {input_tokens + output_tokens} TOTAL")
    
    def get_report(self) -> Dict:
        """Génère rapport complet"""
        total_input = sum(data['input'] for data in self.totals_by_source.values())
        total_output = sum(data['output'] for data in self.totals_by_source.values())
        total_calls = sum(data['count'] for data in self.totals_by_source.values())
        
        report = {
            'summary': {
                'total_calls': total_calls,
                'total_input_tokens': total_input,
                'total_output_tokens': total_output,
                'total_tokens': total_input + total_output,
                'avg_tokens_per_call': (total_input + total_output) / total_calls if total_calls > 0 else 0
            },
            'by_source': dict(self.totals_by_source),
            'detailed_calls': self.calls
        }
        
        return report
    
    def print_report(self):
        """Affiche rapport formaté"""
        report = self.get_report()
        
        print("\n" + "=" * 80)
        print("📊 RAPPORT CONSOMMATION TOKENS ARCHIVISTE")
        print("=" * 80)
        print()
        
        summary = report['summary']
        print(f"Total Appels: {summary['total_calls']}")
        print(f"Total INPUT: {summary['total_input_tokens']:,} tokens")
        print(f"Total OUTPUT: {summary['total_output_tokens']:,} tokens")
        print(f"TOTAL GLOBAL: {summary['total_tokens']:,} tokens")
        print(f"Moyenne/appel: {summary['avg_tokens_per_call']:.0f} tokens")
        print()
        
        print("-" * 80)
        print("PAR SOURCE:")
        print("-" * 80)
        print()
        
        # Trier par consommation totale décroissante
        sorted_sources = sorted(
            report['by_source'].items(),
            key=lambda x: x[1]['input'] + x[1]['output'],
            reverse=True
        )
        
        for source, data in sorted_sources:
            total = data['input'] + data['output']
            pct = (total / summary['total_tokens'] * 100) if summary['total_tokens'] > 0 else 0
            
            print(f"{source}:")
            print(f"  Appels: {data['count']}")
            print(f"  INPUT: {data['input']:,} tokens")
            print(f"  OUTPUT: {data['output']:,} tokens")
            print(f"  TOTAL: {total:,} tokens ({pct:.1f}%)")
            print()
        
        print("=" * 80)
    
    def save_report(self, filepath: str = "data/archiviste_tokens_report.json"):
        """Sauvegarde rapport JSON"""
        report = self.get_report()
        report['generated_at'] = datetime.now().isoformat()
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Rapport sauvegardé: {filepath}")


# Instance globale pour tracking
_global_counter = ArchivisteTokenCounter()


def estimate_tokens_from_text(text: str) -> int:
    """Estime tokens depuis texte (approximation 1 token ≈ 4 chars)"""
    return len(text) // 4


def wrap_archiviste_call(source: str):
    """
    Décorateur pour wrapper les appels Archiviste et mesurer tokens
    
    Usage:
        @wrap_archiviste_call("memory_synthesis")
        async def _call_archiviste_synthesis(self, ...):
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Exécuter fonction originale
            result = await func(*args, **kwargs)
            
            # Estimer tokens (si pas de métriques API disponibles)
            # Pour l'instant approximation basique
            input_approx = estimate_tokens_from_text(str(args) + str(kwargs))
            output_approx = estimate_tokens_from_text(str(result))
            
            # Logger
            _global_counter.log_call(
                source=source,
                input_tokens=input_approx,
                output_tokens=output_approx,
                context=str(args[1] if len(args) > 1 else "")[:100]
            )
            
            return result
        return wrapper
    return decorator


# ===================================================================
# ANALYSE LOGS GROK (si disponibles)
# ===================================================================

def analyze_grok_logs_if_available():
    """
    Tente d'analyser les logs GROK si accessibles
    
    Note: Les logs GROK ne sont probablement PAS accessibles localement,
    mais cette fonction pourrait parser des exports CSV si disponibles
    """
    print("🔍 Recherche logs GROK...")
    print()
    
    # Patterns potentiels de logs
    log_patterns = [
        "data/grok_logs*.json",
        "data/api_logs*.txt",
        "*.log"
    ]
    
    for pattern in log_patterns:
        logs = list(Path(".").glob(pattern))
        if logs:
            print(f"✅ Trouvé logs: {logs}")
            # TODO: Parser selon format
            return
    
    print("⚠️ Aucun log GROK trouvé localement")
    print()
    print("💡 Pour accéder aux logs GROK:")
    print("   1. Aller sur console.x.ai (ou dashboard GROK)")
    print("   2. Section 'Usage' ou 'API Logs'")
    print("   3. Filtrer par model: grok-4-fast-non-reasoning")
    print("   4. Exporter CSV/JSON si option disponible")
    print()


# ===================================================================
# RECOMMANDATIONS OPTIMISATION
# ===================================================================

def generate_optimization_recommendations(report: Dict) -> List[str]:
    """Génère recommandations basées sur le rapport"""
    recommendations = []
    
    summary = report['summary']
    by_source = report['by_source']
    
    # Identifier top consommateurs
    sorted_sources = sorted(
        by_source.items(),
        key=lambda x: x[1]['input'] + x[1]['output'],
        reverse=True
    )
    
    if len(sorted_sources) > 0:
        top_source, top_data = sorted_sources[0]
        top_tokens = top_data['input'] + top_data['output']
        top_pct = (top_tokens / summary['total_tokens'] * 100) if summary['total_tokens'] > 0 else 0
        
        if top_pct > 40:
            recommendations.append(
                f"🔥 PRIORITÉ HAUTE: '{top_source}' consomme {top_pct:.0f}% des tokens - optimiser en priorité"
            )
    
    # Vérifier nombre d'appels par message
    avg_calls = summary['total_calls']  # Sur la session
    if avg_calls > 5:
        recommendations.append(
            f"⚠️ {avg_calls} appels Archiviste détectés - envisager fusion/cache"
        )
    
    # Vérifier ratio INPUT/OUTPUT
    if summary['total_input_tokens'] > 0:
        input_output_ratio = summary['total_input_tokens'] / summary['total_output_tokens'] if summary['total_output_tokens'] > 0 else float('inf')
        if input_output_ratio > 5:
            recommendations.append(
                f"📥 Ratio INPUT/OUTPUT élevé ({input_output_ratio:.1f}:1) - réduire contextes envoyés"
            )
    
    return recommendations


# ===================================================================
# MAIN
# ===================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("🔧 ARCHIVISTE TOKEN DEBUG TOOL")
    print("=" * 80)
    print()
    
    print("Ce script s'intègre à OGMA pour mesurer la consommation réelle.")
    print()
    print("OPTIONS:")
    print("  1. Intégration code (ajouter décorateurs aux fonctions Archiviste)")
    print("  2. Analyse logs GROK (si exports disponibles)")
    print("  3. Monitoring temps réel (hook dans core_logic.py)")
    print()
    
    # Essayer analyse logs
    analyze_grok_logs_if_available()
    
    print()
    print("=" * 80)
    print()
    
    # Exemple simulation
    print("📊 SIMULATION (données exemple):")
    print()
    
    # Simuler quelques appels
    _global_counter.log_call("memory_synthesis", 2000, 300, "Synthèse mémoires utilisateur")
    _global_counter.log_call("semantic_analysis", 800, 150, "Analyse keywords message")
    _global_counter.log_call("temporal_analysis", 900, 100, "Détection fatigue utilisateur")
    _global_counter.log_call("capability_advisor", 1000, 200, "Suggestion capacité recherche")
    _global_counter.log_call("memory_synthesis", 2200, 350, "Synthèse mémoires utilisateur")
    _global_counter.log_call("introspection_dialogue", 2500, 500, "Tour dialogue introspection")
    
    # Afficher rapport
    _global_counter.print_report()
    
    # Recommandations
    report = _global_counter.get_report()
    recommendations = generate_optimization_recommendations(report)
    
    if recommendations:
        print()
        print("💡 RECOMMANDATIONS:")
        print()
        for rec in recommendations:
            print(f"  {rec}")
        print()
    
    # Sauvegarder
    _global_counter.save_report()
    
    print()
    print("✅ Pour intégration réelle, modifier core_logic.py pour logger appels")
    print()
