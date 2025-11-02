#!/usr/bin/env python3
"""
💾 FILE SAVER - Sauvegarde fichiers markdown dans uploads/
===========================================================

Gère la sauvegarde de fichiers .md avec:
- Nommage par titre document
- Gestion collisions noms (suffixes _1, _2, etc.)
- Validation sécurité filesystem
- Stats sauvegarde

USAGE:
    saver = FileSaver(
        uploads_dir="data/uploads",
        debug=True
    )
    
    path = saver.save(
        content="# Mon Document\n\nContenu...",
        title="guide_python"
    )
    
    if path:
        print(f"Sauvegardé: {path}")
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Optional


class FileSaver:
    """Gestionnaire sauvegarde fichiers markdown."""
    
    def __init__(self, uploads_dir: str = "data/uploads", debug: bool = False):
        """
        Initialise le saver.
        
        Args:
            uploads_dir: Répertoire destination
            debug: Active logs debug
        """
        self.uploads_dir = Path(uploads_dir)
        self.debug = debug
        
        # Créer répertoire si inexistant
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        
        # Stats
        self._stats = {
            'files_saved': 0,
            'total_bytes': 0,
            'last_save': None
        }
    
    def save(
        self,
        content: str,
        title: str = "document",
        extension: str = "md"
    ) -> Optional[str]:
        """
        Sauvegarde contenu dans fichier.
        
        Args:
            content: Contenu markdown à sauvegarder
            title: Titre/nom fichier (sans extension)
            extension: Extension fichier (défaut: md)
            
        Returns:
            Chemin absolu fichier sauvegardé ou None si erreur
        """
        if not content or not isinstance(content, str):
            if self.debug:
                print("[SAVER] Contenu vide ou invalide")
            return None
        
        # Nettoyer titre
        safe_title = self._sanitize_filename(title)
        
        # Générer nom fichier unique
        filename = self._generate_unique_filename(safe_title, extension)
        
        # Chemin complet
        filepath = self.uploads_dir / filename
        
        try:
            # Sauvegarder fichier
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Mettre à jour stats
            file_size = len(content.encode('utf-8'))
            self._stats['files_saved'] += 1
            self._stats['total_bytes'] += file_size
            self._stats['last_save'] = datetime.now()
            
            if self.debug:
                print(f"[SAVER] ✅ Fichier sauvegardé: {filepath}")
                print(f"[SAVER] Taille: {file_size} bytes")
            
            return str(filepath)
            
        except Exception as e:
            print(f"[SAVER] ❌ Erreur sauvegarde: {e}")
            return None
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Nettoie nom fichier pour sécurité filesystem.
        
        Args:
            filename: Nom fichier brut
            
        Returns:
            Nom fichier safe
        """
        if not filename:
            return "document"
        
        # Caractères interdits Windows/Linux
        invalid_chars = r'<>:"/\|?*'
        
        # Remplacer caractères invalides par underscore
        safe_name = ''.join(
            c if c not in invalid_chars else '_'
            for c in filename
        )
        
        # Retirer espaces début/fin
        safe_name = safe_name.strip()
        
        # Limiter longueur (max 200 chars)
        if len(safe_name) > 200:
            safe_name = safe_name[:200]
        
        # Si vide après nettoyage
        if not safe_name:
            safe_name = "document"
        
        return safe_name
    
    def _generate_unique_filename(
        self,
        base_name: str,
        extension: str
    ) -> str:
        """
        Génère nom fichier unique (gestion collisions).
        
        Args:
            base_name: Nom base fichier
            extension: Extension (sans point)
            
        Returns:
            Nom fichier unique
        """
        # Retirer extension si déjà présente
        if base_name.endswith(f'.{extension}'):
            base_name = base_name[:-len(extension)-1]
        
        # Essayer nom direct
        filename = f"{base_name}.{extension}"
        filepath = self.uploads_dir / filename
        
        if not filepath.exists():
            return filename
        
        # Si collision, ajouter suffixe numérique
        counter = 1
        while True:
            filename = f"{base_name}_{counter}.{extension}"
            filepath = self.uploads_dir / filename
            
            if not filepath.exists():
                if self.debug:
                    print(f"[SAVER] Collision détectée, suffixe: _{counter}")
                return filename
            
            counter += 1
            
            # Sécurité: max 1000 tentatives
            if counter > 1000:
                # Fallback: timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                return f"{base_name}_{timestamp}.{extension}"
    
    def get_statistics(self) -> dict:
        """
        Retourne statistiques sauvegarde.
        
        Returns:
            Dict avec métriques
        """
        stats = self._stats.copy()
        
        # Ajouter info répertoire
        stats['uploads_dir'] = str(self.uploads_dir)
        stats['dir_exists'] = self.uploads_dir.exists()
        
        # Formater last_save
        if stats['last_save']:
            stats['last_save_formatted'] = stats['last_save'].strftime('%Y-%m-%d %H:%M:%S')
        
        return stats
    
    def list_saved_files(self, limit: int = 10) -> list:
        """
        Liste fichiers sauvegardés récents.
        
        Args:
            limit: Nombre max fichiers à retourner
            
        Returns:
            Liste dicts avec infos fichiers
        """
        if not self.uploads_dir.exists():
            return []
        
        files = []
        
        for filepath in self.uploads_dir.glob("*.md"):
            stat = filepath.stat()
            
            files.append({
                'name': filepath.name,
                'path': str(filepath),
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'created': datetime.fromtimestamp(stat.st_ctime)
            })
        
        # Trier par date modification décroissante
        files.sort(key=lambda x: x['modified'], reverse=True)
        
        return files[:limit]


if __name__ == "__main__":
    # Tests
    saver = FileSaver(uploads_dir="data/uploads", debug=True)
    
    # Test 1: Sauvegarde simple
    content1 = """# Guide Python

## Introduction

Python est un langage de programmation puissant et facile à apprendre.

## Caractéristiques

- Syntaxe claire
- Grande communauté
- Nombreuses bibliothèques
"""
    
    print("TEST 1: Sauvegarde simple")
    path1 = saver.save(content1, title="guide_python")
    print(f"Chemin: {path1}\n")
    
    # Test 2: Collision nom (même titre)
    print("TEST 2: Collision nom")
    path2 = saver.save(content1, title="guide_python")
    print(f"Chemin: {path2}\n")
    
    # Test 3: Titre avec caractères spéciaux
    print("TEST 3: Caractères spéciaux")
    path3 = saver.save(content1, title="Guide/Python:v2.0")
    print(f"Chemin: {path3}\n")
    
    # Stats
    print("STATS:")
    stats = saver.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Liste fichiers
    print("\nFICHIERS RÉCENTS:")
    recent = saver.list_saved_files(limit=5)
    for f in recent:
        print(f"  - {f['name']} ({f['size']} bytes)")
