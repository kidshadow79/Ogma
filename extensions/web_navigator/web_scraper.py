#!/usr/bin/env python3
"""
🌐 Web Content Scraper pour OGMA
Module de scraping intelligent qui extrait le contenu principal des pages web
pour alimenter l'IA avec des informations substantielles.
"""

import asyncio
import aiohttp
import re
import time
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    print("[WEB-SCRAPER] ⚠️ BeautifulSoup non disponible - utilisation parsing basique")

@dataclass
class ScrapedContent:
    """Contenu scrapé d'une page web"""
    url: str
    title: str
    content: str
    word_count: int
    scrape_time: float
    success: bool
    error: Optional[str] = None

class WebContentScraper:
    """
    Scraper intelligent pour extraire le contenu principal des pages web
    Optimisé pour donner du contenu substantiel à l'IA OGMA
    """
    
    def __init__(self, config=None):
        self.config = config
        self.session = None
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        self.timeout = 8.0  # Timeout par page
        self.max_content_length = 8000  # Maximum 8000 caractères par page
        self.min_content_length = 100   # Minimum 100 caractères pour être valide
        
    async def __aenter__(self):
        """Context manager pour la session aiohttp"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={'User-Agent': self.user_agent}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Fermeture de la session"""
        if self.session:
            await self.session.close()
    
    def _clean_text(self, text: str) -> str:
        """Nettoie et formate le texte extrait"""
        if not text:
            return ""
        
        # Supprime les retours à la ligne multiples
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Supprime les espaces multiples
        text = re.sub(r' +', ' ', text)
        
        # Supprime les caractères de contrôle
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        # Limite la longueur
        if len(text) > self.max_content_length:
            text = text[:self.max_content_length] + "..."
        
        return text.strip()
    
    def _extract_content_with_bs4(self, html: str, url: str) -> Tuple[str, str]:
        """Extrait le contenu avec BeautifulSoup (méthode avancée)"""
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extraire le titre
        title_tag = soup.find('title')
        title = title_tag.get_text().strip() if title_tag else ""
        
        # Supprimer les éléments indésirables
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 
                           'aside', 'iframe', 'noscript', 'form', 'button']):
            element.decompose()
        
        # Supprimer les commentaires
        for element in soup.find_all(string=lambda text: isinstance(text, str) and text.strip().startswith('<!--')):
            element.extract()
        
        # Rechercher le contenu principal par priorité
        main_content = None
        
        # 1. Chercher des balises sémantiques
        for tag in ['main', 'article']:
            main_content = soup.find(tag)
            if main_content:
                break
        
        # 2. Chercher par classes/IDs communs
        if not main_content:
            selectors = [
                '.content', '.main-content', '.article-content', 
                '.post-content', '.entry-content', '#content',
                '#main', '#article', '.article-body', '.story-body'
            ]
            for selector in selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    break
        
        # 3. Fallback : plus grand bloc de texte
        if not main_content:
            # Chercher le div avec le plus de texte
            divs = soup.find_all('div')
            if divs:
                main_content = max(divs, key=lambda d: len(d.get_text()))
        
        # 4. Dernier recours : body entier
        if not main_content:
            main_content = soup.find('body') or soup
        
        # Extraire le texte
        content = main_content.get_text(separator=' ', strip=True)
        
        return title, content
    
    def _extract_content_basic(self, html: str, url: str) -> Tuple[str, str]:
        """Extrait le contenu avec parsing basique (fallback)"""
        
        # Extraire le titre
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else ""
        
        # Supprimer les scripts et styles
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.IGNORECASE | re.DOTALL)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.IGNORECASE | re.DOTALL)
        
        # Supprimer les balises HTML
        content = re.sub(r'<[^>]+>', ' ', html)
        
        # Décoder les entités HTML basiques
        content = content.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        content = content.replace('&quot;', '"').replace('&#39;', "'").replace('&nbsp;', ' ')
        
        return title, content
    
    async def scrape_page(self, url: str) -> ScrapedContent:
        """
        Scrape une page web et extrait son contenu principal
        
        Args:
            url: URL de la page à scraper
            
        Returns:
            ScrapedContent avec le contenu extrait
        """
        
        start_time = time.time()
        
        try:
            print(f"[WEB-SCRAPER] 🔍 Scraping: {url}")
            
            if not self.session:
                raise Exception("Session non initialisée - utiliser comme context manager")
            
            # Vérifier l'URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise Exception(f"URL invalide: {url}")
            
            # Requête HTTP
            async with self.session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")
                
                # Vérifier le content-type
                content_type = response.headers.get('content-type', '').lower()
                if 'text/html' not in content_type:
                    raise Exception(f"Type de contenu non supporté: {content_type}")
                
                # Lire le contenu
                html = await response.text()
                
                if not html or len(html) < 100:
                    raise Exception("Contenu HTML trop court")
            
            # Extraction du contenu
            if BS4_AVAILABLE:
                title, content = self._extract_content_with_bs4(html, url)
            else:
                title, content = self._extract_content_basic(html, url)
            
            # Nettoyage
            title = self._clean_text(title)
            content = self._clean_text(content)
            
            # Validation
            if len(content) < self.min_content_length:
                raise Exception(f"Contenu trop court: {len(content)} caractères")
            
            scrape_time = time.time() - start_time
            
            print(f"[WEB-SCRAPER] ✅ Succès: {len(content)} chars en {scrape_time:.1f}s")
            
            return ScrapedContent(
                url=url,
                title=title,
                content=content,
                word_count=len(content.split()),
                scrape_time=scrape_time,
                success=True
            )
            
        except Exception as e:
            scrape_time = time.time() - start_time
            error_msg = str(e)
            
            print(f"[WEB-SCRAPER] ❌ Échec {url}: {error_msg}")
            
            return ScrapedContent(
                url=url,
                title="",
                content="",
                word_count=0,
                scrape_time=scrape_time,
                success=False,
                error=error_msg
            )
    
    async def scrape_multiple(self, urls: List[str], max_concurrent: int = 3) -> List[ScrapedContent]:
        """
        Scrape plusieurs pages en parallèle
        
        Args:
            urls: Liste des URLs à scraper
            max_concurrent: Nombre maximum de scraping simultanés
            
        Returns:
            Liste des contenus scrapés
        """
        
        print(f"[WEB-SCRAPER] 🚀 Scraping {len(urls)} pages (max {max_concurrent} concurrents)")
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def scrape_with_semaphore(url):
            async with semaphore:
                return await self.scrape_page(url)
        
        tasks = [scrape_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Traiter les exceptions
        scraped_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"[WEB-SCRAPER] ❌ Exception pour {urls[i]}: {result}")
                scraped_results.append(ScrapedContent(
                    url=urls[i],
                    title="",
                    content="",
                    word_count=0,
                    scrape_time=0,
                    success=False,
                    error=str(result)
                ))
            else:
                scraped_results.append(result)
        
        success_count = sum(1 for r in scraped_results if r.success)
        total_words = sum(r.word_count for r in scraped_results if r.success)
        
        print(f"[WEB-SCRAPER] 📊 Résultat: {success_count}/{len(urls)} pages scrapées, {total_words} mots récupérés")
        
        return scraped_results

