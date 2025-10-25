"""
Téléchargeur d'images pour l'extension Web Navigator

Gère le téléchargement et la sauvegarde d'images depuis le web
"""

import requests
import time
from typing import Tuple, Optional, Dict, Any
from urllib.parse import urlparse
from pathlib import Path
import hashlib
import mimetypes

class ImageFetcher:
    """Gestionnaire de téléchargement d'images web"""
    
    def __init__(self, config):
        self.config = config
        self.last_request_time = 0
        self.session = requests.Session()
        
        # Configuration session pour images
        self.session.headers.update({
            'User-Agent': self.config.get_user_agent(),
            'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Connection': 'keep-alive'
        })
        
        print("[IMAGE-FETCHER] 🖼️ Téléchargeur d'images initialisé")
    
    def _enforce_rate_limit(self):
        """Applique le rate limiting entre requêtes"""
        rate_limit = self.config.get_rate_limit()
        time_since_last = time.time() - self.last_request_time
        
        if time_since_last < rate_limit:
            sleep_time = rate_limit - time_since_last
            print(f"[IMAGE-FETCHER] ⏱️ Rate limiting: attente {sleep_time:.1f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _is_domain_allowed(self, url: str) -> bool:
        """Vérifie si le domaine de l'URL est autorisé"""
        try:
            domain = urlparse(url).netloc.lower()
            return self.config.is_domain_allowed(domain)
        except Exception:
            return False
    
    def _get_image_extension(self, url: str, content_type: str) -> str:
        """Détermine l'extension d'image appropriée"""
        
        # D'abord essayer depuis l'URL
        url_path = urlparse(url).path.lower()
        for ext in self.config.get_supported_image_formats():
            if url_path.endswith(f'.{ext}'):
                return ext
        
        # Ensuite depuis le content-type
        mime_to_ext = {
            'image/jpeg': 'jpg',
            'image/jpg': 'jpg', 
            'image/png': 'png',
            'image/gif': 'gif',
            'image/webp': 'webp',
            'image/svg+xml': 'svg'
        }
        
        if content_type in mime_to_ext:
            return mime_to_ext[content_type]
        
        # Fallback
        return 'jpg'
    
    def _generate_filename(self, url: str, content_type: str) -> str:
        """Génère un nom de fichier unique pour l'image"""
        
        # Créer un hash de l'URL pour éviter les doublons
        url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
        
        # Obtenir extension
        extension = self._get_image_extension(url, content_type)
        
        # Timestamp pour unicité
        timestamp = int(time.time())
        
        return f"web_image_{timestamp}_{url_hash}.{extension}"
    
    def _is_valid_image_format(self, content_type: str, url: str) -> bool:
        """Vérifie si le format d'image est supporté"""
        
        # Vérifier par content-type
        supported_mimes = {
            'image/jpeg', 'image/jpg', 'image/png', 
            'image/gif', 'image/webp', 'image/svg+xml'
        }
        
        if content_type in supported_mimes:
            return True
        
        # Vérifier par extension URL
        url_path = urlparse(url).path.lower()
        supported_extensions = self.config.get_supported_image_formats()
        
        for ext in supported_extensions:
            if url_path.endswith(f'.{ext}'):
                return True
        
        return False
    
    def download_image(self, url: str) -> Tuple[Optional[str], Optional[str], Optional[Dict[str, Any]]]:
        """
        Télécharge une image depuis une URL
        
        Args:
            url: URL de l'image à télécharger
            
        Returns:
            Tuple[chemin_fichier_local, erreur, métadonnées]
        """
        
        if not self.config.is_image_analysis_enabled():
            return None, "Analyse d'images désactivée dans la configuration", None
        
        if not self._is_domain_allowed(url):
            domain = urlparse(url).netloc
            return None, f"Domaine '{domain}' non autorisé dans la configuration", None
        
        print(f"[IMAGE-FETCHER] 🖼️ Téléchargement: {url[:80]}...")
        
        try:
            # Appliquer rate limiting
            self._enforce_rate_limit()
            
            # Effectuer une requête HEAD d'abord pour vérifier le type
            head_response = self.session.head(
                url,
                timeout=10,  # Timeout plus court pour HEAD
                allow_redirects=True
            )
            
            # Vérifier le content-type depuis HEAD
            content_type = head_response.headers.get('content-type', '').split(';')[0].lower()
            content_length = head_response.headers.get('content-length')
            
            if not self._is_valid_image_format(content_type, url):
                return None, f"Format d'image non supporté: {content_type}", None
            
            # Vérifier la taille si disponible
            if content_length:
                size = int(content_length)
                max_size = self.config.get_max_image_size_bytes()
                if size > max_size:
                    return None, f"Image trop volumineuse: {size/1024/1024:.1f}MB > {max_size/1024/1024:.1f}MB", None
            
            # Télécharger l'image complète
            response = self.session.get(
                url,
                timeout=self.config.get_request_timeout(),
                stream=True  # Stream pour éviter de charger tout en mémoire
            )
            
            response.raise_for_status()
            
            # Vérifier à nouveau le content-type de la réponse complète
            final_content_type = response.headers.get('content-type', '').split(';')[0].lower()
            if not self._is_valid_image_format(final_content_type, url):
                return None, f"Format d'image non supporté après téléchargement: {final_content_type}", None
            
            # Lire le contenu avec limite de taille
            max_size = self.config.get_max_image_size_bytes()
            image_data = b''
            
            for chunk in response.iter_content(chunk_size=8192):
                image_data += chunk
                if len(image_data) > max_size:
                    return None, f"Image trop volumineuse lors du téléchargement: > {max_size/1024/1024:.1f}MB", None
            
            # Sauvegarder l'image si configuré
            local_path = None
            if self.config.get("save_downloaded_images", True):
                local_path = self._save_image_to_disk(image_data, url, final_content_type)
            
            # Préparer les métadonnées
            metadata = {
                "url": url,
                "content_type": final_content_type,
                "size_bytes": len(image_data),
                "size_mb": len(image_data) / (1024 * 1024),
                "local_path": local_path,
                "downloaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "filename": Path(local_path).name if local_path else None
            }
            
            print(f"[IMAGE-FETCHER] ✅ Image téléchargée: {len(image_data)/1024:.1f}KB")
            if local_path:
                print(f"[IMAGE-FETCHER] 💾 Sauvegardée: {local_path}")
            
            return local_path, None, metadata
            
        except requests.exceptions.Timeout:
            return None, f"Timeout après {self.config.get_request_timeout()}s", None
        
        except requests.exceptions.ConnectionError:
            return None, "Erreur de connexion - image inaccessible", None
        
        except requests.exceptions.HTTPError as e:
            return None, f"Erreur HTTP {e.response.status_code}: {e.response.reason}", None
        
        except Exception as e:
            return None, f"Erreur inattendue: {str(e)}", None
    
    def _save_image_to_disk(self, image_data: bytes, url: str, content_type: str) -> Optional[str]:
        """Sauvegarde l'image sur le disque"""
        
        try:
            # Obtenir le répertoire de sauvegarde
            save_dir = self.config.get_image_save_path()
            
            # Générer nom de fichier unique
            filename = self._generate_filename(url, content_type)
            filepath = save_dir / filename
            
            # Écrire l'image
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            return str(filepath)
            
        except Exception as e:
            print(f"[IMAGE-FETCHER] ❌ Erreur sauvegarde: {e}")
            return None
    
    def get_image_info(self, url: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Obtient des informations sur une image sans la télécharger complètement
        
        Args:
            url: URL de l'image
            
        Returns:
            Tuple[infos, erreur]
        """
        
        try:
            # Appliquer rate limiting
            self._enforce_rate_limit()
            
            # Requête HEAD pour obtenir les headers
            response = self.session.head(
                url,
                timeout=10,
                allow_redirects=True
            )
            
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '').split(';')[0].lower()
            content_length = response.headers.get('content-length')
            
            info = {
                "url": url,
                "content_type": content_type,
                "is_valid_format": self._is_valid_image_format(content_type, url),
                "size_bytes": int(content_length) if content_length else None,
                "size_mb": int(content_length) / (1024 * 1024) if content_length else None,
                "extension": self._get_image_extension(url, content_type)
            }
            
            return info, None
            
        except Exception as e:
            return None, f"Erreur obtention infos image: {str(e)}"
    
    def close(self):
        """Ferme la session de téléchargement"""
        if self.session:
            self.session.close()
            print("[IMAGE-FETCHER] 🔒 Session de téléchargement fermée")