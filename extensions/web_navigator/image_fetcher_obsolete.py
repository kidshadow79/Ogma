# FICHIER OBSOLÈTE - MIGRATION VERS SERPER

"""  
Ce fichier (image_fetcher.py) est obsolète depuis la migration vers Serper API.

Le téléchargement d'images se fait maintenant via:
- extensions/web_navigator/commands.py → download_image_from_url()
- Recherche d'images via Serper API au lieu de téléchargement direct

Pour télécharger des images:
1. Utiliser '/image REQUÊTE' pour rechercher et télécharger
2. Images sauvées automatiquement dans data/uploads/
3. Commandes: /image robots OR "cherche des images de robots"

Ce fichier sera supprimé dans une version future.
"""

print("[IMAGE-FETCHER] ⚠️ OBSOLÈTE - Utilisez commands.download_image_from_url() maintenant")