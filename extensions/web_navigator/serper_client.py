"""
Client Serper pour l'extension Web Navigator OGMA

Gère toutes les interactions avec l'API Serper pour recherche web, actualités, images
Intègre le scraping intelligent pour extraire le contenu complet des pages
"""

import requests
import time
import asyncio
from typing import Dict, Any, Optional, List, Tuple
import json

from .web_scraper import WebContentScraper

class SerperClient:
    """Client pour l'API Serper - recherche web, actualités, images avec scraping intelligent"""
    
    def __init__(self, config):
        self.config = config
        self.last_request_time = 0
        
        # Headers pour requêtes Serper
        self.headers = {
            'X-API-KEY': self.config.get_serper_api_key(),
            'Content-Type': 'application/json',
            'User-Agent': 'OGMA-WebNavigator-Serper/1.0'
        }
        
        print("[SERPER-CLIENT] 🌐 Client Serper initialisé avec scraping intelligent")
    
    def _respect_rate_limit(self):
        """Respecte le délai entre requêtes"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        rate_limit = self.config.get_rate_limit()
        
        if time_since_last < rate_limit:
            wait_time = rate_limit - time_since_last
            print(f"[SERPER-CLIENT] ⏱️ Rate limiting: attente {wait_time:.1f}s")
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, payload: Dict[str, Any]) -> Tuple[Optional[Dict], Optional[str]]:
        """Effectue une requête à l'API Serper"""
        
        if not self.config.has_valid_api_key():
            return None, "Clé API Serper manquante ou invalide"
        
        self._respect_rate_limit()
        
        url = f"{self.config.get_serper_base_url()}/{endpoint}"
        
        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=self.config.get_request_timeout()
            )
            
            if response.status_code == 200:
                return response.json(), None
            elif response.status_code == 401:
                return None, "Clé API Serper invalide ou expirée"
            elif response.status_code == 429:
                return None, "Quota API Serper dépassé"
            else:
                return None, f"Erreur API Serper: {response.status_code} - {response.text[:200]}"
                
        except requests.exceptions.Timeout:
            return None, f"Timeout après {self.config.get_request_timeout()}s"
        except requests.exceptions.RequestException as e:
            return None, f"Erreur réseau: {str(e)}"
        except json.JSONDecodeError:
            return None, "Réponse API Serper invalide (JSON malformé)"
        except Exception as e:
            return None, f"Erreur inattendue: {str(e)}"
    
    async def search_with_intelligent_scraping(self, query: str, top_pages: int = 5) -> Tuple[Optional[str], Optional[str]]:
        """
        Recherche avec scraping intelligent des Top N pages
        
        Args:
            query: Requête de recherche
            top_pages: Nombre de pages à scraper (max 5)
            
        Returns:
            Tuple[contenu_enrichi, erreur]
        """
        
        print(f"[SERPER-CLIENT] 🧠 Recherche intelligente: '{query}' (Top {top_pages})")
        
        # 1. Recherche Serper normale
        serper_response, error = self.search_web(query)
        if error:
            return None, error
        
        if not serper_response:
            return None, "Aucun résultat Serper reçu"
        
        # Vérifier la structure de la réponse
        if 'organic' not in serper_response:
            print(f"[SERPER-CLIENT] ⚠️ Pas de résultats organiques, clés disponibles: {list(serper_response.keys())}")
            # Essayer de retourner au moins les résultats Serper formatés
            return self.format_web_results_for_ogma(serper_response, query), None
        
        organic_results = serper_response['organic']
        if not organic_results:
            print(f"[SERPER-CLIENT] ⚠️ Liste de résultats organiques vide")
            return self.format_web_results_for_ogma(serper_response, query), None
        
        # 2. Extraire les URLs du Top N
        organic_results_slice = organic_results[:top_pages]
        urls_to_scrape = []
        
        print(f"[SERPER-CLIENT] 🔍 Analyse de {len(organic_results_slice)} résultats organiques")
        
        for i, result in enumerate(organic_results_slice, 1):
            url = result.get('link')
            title = result.get('title', 'Sans titre')
            
            print(f"[SERPER-CLIENT] 📄 Résultat {i}: {title[:50]}...")
            print(f"[SERPER-CLIENT] 🔗 URL: {url}")
            
            if url and url.startswith(('http://', 'https://')):
                # Vérifier que l'URL n'est pas un domaine bloqué/problématique
                blocked_domains = ['youtube.com', 'facebook.com', 'twitter.com', 'linkedin.com']
                is_blocked = any(domain in url.lower() for domain in blocked_domains)
                
                if not is_blocked:
                    urls_to_scrape.append(url)
                    print(f"[SERPER-CLIENT] ✅ URL ajoutée pour scraping")
                else:
                    print(f"[SERPER-CLIENT] ⚠️ URL ignorée (domaine bloqué)")
            else:
                print(f"[SERPER-CLIENT] ❌ URL invalide ou non HTTP(S)")
        
        if not urls_to_scrape:
            print(f"[SERPER-CLIENT] ⚠️ Aucune URL valide à scraper, fallback vers résultats Serper normaux")
            return self.format_web_results_for_ogma(serper_response, query), None
        
        print(f"[SERPER-CLIENT] 📄 {len(urls_to_scrape)} pages à scraper")
        
        # 3. Scraping intelligent asynchrone
        scraped_contents = []
        try:
            async with WebContentScraper() as scraper:
                scraped_results = await scraper.scrape_multiple(urls_to_scrape, max_concurrent=2)
                
                # Garder seulement les scraping réussis
                for result in scraped_results:
                    if result.success and len(result.content) > 200:  # Contenu substantiel
                        scraped_contents.append(result)
        
        except Exception as e:
            print(f"[SERPER-CLIENT] ❌ Erreur scraping: {e}")
            # Continuer avec les résultats Serper normaux si le scraping échoue
            return self.format_web_results_for_ogma(serper_response, query), None
        
        # 4. Formatage pour l'IA
        if not scraped_contents:
            print("[SERPER-CLIENT] ⚠️ Aucun contenu scrapé - fallback vers résultats Serper")
            return self.format_web_results_for_ogma(serper_response, query), None
        
        # 5. Création du contenu enrichi
        enriched_content = self._format_intelligent_results(query, serper_response, scraped_contents)
        
        print(f"[SERPER-CLIENT] ✅ Contenu enrichi créé: {len(enriched_content)} caractères")
        return enriched_content, None
    
    def _format_intelligent_results(self, query: str, serper_response: Dict, scraped_contents: List) -> str:
        """
        Formate les résultats enrichis avec le contenu scrapé
        
        Args:
            query: Requête originale
            serper_response: Réponse Serper
            scraped_contents: Contenus scrapés
            
        Returns:
            Contenu formaté pour l'IA
        """
        
        formatted = f"**🧠 RECHERCHE INTELLIGENTE ENRICHIE:** {query}\n\n"
        
        # 1. RÉSUMÉ EXÉCUTIF
        formatted += "**📊 RÉSUMÉ EXÉCUTIF:**\n"
        total_words = sum(content.word_count for content in scraped_contents)
        success_rate = len(scraped_contents) / len(serper_response.get('organic', [])[:5]) * 100
        formatted += f"• {len(scraped_contents)} pages analysées en profondeur\n"
        formatted += f"• {total_words:,} mots de contenu substantiel récupérés\n"
        formatted += f"• Taux de succès du scraping: {success_rate:.0f}%\n\n"
        
        # 2. INFORMATIONS CLÉS (SERPER)
        if 'answerBox' in serper_response:
            ab = serper_response['answerBox']
            if 'answer' in ab:
                formatted += "**💡 RÉPONSE DIRECTE:**\n"
                formatted += f"{ab['answer']}\n\n"
        
        # 3. CONTENU DÉTAILLÉ DES PAGES SCRAPÉES
        formatted += "**📚 ANALYSE APPROFONDIE DES SOURCES:**\n\n"
        
        for i, content in enumerate(scraped_contents, 1):
            formatted += f"**Source {i}: {content.title or 'Sans titre'}**\n"
            formatted += f"🌐 URL: {content.url}\n"
            formatted += f"📝 Contenu: {content.word_count} mots\n"
            formatted += f"⏱️ Temps d'extraction: {content.scrape_time:.1f}s\n\n"
            
            # Contenu principal (limité pour éviter la surcharge)
            content_preview = content.content[:1500] if len(content.content) > 1500 else content.content
            formatted += f"**Extrait principal:**\n{content_preview}\n"
            
            if len(content.content) > 1500:
                formatted += "...(contenu tronqué pour la synthèse)\n"
            
            formatted += "\n" + "="*50 + "\n\n"
        
        # 4. SYNTHÈSE FINALE
        formatted += "**🎯 SYNTHÈSE POUR L'IA:**\n"
        formatted += f"Cette recherche a permis d'extraire du contenu substantiel ({total_words:,} mots) "
        formatted += f"depuis {len(scraped_contents)} sources fiables. Le contenu ci-dessus fournit "
        formatted += "une base factuelle solide pour répondre à la question ou approfondir le sujet. "
        formatted += "Toutes les informations sont maintenant intégrées dans le contexte de conversation.\n\n"
        
        # 5. RECHERCHES CONNEXES
        if 'relatedSearches' in serper_response:
            related = serper_response['relatedSearches'][:3]
            if related:
                formatted += "**🔍 POUR APPROFONDIR DAVANTAGE:**\n"
                for search in related:
                    formatted += f"• {search.get('query', '')}\n"
                formatted += "\n"
        
        return formatted
    
    def search_web(self, query: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Effectue une recherche web via Serper
        
        Args:
            query: Requête de recherche
            
        Returns:
            Tuple[résultats_serper, erreur]
        """
        
        if not query or not query.strip():
            return None, "Requête de recherche vide"
        
        payload = {
            "q": query.strip(),
            "num": self.config.get_results_per_query(),
            "hl": self.config.get_language(),
            "gl": self.config.get_country()
        }
        
        print(f"[SERPER-CLIENT] 🔍 Recherche web: '{query}'")
        return self._make_request("search", payload)
    
    def search_news(self, query: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Effectue une recherche d'actualités via Serper
        
        Args:
            query: Requête de recherche
            
        Returns:
            Tuple[résultats_serper, erreur]
        """
        
        if not query or not query.strip():
            return None, "Requête de recherche vide"
        
        payload = {
            "q": query.strip(),
            "num": min(self.config.get_results_per_query(), 10),  # Max 10 pour news
            "hl": self.config.get_language(),
            "gl": self.config.get_country()
        }
        
        print(f"[SERPER-CLIENT] 📰 Recherche actualités: '{query}'")
        return self._make_request("news", payload)
    
    def search_images(self, query: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Effectue une recherche d'images via Serper
        
        Args:
            query: Requête de recherche
            
        Returns:
            Tuple[résultats_serper, erreur]
        """
        
        if not query or not query.strip():
            return None, "Requête de recherche vide"
        
        payload = {
            "q": query.strip(),
            "num": min(self.config.get_results_per_query(), 20),  # Max 20 pour images
            "hl": self.config.get_language(),
            "gl": self.config.get_country()
        }
        
        print(f"[SERPER-CLIENT] 🖼️ Recherche images: '{query}'")
        return self._make_request("images", payload)
    
    def search_scholar(self, query: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Effectue une recherche académique via Serper Scholar
        
        Args:
            query: Requête de recherche
            
        Returns:
            Tuple[résultats_serper, erreur]
        """
        
        if not query or not query.strip():
            return None, "Requête de recherche vide"
        
        payload = {
            "q": query.strip(),
            "num": min(self.config.get_results_per_query(), 10),  # Max 10 pour scholar
            "hl": self.config.get_language()
        }
        
        print(f"[SERPER-CLIENT] 🎓 Recherche académique: '{query}'")
        return self._make_request("scholar", payload)
    
    def format_web_results_for_ogma(self, serper_response: Dict[str, Any], query: str) -> str:
        """
        Formate les résultats de recherche web pour OGMA avec synthèse intelligente
        
        Args:
            serper_response: Réponse JSON de Serper
            query: Requête originale
            
        Returns:
            Texte synthétisé et actionnable pour l'IA OGMA
        """
        
        formatted = f"**🌐 Synthèse Web:** {query}\n\n"
        
        # 1. INFORMATIONS CLÉS (Knowledge Graph + Answer Box)
        key_info = []
        
        # Knowledge Graph si disponible
        if 'knowledgeGraph' in serper_response:
            kg = serper_response['knowledgeGraph']
            if 'title' in kg and 'description' in kg:
                key_info.append(f"**{kg['title']}:** {kg['description']}")
            if 'attributes' in kg:
                for key, value in kg['attributes'].items():
                    key_info.append(f"• {key}: {value}")
        
        # Answer Box si disponible
        if 'answerBox' in serper_response:
            ab = serper_response['answerBox']
            if 'answer' in ab:
                key_info.append(f"**Réponse directe:** {ab['answer']}")
            elif 'snippet' in ab:
                key_info.append(f"**Information clé:** {ab['snippet']}")
        
        if key_info:
            formatted += "**📖 Informations essentielles:**\n"
            formatted += "\n".join(key_info) + "\n\n"
        
        # 2. SYNTHÈSE DES RÉSULTATS ORGANIQUES
        if 'organic' in serper_response:
            insights = []
            sources = []
            
            for i, result in enumerate(serper_response['organic'][:6], 1):  # Max 6 résultats
                title = result.get('title', '')
                snippet = result.get('snippet', '')
                link = result.get('link', '')
                
                if snippet:
                    # Extraire l'information clé du snippet (sans formatage)
                    clean_snippet = snippet.replace("...", "").strip()
                    if clean_snippet:
                        insights.append(clean_snippet)
                
                # Garder les sources pour référence
                if title and link:
                    domain = link.split('/')[2] if '/' in link else link
                    sources.append(f"[{i}] {title} ({domain})")
            
            if insights:
                formatted += "**🧠 Points clés identifiés:**\n"
                # Regrouper les insights similaires et éviter les doublons
                unique_insights = []
                for insight in insights:
                    if len(insight) > 30 and not any(insight[:50] in existing for existing in unique_insights):
                        unique_insights.append(insight)
                
                for insight in unique_insights[:4]:  # Max 4 insights
                    formatted += f"• {insight}\n"
                formatted += "\n"
            
            if sources:
                formatted += "**📚 Sources consultées:**\n"
                for source in sources[:4]:  # Max 4 sources
                    formatted += f"{source}\n"
                formatted += "\n"
        
        # 3. PISTES D'APPROFONDISSEMENT
        if 'relatedSearches' in serper_response:
            related = serper_response['relatedSearches'][:3]  # Max 3 suggestions
            if related:
                formatted += "**� Pour approfondir:**\n"
                for search in related:
                    formatted += f"• {search.get('query', '')}\n"
                formatted += "\n"
        
        # 4. RÉSUMÉ ACTIONNABLE
        formatted += "**💡 En résumé:** Ces informations sont maintenant intégrées dans mon contexte et peuvent enrichir notre conversation sur ce sujet."
        
        return formatted
    
    def format_news_results_for_ogma(self, serper_response: Dict[str, Any], query: str) -> str:
        """
        Formate les résultats d'actualités pour OGMA avec synthèse intelligente
        
        Args:
            serper_response: Réponse JSON de Serper News
            query: Requête originale
            
        Returns:
            Texte synthétisé pour l'IA OGMA
        """
        
        formatted = f"**📰 Actualités:** {query}\n\n"
        
        if 'news' in serper_response:
            # Analyser les articles pour extraire les tendances
            recent_news = []
            key_sources = set()
            
            for article in serper_response['news'][:6]:  # Max 6 articles
                title = article.get('title', '')
                snippet = article.get('snippet', '')
                source = article.get('source', '')
                date = article.get('date', '')
                
                if snippet:
                    # Nettoyer et extraire l'info clé
                    clean_snippet = snippet.replace("...", "").strip()
                    if clean_snippet and len(clean_snippet) > 20:
                        recent_news.append({
                            'content': clean_snippet,
                            'source': source,
                            'date': date,
                            'title': title
                        })
                        key_sources.add(source)
            
            if recent_news:
                formatted += "**🔥 Actualités récentes identifiées:**\n"
                for i, news in enumerate(recent_news[:4], 1):  # Max 4 actualités
                    formatted += f"• **{news['title']}** ({news['source']})\n"
                    formatted += f"  {news['content']}\n"
                    if news['date']:
                        formatted += f"  📅 {news['date']}\n"
                    formatted += "\n"
                
                if key_sources:
                    formatted += f"**� Sources média:** {', '.join(list(key_sources)[:4])}\n\n"
                
                formatted += "**💡 En résumé:** Ces actualités récentes sont maintenant intégrées dans mon contexte pour enrichir notre discussion sur ce sujet d'actualité."
            else:
                formatted += "**⚠️ Aucune actualité récente détaillée trouvée sur ce sujet.**"
        else:
            formatted += "**⚠️ Aucune actualité trouvée pour cette recherche.**"
        
        return formatted
    
    def format_images_results_for_ogma(self, serper_response: Dict[str, Any], query: str) -> str:
        """
        Formate les résultats de recherche d'images pour OGMA
        
        Args:
            serper_response: Réponse JSON de Serper Images
            query: Requête originale
            
        Returns:
            Texte formaté pour l'IA OGMA
        """
        
        formatted = f"[RECHERCHE IMAGES SERPER] Résultats pour : \"{query}\"\n\n"
        
        if 'images' in serper_response:
            formatted += f"**🖼️ Images trouvées :**\n\n"
            for i, image in enumerate(serper_response['images'][:8], 1):  # Max 8 images
                title = image.get('title', 'Image sans titre')
                image_url = image.get('imageUrl', '')
                source = image.get('source', 'Source inconnue')
                
                formatted += f"**{i}. {title}**\n"
                formatted += f"🖼️ {image_url}\n"
                formatted += f"📰 Source: {source}\n\n"
        
        return formatted
    
    def close(self):
        """Ferme les ressources du client (placeholder pour compatibilité)"""
        print("[SERPER-CLIENT] 🔒 Client Serper fermé")