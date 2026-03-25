"""
Gestionnaire de commandes pour l'extension Web Navigator avec Serper

Gère les phrases magiques et commandes pour recherche internet via Serper
"""

import asyncio
import time
from typing import Dict, Any, Optional, Tuple
import re
import requests
from pathlib import Path

class WebNavigatorCommands:
    """Gestionnaire de commandes internet avec Serper pour OGMA"""
    
    def __init__(self, config, serper_client, duckduckgo_client=None):
        self.config = config
        self.serper_client = serper_client
        self.duckduckgo_client = duckduckgo_client
        
        # Statistiques d'usage
        self.stats = {
            "web_searches": 0,
            "news_searches": 0,
            "image_searches": 0,
            "scholar_searches": 0,
            "image_downloads": 0,
            "successful_requests": 0,
            "errors": 0,
            "last_used": None
        }
        
        print("[WEB-COMMANDS] 🎮 Gestionnaire de commandes Serper initialisé")

    def _get_active_client(self):
        """
        Retourne le client de recherche actif selon la configuration.
        - 'duckduckgo' : DuckDuckGoClient (gratuit, sans clé API)
        - 'serper'     : SerperClient (par défaut)
        """
        if self.config.get_search_provider() == "duckduckgo" and self.duckduckgo_client:
            return self.duckduckgo_client
        return self.serper_client

    def clean_search_query(self, query: str) -> str:
        """
        Nettoie et optimise une requête de recherche
        
        Args:
            query: Requête brute extraite du message
            
        Returns:
            Requête nettoyée optimisée pour la recherche
        """
        
        if not query or not isinstance(query, str):
            return ""
        
        # Nettoyage de base
        cleaned = query.strip()
        
        # Supprimer les guillemets encadrants (recherche exacte trop restrictive)
        # Cas 1: guillemets parfaits "texte"
        if cleaned.startswith('"') and cleaned.endswith('"') and len(cleaned) > 2:
            cleaned = cleaned[1:-1]
            print(f"[WEB-COMMANDS] 🔓 Guillemets exacts supprimés")
        # Cas 2: guillemets avec ponctuation "texte".
        elif cleaned.startswith('"') and len(cleaned) > 3 and cleaned[-2] == '"':
            cleaned = cleaned[1:-2] + cleaned[-1]  # Garder la ponctuation finale si nécessaire
            print(f"[WEB-COMMANDS] 🔓 Guillemets avec ponctuation supprimés")
        # Cas 3: guillemets ouvrants seulement
        elif cleaned.startswith('"') and cleaned.count('"') == 1:
            cleaned = cleaned[1:]
            print(f"[WEB-COMMANDS] 🔓 Guillemets ouvrants supprimés")
        # Cas 4: guillemets fermants seulement
        elif cleaned.endswith('"') and cleaned.count('"') == 1:
            cleaned = cleaned[:-1]
            print(f"[WEB-COMMANDS] 🔓 Guillemets fermants supprimés")
        
        # Supprimer la ponctuation finale
        cleaned = cleaned.rstrip('.,!?;:')
        
        # Supprimer les mots vides en début/fin qui peuvent nuire à la recherche
        stop_words_start = ['sur', 'de', 'le', 'la', 'les', 'un', 'une', 'des', 'du', 'about', 'on', 'for']
        stop_words_end = ['s\'il', 'stp', 'svp', 'please', 'merci', 'thanks']
        
        words = cleaned.split()
        
        # Supprimer mots vides au début
        while words and words[0].lower() in stop_words_start:
            words.pop(0)
        
        # Supprimer mots vides à la fin
        while words and words[-1].lower() in stop_words_end:
            words.pop()
        
        # Reconstituer la requête
        cleaned = ' '.join(words)
        
        # Supprimer les espaces multiples
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Limiter la longueur (Google/Serper recommande < 32 mots)
        words = cleaned.split()
        if len(words) > 25:
            cleaned = ' '.join(words[:25])
        
        print(f"[WEB-COMMANDS] 🧹 Requête nettoyée: '{query}' → '{cleaned}'")
        
        return cleaned.strip()
    
    def is_internet_request(self, message: str) -> bool:
        """Détecte si le message contient une demande d'accès internet"""
        if not message or not isinstance(message, str):
            return False
        
        message_lower = message.lower().strip()
        
        # Phrases magiques pour recherche internet
        magic_phrases = [
            # Commandes directes
            r'^/web\b',
            r'^/image\b',
            r'^/search\b',
            r'^/news\b',
            
            # Phrases naturelles
            r'\bcher(che|cher)\s+sur\s+internet\b',
            r'\brecher(che|cher)\s+sur\s+internet\b',
            r'\brecherche\s+sur\s+le\s+web\b',
            r'\bcher(che|cher)\s+en\s+ligne\b',
            r'\btrouve\s+sur\s+internet\b',
            r'\bregarder?\s+sur\s+google\b',
            r'\bgooglise?\b',
            r'\bfais\s+une\s+recherche\b',
            r'\brecherche\s+des?\s+images?\b',
            r'\bcher(che|cher)\s+des?\s+images?\b',
            r'\bactualités?\s+sur\b',
            r'\bnews\s+about\b',
            r'\bweb-config\b',
            
            # Phrases pour l'IA elle-même
            r'\bil\s+faut\s+que\s+je\s+recherche\s+sur\s+le\s+net\b',
            r'\bil\s+faut\s+que\s+je\s+recherche\s+sur\s+internet\b',
            r'\bil\s+faut\s+que\s+je\s+cherche\s+sur\s+internet\b',
            r'\bje\s+dois\s+rechercher\s+sur\s+internet\b',
            r'\bje\s+dois\s+chercher\s+sur\s+le\s+web\b',
            r'\bje\s+vais\s+faire\s+une\s+recherche\s+web\b',
            r'\blaissez-moi\s+rechercher\s+sur\s+internet\b',
            r'\bpermettez-moi\s+de\s+faire\s+une\s+recherche\b',
            r'\bil\s+faut\s+que\s+je\s+vérifie\s+sur\s+internet\b',
            r'\bje\s+dois\s+vérifier\s+en\s+ligne\b',
            r'\bje\s+vais\s+vérifier\s+sur\s+le\s+web\b'
        ]
        
        for pattern in magic_phrases:
            if re.search(pattern, message_lower):
                return True
        
        return False
    
    def extract_search_intent_and_query(self, message: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extrait l'intention de recherche et la requête du message
        
        Returns:
            Tuple[type_recherche, requête]
        """
        
        message = message.strip()
        message_lower = message.lower()
        
        # Commandes directes avec /
        direct_commands = {
            r'^/web\s+(.+)$': ('web', 1),
            r'^/search\s+(.+)$': ('web', 1),
            r'^/image\s+(.+)$': ('images', 1),
            r'^/images\s+(.+)$': ('images', 1),
            r'^/news\s+(.+)$': ('news', 1),
            r'^/actualités?\s+(.+)$': ('news', 1),
            r'^/scholar\s+(.+)$': ('scholar', 1),
            r'^/web-config$': ('config', 0),
            r'^/serper-config$': ('config', 0),
        }
        
        for pattern, (search_type, group_idx) in direct_commands.items():
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                if group_idx > 0:
                    query = match.group(group_idx).strip()
                    # Nettoyer la requête extraite
                    cleaned_query = self.clean_search_query(query)
                    return search_type, cleaned_query
                else:
                    return search_type, None
        
        # Phrases naturelles avec extraction de requête
        natural_patterns = [
            (r'cher(?:che|cher)\s+sur\s+internet\s+(.+)', 'web'),
            (r'recher(?:che|cher)\s+sur\s+internet\s+(.+)', 'web'),
            (r'recherche\s+sur\s+le\s+web\s+(.+)', 'web'),
            (r'recherche\s+web\s+(.+)', 'web'),
            (r'cher(?:che|cher)\s+en\s+ligne\s+(.+)', 'web'),
            (r'trouve\s+sur\s+internet\s+(.+)', 'web'),
            (r'regarde?\s+sur\s+google\s+(.+)', 'web'),
            (r'googlise?\s+(.+)', 'web'),
            (r'fais\s+une\s+recherche\s+(?:sur\s+)?(.+)', 'web'),
            (r'recherche\s+des?\s+images?\s+(?:de\s+|sur\s+)?(.+)', 'images'),
            (r'cher(?:che|cher)\s+des?\s+images?\s+(?:de\s+|sur\s+)?(.+)', 'images'),
            (r'actualités?\s+sur\s+(.+)', 'news'),
            (r'news\s+about\s+(.+)', 'news'),
            
            # Patterns pour l'IA elle-même
            (r'il\s+faut\s+que\s+je\s+recherche\s+sur\s+le\s+net\s+(.+)', 'web'),
            (r'il\s+faut\s+que\s+je\s+recherche\s+sur\s+internet\s+(.+)', 'web'),
            (r'il\s+faut\s+que\s+je\s+cherche\s+sur\s+internet\s+(.+)', 'web'),
            (r'je\s+dois\s+rechercher\s+sur\s+internet\s+(.+)', 'web'),
            (r'je\s+dois\s+chercher\s+sur\s+le\s+web\s+(.+)', 'web'),
            (r'je\s+vais\s+faire\s+une\s+recherche\s+web\s+sur\s+(.+)', 'web'),
            (r'laissez-moi\s+rechercher\s+sur\s+internet\s+(.+)', 'web'),
            (r'permettez-moi\s+de\s+faire\s+une\s+recherche\s+sur\s+(.+)', 'web'),
            (r'il\s+faut\s+que\s+je\s+vérifie\s+sur\s+internet\s+(.+)', 'web'),
            (r'je\s+dois\s+vérifier\s+en\s+ligne\s+(.+)', 'web'),
            (r'je\s+vais\s+vérifier\s+sur\s+le\s+web\s+(.+)', 'web'),
        ]
        
        for pattern, search_type in natural_patterns:
            match = re.search(pattern, message_lower)
            if match:
                query = match.group(1).strip()
                # Nettoyer la requête extraite
                cleaned_query = self.clean_search_query(query)
                return search_type, cleaned_query
        
        return None, None
    
    async def download_image_from_url(self, image_url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Télécharge une image depuis une URL vers data/uploads
        
        Args:
            image_url: URL de l'image à télécharger
            
        Returns:
            Tuple[chemin_local, erreur]
        """
        
        try:
            print(f"[WEB-COMMANDS] 📥 Téléchargement image: {image_url}")
            
            # Créer le dossier de destination
            save_path = self.config.get_image_save_path()
            
            # Télécharger l'image
            response = requests.get(
                image_url,
                timeout=self.config.get_request_timeout(),
                headers={'User-Agent': 'OGMA-WebNavigator/1.0'},
                stream=True
            )
            
            if response.status_code != 200:
                return None, f"Erreur HTTP {response.status_code}"
            
            # Générer nom de fichier unique
            filename = f"serper_image_{int(time.time())}_{hash(image_url) % 10000}"
            
            # Détecter extension depuis Content-Type ou URL
            content_type = response.headers.get('content-type', '').lower()
            if 'jpeg' in content_type or 'jpg' in content_type:
                filename += '.jpg'
            elif 'png' in content_type:
                filename += '.png'
            elif 'gif' in content_type:
                filename += '.gif'
            elif 'webp' in content_type:
                filename += '.webp'
            elif image_url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                # Extension depuis URL
                ext = '.' + image_url.split('.')[-1].lower()
                filename += ext
            else:
                filename += '.jpg'  # Par défaut
            
            local_path = save_path / filename
            
            # Écrire le fichier
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"[WEB-COMMANDS] ✅ Image sauvegardée: {local_path}")
            return str(local_path), None
            
        except Exception as e:
            return None, f"Erreur téléchargement: {str(e)}"
    
    async def handle_web_search(self, query: str, intelligent_scraping: bool = True) -> Tuple[str, Optional[str]]:
        """
        Gère une recherche web via Serper avec scraping intelligent optionnel
        
        Args:
            query: Requête de recherche
            intelligent_scraping: Si True, utilise le scraping intelligent du Top 5
            
        Returns:
            Tuple[réponse_pour_ia, None]
        """
        
        self.stats["web_searches"] += 1
        self.stats["last_used"] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        if not self.config.is_web_search_enabled():
            self.stats["errors"] += 1
            return "❌ La recherche web est désactivée ou clé API manquante.", None
        
        print(f"[WEB-COMMANDS] 🔍 Recherche web{'🧠 intelligente' if intelligent_scraping else ''}: '{query}'")

        client = self._get_active_client()
        try:
            if intelligent_scraping:
                # Recherche avec scraping intelligent (Top 5 pages)
                enriched_content, error = await client.search_with_intelligent_scraping(
                    query, top_pages=5
                )
                
                if error:
                    # Fallback vers recherche normale si le scraping échoue
                    print(f"[WEB-COMMANDS] ⚠️ Scraping intelligent échoué, fallback: {error}")
                    intelligent_scraping = False
                else:
                    self.stats["successful_requests"] += 1
                    return enriched_content, None
            
            if not intelligent_scraping:
                # Recherche classique via client actif
                serper_response, error = await asyncio.to_thread(
                    client.search_web, 
                    query
                )
                
                if error:
                    self.stats["errors"] += 1
                    return f"❌ Erreur recherche web: {error}", None
                
                if not serper_response:
                    self.stats["errors"] += 1
                    return "❌ Aucun résultat trouvé.", None
                
                # Succès
                self.stats["successful_requests"] += 1
                
                # Formater pour OGMA
                formatted_content = client.format_web_results_for_ogma(serper_response, query)
                
                return formatted_content, None
            
        except Exception as e:
            self.stats["errors"] += 1
            return f"❌ Erreur inattendue lors de la recherche: {str(e)}", None
    
    async def handle_news_search(self, query: str) -> Tuple[str, Optional[str]]:
        """
        Gère une recherche d'actualités via Serper
        
        Returns:
            Tuple[réponse_pour_ia, None]
        """
        
        self.stats["news_searches"] += 1
        self.stats["last_used"] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        if not self.config.is_news_search_enabled():
            self.stats["errors"] += 1
            return "❌ La recherche d'actualités est désactivée ou clé API manquante.", None
        
        print(f"[WEB-COMMANDS] 📰 Recherche actualités: '{query}'")

        client = self._get_active_client()
        try:
            # Appel News via client actif
            serper_response, error = await asyncio.to_thread(
                client.search_news, 
                query
            )
            
            if error:
                self.stats["errors"] += 1
                return f"❌ Erreur recherche actualités: {error}", None
            
            if not serper_response:
                self.stats["errors"] += 1
                return "❌ Aucune actualité trouvée.", None
            
            # Succès
            self.stats["successful_requests"] += 1
            
            # Formater pour OGMA
            formatted_content = client.format_news_results_for_ogma(serper_response, query)
            
            return formatted_content, None
            
        except Exception as e:
            self.stats["errors"] += 1
            return f"❌ Erreur inattendue lors de la recherche d'actualités: {str(e)}", None
    
    async def handle_image_search(self, query: str) -> Tuple[str, Optional[str]]:
        """
        Gère une recherche d'images via Serper avec option de téléchargement
        
        Returns:
            Tuple[réponse_pour_ia, chemin_fichier_si_téléchargé]
        """
        
        self.stats["image_searches"] += 1
        self.stats["last_used"] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        if not self.config.is_image_search_enabled():
            self.stats["errors"] += 1
            return "❌ La recherche d'images est désactivée ou clé API manquante.", None
        
        print(f"[WEB-COMMANDS] 🖼️ Recherche images: '{query}'")

        client = self._get_active_client()
        try:
            # Appel Images via client actif
            serper_response, error = await asyncio.to_thread(
                client.search_images, 
                query
            )
            
            if error:
                self.stats["errors"] += 1
                return f"❌ Erreur recherche images: {error}", None
            
            if not serper_response or 'images' not in serper_response:
                self.stats["errors"] += 1
                return "❌ Aucune image trouvée.", None
            
            # Succès
            self.stats["successful_requests"] += 1
            
            # Formater pour OGMA
            formatted_content = client.format_images_results_for_ogma(serper_response, query)
            
            # Si option activée, télécharger la première image
            downloaded_path = None
            if self.config.get("save_downloaded_images", True) and serper_response['images']:
                first_image_url = serper_response['images'][0].get('imageUrl')
                if first_image_url:
                    downloaded_path, download_error = await self.download_image_from_url(first_image_url)
                    if downloaded_path:
                        self.stats["image_downloads"] += 1
                        formatted_content += f"\n**� Première image téléchargée :** {downloaded_path}"
                    elif download_error:
                        formatted_content += f"\n**⚠️ Erreur téléchargement première image :** {download_error}"
            
            return formatted_content, downloaded_path
            
        except Exception as e:
            self.stats["errors"] += 1
            return f"❌ Erreur inattendue lors de la recherche d'images: {str(e)}", None
    
    def handle_config_command(self) -> Tuple[str, Optional[str]]:
        """Gère la commande de configuration"""
        
        api_key_status = "✅ Configurée" if self.config.has_valid_api_key() else "❌ Manquante/Invalide"
        
        config_info = f"""⚙️ **Configuration Extension Web Navigator (Serper)**

**État :** {'✅ Activée' if self.config.is_enabled() else '❌ Désactivée'}
**Clé API Serper :** {api_key_status}

**Fonctionnalités :**
- Recherche web : {'✅' if self.config.is_web_search_enabled() else '❌'}
- Recherche actualités : {'✅' if self.config.is_news_search_enabled() else '❌'}  
- Recherche images : {'✅' if self.config.is_image_search_enabled() else '❌'}

**Paramètres :**
- Résultats par requête : {self.config.get_results_per_query()}
- Langue : {self.config.get_language()}
- Pays : {self.config.get_country()}
- Timeout requêtes : {self.config.get_request_timeout()}s
- Délai entre requêtes : {self.config.get_rate_limit()}s

**Sauvegarde images :** {'✅' if self.config.get("save_downloaded_images") else '❌'}
**Dossier images :** {self.config.get("image_save_directory")}

**Statistiques session :**
- Recherches web : {self.stats['web_searches']}
- Recherches actualités : {self.stats['news_searches']}
- Recherches images : {self.stats['image_searches']}
- Images téléchargées : {self.stats['image_downloads']}
- Requêtes réussies : {self.stats['successful_requests']}
- Erreurs : {self.stats['errors']}

*Pour configurer la clé API, allez dans les paramètres OGMA → Web Navigator.*"""

        return config_info, None
    
    async def process_internet_request(self, message: str) -> Tuple[str, Optional[str]]:
        """
        Traite une demande d'accès internet (phrases magiques + commandes)
        
        Args:
            message: Message contenant la demande
            
        Returns:
            Tuple[réponse_pour_chat, chemin_fichier_pour_vision]
        """
        
        if not self.is_internet_request(message):
            return message, None  # Pas une demande internet, laisser passer
        
        search_type, query = self.extract_search_intent_and_query(message)
        
        if not search_type:
            return "❌ Demande internet non reconnue. Utilisez '/web REQUÊTE' ou 'cherche sur internet REQUÊTE'", None
        
        if search_type == "config":
            return self.handle_config_command()
        
        if not query:
            return f"❌ Requête manquante pour {search_type}. Exemple: '/web intelligence artificielle'", None
        
        # Traiter selon le type de recherche
        if search_type == "web":
            return await self.handle_web_search(query)
        elif search_type == "news":
            return await self.handle_news_search(query)
        elif search_type == "images":
            return await self.handle_image_search(query)
        elif search_type == "scholar":
            return await self.handle_scholar_search(query)
        else:
            return f"❌ Type de recherche '{search_type}' non supporté", None
    
    async def handle_scholar_search(self, query: str) -> Tuple[str, Optional[str]]:
        """
        Gère une recherche académique via Serper Scholar
        
        Returns:
            Tuple[réponse_pour_ia, None]
        """
        
        self.stats["scholar_searches"] += 1
        self.stats["last_used"] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        if not self.config.has_valid_api_key():
            self.stats["errors"] += 1
            return "❌ Recherche académique indisponible: clé API manquante.", None
        
        print(f"[WEB-COMMANDS] 🎓 Recherche académique: '{query}'")
        
        try:
            # Appel API Serper Scholar
            serper_response, error = await asyncio.to_thread(
                self.serper_client.search_scholar, 
                query
            )
            
            if error:
                self.stats["errors"] += 1
                return f"❌ Erreur recherche académique: {error}", None
            
            if not serper_response:
                self.stats["errors"] += 1
                return "❌ Aucun article académique trouvé.", None
            
            # Succès
            self.stats["successful_requests"] += 1
            
            # Formatage basique pour Scholar (pas de méthode dédiée dans serper_client)
            formatted = f"[RECHERCHE ACADÉMIQUE SERPER] Résultats pour : \"{query}\"\n\n"
            if 'organic' in serper_response:
                formatted += "**🎓 Articles académiques :**\n\n"
                for i, article in enumerate(serper_response['organic'][:6], 1):
                    title = article.get('title', 'Titre non disponible')
                    link = article.get('link', '')
                    snippet = article.get('snippet', '')
                    
                    formatted += f"**{i}. {title}**\n"
                    formatted += f"🔗 {link}\n"
                    if snippet:
                        formatted += f"📄 {snippet}\n"
                    formatted += "\n"
            
            return formatted, None
            
        except Exception as e:
            self.stats["errors"] += 1
            return f"❌ Erreur inattendue lors de la recherche académique: {str(e)}", None
    
    def get_help_text(self) -> str:
        """Retourne l'aide sur les commandes internet Serper"""
        
        return """🌐 **Web Navigator avec Serper - Aide**

**Commandes directes :**
- `/web REQUÊTE` - Recherche web générale
- `/search REQUÊTE` - Alias pour recherche web  
- `/news REQUÊTE` - Actualités récentes
- `/image REQUÊTE` - Recherche d'images (+ téléchargement)
- `/scholar REQUÊTE` - Articles académiques
- `/web-config` - Configuration et statistiques

**Phrases magiques :**
- "cherche sur internet SUJET"
- "recherche sur internet SUJET"  
- "actualités sur SUJET"
- "cherche des images de SUJET"
- "fais une recherche SUJET"

**Exemples :**
- `/web intelligence artificielle`
- "cherche sur internet dernières nouvelles IA"
- `/news actualités technologie octobre 2025`
- `/image robots humanoïdes`
- "recherche des images de paysages montagne"

**Configuration :** Paramètres OGMA → Web Navigator (clé API Serper requise)"""
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques d'usage"""
        return self.stats.copy()