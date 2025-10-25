#!/usr/bin/env python3
"""
Diagnostic complet des données OGMA pour le système profil unique
Identifie tous les éléments à sauvegarder/supprimer selon la spécification
"""

import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


def analyze_ogma_data() -> Dict:
    """Analyse complète de tous les éléments OGMA"""
    
    print("🔍 DIAGNOSTIC OGMA - SYSTÈME PROFIL UNIQUE")
    print("=" * 60)
    
    analysis = {
        'timestamp': datetime.now().isoformat(),
        'data_directory': {},
        'extensions_directory': {},
        'memory_analysis': {},
        'souvenirs_fondateurs': [],
        'total_size_mb': 0,
        'recommendations': []
    }
    
    # Analyse du dossier data/
    print("\n📂 ANALYSE DOSSIER DATA/")
    data_dir = Path("data")
    if data_dir.exists():
        analysis['data_directory'] = analyze_data_directory(data_dir)
    
    # Analyse du dossier extensions/
    print("\n🧩 ANALYSE EXTENSIONS/")
    ext_dir = Path("extensions")  
    if ext_dir.exists():
        analysis['extensions_directory'] = analyze_extensions_directory(ext_dir)
    
    # Analyse spécifique de la mémoire
    print("\n🧠 ANALYSE MÉMOIRE")
    analysis['memory_analysis'] = analyze_memory_system()
    
    # Vérification des souvenirs fondateurs
    print("\n🏛️ VÉRIFICATION SOUVENIRS FONDATEURS")
    analysis['souvenirs_fondateurs'] = verify_founder_memories()
    
    # Calcul de la taille totale
    analysis['total_size_mb'] = calculate_total_size()
    
    # Recommandations
    analysis['recommendations'] = generate_recommendations(analysis)
    
    return analysis


def analyze_data_directory(data_dir: Path) -> Dict:
    """Analyse détaillée du dossier data/"""
    
    elements = {}
    
    # Éléments à SUPPRIMER lors du reset
    delete_targets = [
        'conversations/',
        'generated_images/', 
        'summaries_cache/',
        'uploads/',
        'biographies/',
        'ego_archive/',
        'memory/' # (sauf souvenirs fondateurs)
    ]
    
    # Éléments à RÉINITIALISER 
    reset_targets = [
        'settings.json',  # (section prompts seulement)
        'identities.json',
        'ego_prompt.txt'
    ]
    
    # Éléments à CONSERVER
    preserve_targets = [
        'instructions_defaults.json',
        'memories.db',  # (souvenirs fondateurs seulement)
        'memory.db'     # (souvenirs fondateurs seulement) 
    ]
    
    for item in data_dir.iterdir():
        if item.name.startswith('.'):
            continue
            
        item_info = {
            'path': str(item),
            'type': 'directory' if item.is_dir() else 'file',
            'size_mb': 0,
            'action': 'unknown'
        }
        
        if item.is_file():
            item_info['size_mb'] = round(item.stat().st_size / 1024 / 1024, 2)
        elif item.is_dir():
            item_info['size_mb'] = calculate_directory_size(item)
            item_info['file_count'] = count_files_recursive(item)
        
        # Déterminer l'action selon la spécification
        if any(item.name.startswith(target.rstrip('/')) for target in delete_targets):
            item_info['action'] = 'DELETE'
        elif item.name in [target for target in reset_targets]:
            item_info['action'] = 'RESET'
        elif item.name in preserve_targets:
            item_info['action'] = 'PRESERVE'
        else:
            item_info['action'] = 'ANALYZE'
            
        elements[item.name] = item_info
        
        print(f"  {get_action_icon(item_info['action'])} {item.name} "
              f"({item_info['size_mb']} MB) - {item_info['action']}")
    
    return elements