# Fonction utilitaire pour les tests
async def test_scraper():
    """Test du scraper avec quelques URLs d'exemple"""
    
    test_urls = [
        "https://fr.wikipedia.org/wiki/Intelligence_artificielle",
        "https://www.lemonde.fr/",
        "https://www.microsoft.com/"
    ]
    
    async with WebContentScraper() as scraper:
        results = await scraper.scrape_multiple(test_urls, max_concurrent=2)
        
        for result in results:
            print(f"\n{'✅' if result.success else '❌'} {result.url}")
            if result.success:
                print(f"   Titre: {result.title[:100]}...")
                print(f"   Contenu: {len(result.content)} chars, {result.word_count} mots")
                print(f"   Temps: {result.scrape_time:.1f}s")
            else:
                print(f"   Erreur: {result.error}")

if __name__ == "__main__":
    # Installer les dépendances si nécessaire
    try:
        import aiohttp
    except ImportError:
        print("❌ aiohttp manquant - installez avec: pip install aiohttp")
        exit(1)
    
    # Test du scraper
    asyncio.run(test_scraper())
    
    def _enforce_rate_limit(self):
        """Applique le rate limiting entre requêtes"""
        rate_limit = self.config.get_rate_limit()
        time_since_last = time.time() - self.last_request_time
        
        if time_since_last < rate_limit:
            sleep_time = rate_limit - time_since_last
            print(f"[WEB-SCRAPER] ⏱️ Rate limiting: attente {sleep_time:.1f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _is_domain_allowed(self, url: str) -> bool:
        """Vérifie si le domaine de l'URL est autorisé"""
        try:
            domain = urlparse(url).netloc.lower()
            return self.config.is_domain_allowed(domain)
        except Exception:
            return False
    
    def _extract_text_content(self, html_content: str, url: str) -> Dict[str, Any]:
        """Extrait le contenu textuel et métadonnées d'une page HTML"""
        
        if not BS4_AVAILABLE:
            # Fallback simple sans BeautifulSoup
            return self._extract_text_simple(html_content, url)
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Supprimer les éléments non pertinents
            for element in soup(['script', 'style', 'nav', 'footer', 'aside', 'ads']):
                element.decompose()
            
            # Extraire métadonnées
            title = ""
            if soup.title:
                title = soup.title.get_text(strip=True)
            
            description = ""
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                description = meta_desc.get('content', '').strip()
            
            # Extraire le contenu principal
            # Chercher le contenu principal dans l'ordre de priorité
            main_content = None
            
            # 1. Balises sémantiques
            for tag in ['main', 'article', '[role="main"]']:
                main_content = soup.select_one(tag)
                if main_content:
                    break
            
            # 2. Fallback sur le body complet
            if not main_content:
                main_content = soup.body or soup
            
            # Extraire le texte en préservant structure
            text_content = []
            
            # Extraire titres et paragraphes avec structure
            for element in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div', 'li']):
                text = element.get_text(strip=True)
                if text and len(text) > 10:  # Ignorer texte trop court
                    
                    # Ajouter préfixe pour les titres
                    if element.name.startswith('h'):
                        level = element.name[1]
                        text_content.append(f"{'#' * int(level)} {text}")
                    else:
                        text_content.append(text)
            
            # Extraire les liens importants
            links = []
            for link in main_content.find_all('a', href=True)[:10]:  # Max 10 liens
                link_text = link.get_text(strip=True)
                link_url = urljoin(url, link['href'])
                if link_text and len(link_text) > 3:
                    links.append(f"[{link_text}]({link_url})")
            
            # Assembler le résultat
            full_text = "\n\n".join(text_content)
            
            # Nettoyer et limiter la taille
            full_text = self._clean_text(full_text)
            
            return {
                "title": title,
                "description": description,
                "content": full_text,
                "links": links,
                "word_count": len(full_text.split()),
                "char_count": len(full_text)
            }
            
        except Exception as e:
            print(f"[WEB-SCRAPER] ❌ Erreur extraction BeautifulSoup: {e}")
            return self._extract_text_simple(html_content, url)
    
    def _extract_text_simple(self, html_content: str, url: str) -> Dict[str, Any]:
        """Extraction simple sans BeautifulSoup (fallback)"""
        
        # Extraction basique avec regex
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else ""
        
        # Supprimer scripts et styles
        text = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Supprimer toutes les balises HTML
        text = re.sub(r'<[^>]+>', '', text)
        
        # Nettoyer le texte
        text = self._clean_text(text)
        
        return {
            "title": title,
            "description": "",
            "content": text,
            "links": [],
            "word_count": len(text.split()),
            "char_count": len(text)
        }
    
    def _clean_text(self, text: str) -> str:
        """Nettoie et optimise le texte extrait"""
        
        # Décoder les entités HTML communes
        html_entities = {
            '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"',
            '&apos;': "'", '&nbsp;': ' ', '&mdash;': '—', '&ndash;': '–'
        }
        
        for entity, char in html_entities.items():
            text = text.replace(entity, char)
        
        # Nettoyer espaces et sauts de ligne
        text = re.sub(r'\s+', ' ', text)  # Espaces multiples -> espace unique
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Sauts de ligne multiples -> double
        
        # Supprimer lignes vides et espaces début/fin
        lines = [line.strip() for line in text.split('\n')]
        lines = [line for line in lines if line]  # Supprimer lignes vides
        
        return '\n'.join(lines).strip()
    
    def scrape_url(self, url: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Scrape une URL et retourne le contenu extrait
        
        Args:
            url: URL à scraper
            
        Returns:
            Tuple[contenu_extrait, erreur]
        """
        
        if not self.config.is_web_scraping_enabled():
            return None, "Web scraping désactivé dans la configuration"
        
        if not self._is_domain_allowed(url):
            domain = urlparse(url).netloc
            return None, f"Domaine '{domain}' non autorisé dans la configuration"
        
        print(f"[WEB-SCRAPER] 🌐 Scraping: {url[:80]}...")
        
        try:
            # Appliquer rate limiting
            self._enforce_rate_limit()
            
            # Effectuer la requête
            response = self.session.get(
                url,
                timeout=self.config.get_request_timeout(),
                verify=self.config.get("verify_ssl", True),
                allow_redirects=self.config.get("follow_redirects", True)
            )
            
            response.raise_for_status()
            
            # Vérifier la taille du contenu
            content_length = len(response.content)
            max_size = self.config.get_max_page_size_bytes()
            
            if content_length > max_size:
                return None, f"Page trop volumineuse: {content_length/1024/1024:.1f}MB > {max_size/1024/1024:.1f}MB"
            
            # Vérifier que c'est du HTML
            content_type = response.headers.get('content-type', '').lower()
            if 'html' not in content_type:
                return None, f"Type de contenu non supporté: {content_type}"
            
            # Extraire le contenu
            html_content = response.text
            extracted = self._extract_text_content(html_content, url)
            
            # Ajouter métadonnées de la requête
            extracted.update({
                "url": url,
                "status_code": response.status_code,
                "content_type": content_type,
                "content_length": content_length,
                "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
            })
            
            print(f"[WEB-SCRAPER] ✅ Scraping réussi: {extracted['word_count']} mots extraits")
            
            return extracted, None
            
        except requests.exceptions.Timeout:
            return None, f"Timeout après {self.config.get_request_timeout()}s"
        
        except requests.exceptions.ConnectionError:
            return None, "Erreur de connexion - site inaccessible"
        
        except requests.exceptions.HTTPError as e:
            return None, f"Erreur HTTP {e.response.status_code}: {e.response.reason}"
        
        except Exception as e:
            return None, f"Erreur inattendue: {str(e)}"
    
    def format_for_ai(self, extracted_data: Dict[str, Any]) -> str:
        """Formate le contenu extrait pour l'IA conversationnelle"""
        
        title = extracted_data.get("title", "")
        description = extracted_data.get("description", "")
        content = extracted_data.get("content", "")
        links = extracted_data.get("links", [])
        word_count = extracted_data.get("word_count", 0)
        url = extracted_data.get("url", "")
        
        # Construire le texte formaté pour l'IA
        formatted = f"[NAVIGATION WEB] Contenu de la page : {url}\n\n"
        
        if title:
            formatted += f"**Titre :** {title}\n\n"
        
        if description:
            formatted += f"**Description :** {description}\n\n"
        
        formatted += f"**Contenu principal :**\n{content}\n\n"
        
        if links:
            formatted += f"**Liens trouvés :**\n"
            for link in links[:5]:  # Max 5 liens
                formatted += f"- {link}\n"
            formatted += "\n"
        
        formatted += f"**Statistiques :** {word_count} mots extraits\n"
        
        return formatted
    
    def close(self):
        """Ferme la session de scraping"""
        if self.session:
            self.session.close()
            print("[WEB-SCRAPER] 🔒 Session de scraping fermée")