"""
Client DuckDuckGo pour l'extension Web Navigator OGMA

Recherche gratuite sans clé API via la librairie duckduckgo_search.
Interface identique à SerperClient pour un remplacement transparent.
"""

import asyncio
from typing import Dict, Any, Optional, List, Tuple

from .web_scraper import WebContentScraper


class DuckDuckGoClient:
    """
    Client DuckDuckGo — recherche web gratuite, sans clé API.
    Méthodes identiques à SerperClient pour remplacement transparent.
    """

    # Correspondance (lang, country) → région DDG
    _REGION_MAP = {
        ("fr", "fr"): "fr-fr",
        ("en", "us"): "us-en",
        ("en", "gb"): "uk-en",
        ("de", "de"): "de-de",
        ("es", "es"): "es-es",
        ("it", "it"): "it-it",
    }
    _DEFAULT_REGION = "wt-wt"  # Mondial, sans ciblage géographique

    def __init__(self, config):
        self.config = config
        self.scraper = WebContentScraper()
        print("[DDG-CLIENT] Client DuckDuckGo initialisé (gratuit, sans clé API)")

    # ──────────────────────────────────────────────────────────────────────
    # Helpers internes
    # ──────────────────────────────────────────────────────────────────────

    def _get_region(self) -> str:
        lang = self.config.get_language()
        country = self.config.get_country()
        return self._REGION_MAP.get((lang, country), self._DEFAULT_REGION)

    def _get_ddgs(self):
        """Retourne une instance DDGS (lève ImportError si lib absente)."""
        try:
            from duckduckgo_search import DDGS
            return DDGS()
        except ImportError:
            raise ImportError(
                "La librairie 'duckduckgo_search' n'est pas installée. "
                "Lancez : pip install duckduckgo_search"
            )

    # ──────────────────────────────────────────────────────────────────────
    # Méthodes principales (interface compatible SerperClient)
    # ──────────────────────────────────────────────────────────────────────

    def search_web(self, query: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Recherche web DDG.
        Retourne un dict au format Serper : {"organic": [...]}
        """
        if not query or not query.strip():
            return None, "Requête vide"
        try:
            ddgs = self._get_ddgs()
            results = list(ddgs.text(
                query.strip(),
                region=self._get_region(),
                max_results=self.config.get_results_per_query()
            ))
            if not results:
                return None, "Aucun résultat DuckDuckGo"
            response = {
                "organic": [
                    {
                        "title": r.get("title", ""),
                        "link": r.get("href", ""),
                        "snippet": r.get("body", ""),
                    }
                    for r in results
                ]
            }
            return response, None
        except Exception as e:
            return None, f"Erreur DuckDuckGo: {str(e)}"

    def search_news(self, query: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Actualités DDG.
        Retourne un dict au format Serper : {"news": [...]}
        """
        if not query or not query.strip():
            return None, "Requête vide"
        try:
            ddgs = self._get_ddgs()
            results = list(ddgs.news(
                query.strip(),
                region=self._get_region(),
                max_results=self.config.get_results_per_query()
            ))
            if not results:
                return None, "Aucune actualité DuckDuckGo"
            response = {
                "news": [
                    {
                        "title": r.get("title", ""),
                        "link": r.get("url", ""),
                        "snippet": r.get("body", ""),
                        "date": r.get("date", ""),
                        "source": r.get("source", ""),
                    }
                    for r in results
                ]
            }
            return response, None
        except Exception as e:
            return None, f"Erreur DuckDuckGo News: {str(e)}"

    def search_images(self, query: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Images DDG.
        Retourne un dict au format Serper : {"images": [...]}
        """
        if not query or not query.strip():
            return None, "Requête vide"
        try:
            ddgs = self._get_ddgs()
            results = list(ddgs.images(
                query.strip(),
                region=self._get_region(),
                max_results=10
            ))
            if not results:
                return None, "Aucune image DuckDuckGo"
            response = {
                "images": [
                    {
                        "title": r.get("title", "Image sans titre"),
                        "imageUrl": r.get("image", ""),
                        "link": r.get("url", ""),
                        "thumbnail": r.get("thumbnail", ""),
                        "source": r.get("source", ""),
                    }
                    for r in results
                ]
            }
            return response, None
        except Exception as e:
            return None, f"Erreur DuckDuckGo Images: {str(e)}"

    # ──────────────────────────────────────────────────────────────────────
    # Formatage (même sortie textuelle que SerperClient)
    # ──────────────────────────────────────────────────────────────────────

    def format_web_results_for_ogma(self, response_data: Dict[str, Any], query: str) -> str:
        """Formate les résultats web DDG pour OGMA — même format sortant que SerperClient."""
        formatted = f"**🌐 Synthèse Web (DuckDuckGo):** {query}\n\n"

        if "organic" in response_data:
            insights = []
            sources = []
            for i, result in enumerate(response_data["organic"][:6], 1):
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                link = result.get("link", "")
                if snippet:
                    clean = snippet.replace("...", "").strip()
                    if clean:
                        insights.append(clean)
                if title and link:
                    domain = link.split("/")[2] if "/" in link else link
                    sources.append(f"[{i}] {title} ({domain})")

            if insights:
                formatted += "**🧠 Points clés identifiés:**\n"
                unique: List[str] = []
                for ins in insights:
                    if len(ins) > 30 and not any(ins[:50] in ex for ex in unique):
                        unique.append(ins)
                for ins in unique[:4]:
                    formatted += f"• {ins}\n"
                formatted += "\n"

            if sources:
                formatted += "**📚 Sources consultées:**\n"
                for src in sources[:4]:
                    formatted += f"{src}\n"
                formatted += "\n"

        formatted += (
            "**💡 En résumé:** Ces informations sont maintenant intégrées dans mon contexte "
            "et peuvent enrichir notre conversation sur ce sujet."
        )
        return formatted

    def format_news_results_for_ogma(self, response_data: Dict[str, Any], query: str) -> str:
        """Formate les actualités DDG pour OGMA — même format sortant que SerperClient."""
        formatted = f"**📰 Actualités (DuckDuckGo):** {query}\n\n"

        if "news" in response_data:
            recent_news = []
            key_sources = set()
            for article in response_data["news"][:6]:
                title = article.get("title", "")
                snippet = article.get("snippet", "")
                source = article.get("source", "")
                date = article.get("date", "")
                if snippet and len(snippet) > 20:
                    recent_news.append({
                        "content": snippet.replace("...", "").strip(),
                        "source": source,
                        "date": date,
                        "title": title
                    })
                    if source:
                        key_sources.add(source)

            if recent_news:
                formatted += "**🔥 Actualités récentes identifiées:**\n"
                for news in recent_news[:4]:
                    formatted += f"• **{news['title']}** ({news['source']})\n"
                    formatted += f"  {news['content']}\n"
                    if news["date"]:
                        formatted += f"  📅 {news['date']}\n"
                    formatted += "\n"
                if key_sources:
                    formatted += f"**📡 Sources média:** {', '.join(list(key_sources)[:4])}\n\n"
                formatted += (
                    "**💡 En résumé:** Ces actualités récentes sont maintenant intégrées "
                    "dans mon contexte pour enrichir notre discussion."
                )
            else:
                formatted += "**⚠️ Aucune actualité récente détaillée trouvée sur ce sujet.**"
        else:
            formatted += "**⚠️ Aucune actualité trouvée pour cette recherche.**"

        return formatted

    def format_images_results_for_ogma(self, response_data: Dict[str, Any], query: str) -> str:
        """Formate les images DDG pour OGMA — même format sortant que SerperClient."""
        formatted = f'[RECHERCHE IMAGES DUCKDUCKGO] Résultats pour : "{query}"\n\n'

        if "images" in response_data:
            formatted += "**🖼️ Images trouvées :**\n\n"
            for i, image in enumerate(response_data["images"][:8], 1):
                title = image.get("title", "Image sans titre")
                image_url = image.get("imageUrl", "")
                source = image.get("source", "Source inconnue")
                formatted += f"**{i}. {title}**\n"
                formatted += f"🖼️ {image_url}\n"
                formatted += f"📰 Source: {source}\n\n"

        return formatted

    # ──────────────────────────────────────────────────────────────────────
    # Scraping intelligent (même signature que SerperClient)
    # ──────────────────────────────────────────────────────────────────────

    async def search_with_intelligent_scraping(
        self, query: str, top_pages: int = 5
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Recherche DDG + scraping intelligent des top pages.
        Interface identique à SerperClient.search_with_intelligent_scraping.
        """
        # Étape 1 — recherche de base
        response, error = await asyncio.to_thread(self.search_web, query)
        if error or not response:
            return None, error or "Pas de résultats"

        organic = response.get("organic", [])
        if not organic:
            return self.format_web_results_for_ogma(response, query), None

        # Étape 2 — scraping async des top pages
        urls_to_scrape = [r["link"] for r in organic[:top_pages] if r.get("link")]
        scraped_content = []
        for url in urls_to_scrape:
            try:
                scraped, _ = await asyncio.to_thread(self.scraper.scrape_url, url)
                if scraped and isinstance(scraped, dict):
                    text = scraped.get("content", scraped.get("text", ""))
                    if text and len(text) > 200:
                        scraped_content.append({"url": url, "content": text[:3000]})
            except Exception:
                continue

        if not scraped_content:
            # Fallback vers résultats simples si impossible à scraper
            return self.format_web_results_for_ogma(response, query), None

        # Étape 3 — synthèse enrichie
        enriched = f"**🌐 Synthèse Web enrichie (DuckDuckGo):** {query}\n\n"
        enriched += "**🧠 Contenu extrait des sources:**\n\n"
        for i, sc in enumerate(scraped_content[:3], 1):
            domain = sc["url"].split("/")[2] if "/" in sc["url"] else sc["url"]
            enriched += f"**Source {i} ({domain}):**\n{sc['content'][:800]}\n\n"

        # Ajouter la synthèse basique en dessous
        enriched += "---\n" + self.format_web_results_for_ogma(response, query)
        return enriched, None

    def close(self):
        """Ferme les ressources (compatibilité interface SerperClient)."""
        print("[DDG-CLIENT] Client DuckDuckGo fermé")