def analyze_extensions_directory(ext_dir: Path) -> Dict:
    """Analyse des extensions avec leurs données"""
    
    extensions = {}
    
    for ext_path in ext_dir.iterdir():
        if not ext_path.is_dir() or ext_path.name.startswith('.'):
            continue
            
        ext_info = {
            'path': str(ext_path),
            'has_data': False,
            'data_size_mb': 0,
            'config_files': [],
            'action': 'ANALYZE'
        }
        
        # Rechercher dossier data/ dans l'extension
        data_subdir = ext_path / 'data'
        if data_subdir.exists():
            ext_info['has_data'] = True
            ext_info['data_size_mb'] = calculate_directory_size(data_subdir)
            
            # Journal de bord = DELETE data/
            if ext_path.name == 'journal_de_bord':
                ext_info['action'] = 'DELETE_DATA'
        
        # Rechercher fichiers de configuration
        for config_file in ext_path.glob('**/*.json'):
            if 'config' in config_file.name.lower() or 'settings' in config_file.name.lower():
                ext_info['config_files'].append(str(config_file))
        
        extensions[ext_path.name] = ext_info
        
        action_text = "DELETE data/" if ext_info['action'] == 'DELETE_DATA' else ext_info['action']
        print(f"  {get_action_icon(ext_info['action'])} {ext_path.name} "
              f"({ext_info['data_size_mb']} MB) - {action_text}")
    
    return extensions


def analyze_memory_system() -> Dict:
    """Analyse spécifique du système de mémoire"""
    
    memory_info = {
        'sqlite_files': [],
        'faiss_files': [],
        'backup_files': [],
        'founder_memories_found': [],
        'total_memories': 0,
        'founder_memories_count': 0
    }
    
    # Analyser les fichiers SQLite
    for db_file in Path("data").glob("**/*.db"):
        db_info = {
            'path': str(db_file),
            'size_mb': round(db_file.stat().st_size / 1024 / 1024, 2)
        }
        
        # Essayer de compter les enregistrements
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # Chercher table memories
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='memories'")
            if cursor.fetchone():
                cursor.execute("SELECT COUNT(*) FROM memories")
                db_info['memory_count'] = cursor.fetchone()[0]
                memory_info['total_memories'] += db_info['memory_count']
                
                # Chercher souvenirs fondateurs
                founder_ids = [
                    "MC2-20250823-021",
                    "MC2-20250823-052", 
                    "MC2-20250823-020",
                    "usr-75e2ec09-cdbe-4f05-a729-3aa1a8aa8112"
                ]
                
                for founder_id in founder_ids:
                    cursor.execute("SELECT id FROM memories WHERE id = ?", (founder_id,))
                    if cursor.fetchone():
                        memory_info['founder_memories_found'].append(founder_id)
                        memory_info['founder_memories_count'] += 1
            
            conn.close()
            
        except Exception as e:
            db_info['error'] = str(e)
            
        memory_info['sqlite_files'].append(db_info)
        print(f"  💾 {db_file.name}: {db_info.get('memory_count', '?')} souvenirs "
              f"({db_info['size_mb']} MB)")
    
    # Analyser les fichiers FAISS
    for faiss_file in Path("data").glob("**/*.index"):
        faiss_info = {
            'path': str(faiss_file),
            'size_mb': round(faiss_file.stat().st_size / 1024 / 1024, 2)
        }
        memory_info['faiss_files'].append(faiss_info)
        print(f"  🔍 {faiss_file.name}: Index vectoriel ({faiss_info['size_mb']} MB)")
    
    return memory_info


def verify_founder_memories() -> List[Dict]:
    """Vérifie la présence des souvenirs fondateurs"""
    
    founder_ids = [
        "MC2-20250823-021",
        "MC2-20250823-052", 
        "MC2-20250823-020",
        "usr-75e2ec09-cdbe-4f05-a729-3aa1a8aa8112"
    ]
    
    found_memories = []
    
    try:
        # Vérifier dans memories.db
        db_path = Path("data/memory/memories.db")
        if db_path.exists():
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            for founder_id in founder_ids:
                cursor.execute("SELECT id, titre, score_impact FROM memories WHERE id = ?", (founder_id,))
                result = cursor.fetchone()
                
                memory_info = {
                    'id': founder_id,
                    'found': result is not None,
                    'titre': result[1] if result else None,
                    'score_impact': result[2] if result else None
                }
                
                found_memories.append(memory_info)
                
                status = "✅ TROUVÉ" if memory_info['found'] else "❌ MANQUANT"
                print(f"  {status} {founder_id}")
                if memory_info['found']:
                    print(f"    📝 {memory_info['titre']} (Score: {memory_info['score_impact']})")
            
            conn.close()
            
    except Exception as e:
        print(f"  ⚠️ Erreur lors de la vérification : {e}")
    
    return found_memories


def calculate_directory_size(directory: Path) -> float:
    """Calcule la taille d'un dossier en MB"""
    total_size = 0
    try:
        for file in directory.rglob("*"):
            if file.is_file():
                total_size += file.stat().st_size
    except Exception:
        pass
    return round(total_size / 1024 / 1024, 2)


def count_files_recursive(directory: Path) -> int:
    """Compte le nombre de fichiers dans un dossier"""
    count = 0
    try:
        for file in directory.rglob("*"):
            if file.is_file():
                count += 1
    except Exception:
        pass
    return count


def calculate_total_size() -> float:
    """Calcule la taille totale des données OGMA"""
    total = 0
    for directory in [Path("data"), Path("extensions")]:
        if directory.exists():
            total += calculate_directory_size(directory)
    return total


def get_action_icon(action: str) -> str:
    """Retourne l'icône correspondant à l'action"""
    icons = {
        'DELETE': '🗑️',
        'RESET': '🔄', 
        'PRESERVE': '💾',
        'DELETE_DATA': '🗂️',
        'ANALYZE': '❓',
        'unknown': '❔'
    }
    return icons.get(action, '❔')


def generate_recommendations(analysis: Dict) -> List[str]:
    """Génère des recommandations basées sur l'analyse"""
    
    recommendations = []
    
    # Vérifier souvenirs fondateurs
    founder_count = analysis['memory_analysis']['founder_memories_count']
    if founder_count < 4:
        recommendations.append(
            f"⚠️ Seulement {founder_count}/4 souvenirs fondateurs trouvés. "
            "Vérifier la liste des IDs à préserver."
        )
    
    # Vérifier taille des données
    total_size = analysis['total_size_mb']
    if total_size > 100:
        recommendations.append(
            f"💾 Données volumineuses ({total_size} MB). "
            "Prévoir un système de compression pour les sauvegardes."
        )
    
    # Vérifier présence d'instructions par défaut
    if 'instructions_defaults.json' not in analysis['data_directory']:
        recommendations.append(
            "📋 Fichier instructions_defaults.json créé. "
            "Backup des instructions par défaut disponible."
        )
    
    return recommendations


def save_analysis_report(analysis: Dict):
    """Sauvegarde le rapport d'analyse"""
    
    report_path = Path("diagnostic_profil_unique.json")
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    
    print(f"\n📋 Rapport sauvegardé : {report_path}")


if __name__ == "__main__":
    try:
        analysis = analyze_ogma_data()
        
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ")
        print("=" * 60)
        
        print(f"📂 Dossier data/ : {len(analysis['data_directory'])} éléments")
        print(f"🧩 Extensions : {len(analysis['extensions_directory'])} trouvées")
        print(f"🧠 Mémoires totales : {analysis['memory_analysis']['total_memories']}")
        print(f"🏛️ Souvenirs fondateurs : {analysis['memory_analysis']['founder_memories_count']}/4")
        print(f"💾 Taille totale : {analysis['total_size_mb']} MB")
        
        if analysis['recommendations']:
            print(f"\n⚠️ RECOMMANDATIONS :")
            for rec in analysis['recommendations']:
                print(f"  {rec}")
        
        save_analysis_report(analysis)
        
        print(f"\n🎯 PROCHAINE ÉTAPE : Implémentation du ProfileManager selon SPECIFICATION_PROFIL_UNIQUE_OGMA.md")
        
    except Exception as e:
        print(f"❌ ERREUR : {e}")
        import traceback
        traceback.print_exc()