# Extension Web Navigator — Documentation Exhaustive

**Dossier** : `extensions/web_navigator/`
**Rôle** : Recherche web intelligente intégrée dans le chat OGMA — détection automatique des requêtes de recherche, scraping de contenu filtré, injection du résultat dans le contexte IA.

---

## Architecture — Fichiers

| Fichier | Classe | Rôle |
|---------|--------|------|
| `__init__.py` | — | API publique + singleton |
| `config.py` | `WebNavigatorConfig` | Configuration |
| `commands.py` | `WebNavigatorCommands` | Détection phrases magiques |
| `serper_client.py` | `SerperClient` | Client Serper.dev (recherche primaire) |
| `ddg_client.py` | `DuckDuckGoClient` | Client DuckDuckGo (fallback gratuit) |
| `scraper.py` | `WebContentScraper` | Extraction contenu pages |
| `image_fetcher.py` | `ImageFetcher` | Récupération images |
| `ui_components.py` | `WebNavigatorUI` | Interface configuration |

---

## `config.py` — Classe `WebNavigatorConfig`

| Clé | Défaut | Description |
|-----|--------|-------------|
| `extension_enabled` | `True` | Activé par défaut |
| `search_engine` | `"auto"` | `"serper"`, `"ddg"`, ou `"auto"` (Serper si clé dispo, sinon DDG) |
| `serper_api_key` | `""` | Clé API Serper.dev |
| `max_results` | `5` | Résultats de recherche max |
| `max_scraped_pages` | `3` | Pages à scraper en détail |
| `max_content_per_page` | `2000` | Chars max par page scrapée |
| `total_max_content` | `6000` | Chars max total injection |
| `request_timeout` | `10` | Timeout par requête (secondes) |
| `include_images` | `False` | Récupérer images dans résultats |
| `max_images` | `3` | Images max si activé |
| `cache_enabled` | `True` | Cache résultats (TTL 1h) |
| `cache_ttl_minutes` | `60` | Durée cache |
| `inject_mode` | `"context"` | `"context"` (system) ou `"message"` (dans chat) |
| `blocked_domains` | (voir ci-dessous) | Domaines ignorés |

**`blocked_domains`** (par défaut) : `["youtube.com", "facebook.com", "twitter.com", "instagram.com", "tiktok.com", "linkedin.com", "reddit.com"]`

---

## `commands.py` — Classe `WebNavigatorCommands`

### Détection — 20+ patterns

| Catégorie | Exemples de phrases |
|-----------|---------------------|
| Recherche explicite | `"cherche"`, `"recherche"`, `"trouve"`, `"look for"`, `"search"` |
| Questions ouvertes | `"qu'est-ce que"`, `"c'est quoi"`, `"qui est"`, `"comment"`, `"pourquoi"` suivi d'un sujet externe |
| Actualité | `"dernières nouvelles de"`, `"actu"`, `"qu'est-il arrivé à"` |
| Prix/Disponibilité | `"prix de"`, `"combien coûte"`, `"est disponible"` |
| Définition | `"définition de"`, `"signifie"`, `"veut dire"` |

**Condition de déclenchement** : patterns détectés **ET** sujet externe (pas une question introspective sur l'IA).

### `clean_search_query(text)` → `str`

1. Retire phrases magiques de déclenchement
2. Retire guillemets en début/fin
3. Retire 25 mots vides (`le`, `la`, `les`, `du`, `de`, `des`, `un`, `une`, `et`, `est`, ...)
4. Tronque à 25 mots maximum
5. Retourne requête propre

### Méthodes

| Méthode | Description |
|---------|-------------|
| `detect_search_intent(text)` | Retourne `Optional[str]` — requête nettoyée ou `None` |
| `is_introspective_question(text)` | Détecte questions sur l'IA elle-même (ne pas chercher) |
| `extract_search_modifiers(text)` | Options : `{recent: bool, images: bool, detailed: bool}` |

---

## `serper_client.py` — Classe `SerperClient`

**API** : Serper.dev — Google Search API

### `async search_with_intelligent_scraping(query, options)` → `dict`

1. `_serper_search(query)` → top 10 résultats JSON
2. Filtre domaines bloqués (`blocked_domains`)
3. Conserve top `max_results` (défaut 5)
4. Scrape en parallèle les `max_scraped_pages` premières URLs
5. Combine snippets + contenu scrapé
6. Retourne `{results: [], scraped_content: {url: text}, total_chars, query}`

### `_serper_search(query)` 

- POST `https://google.serper.dev/search`
- Headers : `X-API-KEY: {serper_api_key}`, `Content-Type: application/json`
- Body : `{q: query, num: 10, hl: "fr", gl: "fr"}`
- Retourne liste `{title, link, snippet, position}`

### Cache

- Clé cache : `SHA256(query + options)`[:16]
- TTL configurable `cache_ttl_minutes` (défaut 60)
- Stockage : dict en mémoire `_cache = {key: (timestamp, result)}`

---

## `ddg_client.py` — Classe `DuckDuckGoClient`

**Interface identique à `SerperClient`** — remplacement transparent (duck typing).

**Dépendance** : `duckduckgo_search` (`DDGS`)

### `async search_with_intelligent_scraping(query, options)` → `dict`

1. `DDGS().text(query, max_results=10)` (sync, via `asyncio.to_thread`)
2. Filtre domaines bloqués
3. Scrape identique Serper
4. Même format de retour

**Avantage** : 100% gratuit, aucune clé API.  
**Inconvénient** : Qualité résultats légèrement inférieure + rate limiting possible.

---

## `scraper.py` — Classe `WebContentScraper`

**Mode** : asyncio avec `aiohttp.ClientSession` (connexions parallèles)

### `async scrape_urls(urls, max_chars_per_page)` → `dict[str, str]`

Scrape toutes les URLs en parallèle (`asyncio.gather`).

### `async scrape_url(url, max_chars)` → `Optional[str]`

1. GET avec headers user-agent browser simulé
2. Vérifie Content-Type (`text/html` uniquement)
3. BS4 parsing HTML
4. Extraction par priorité :
   - `<main>` → `<article>` → `.content` → `[role="main"]` → `<body>`
5. Nettoyage :
   - Retire scripts, styles, nav, header, footer, aside, ads
   - Normalise espaces blancs
6. Tronque à `max_chars`

### Headers simulés

```python
{
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
    "Accept": "text/html,application/xhtml+xml,...",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br"
}
```

### Timeouts et sécurité

- Timeout total : `request_timeout` (défaut 10s)
- `aiohttp.ClientTimeout(total=timeout)`
- Ignore erreurs SSL : `ssl=False` (nécessaire pour certains sites)
- Max redirect : 5

---

## `image_fetcher.py` — Classe `ImageFetcher`

Récupération d'images depuis URLs de résultats de recherche.

### `async fetch_images(image_urls, max_images)` → `list[ImageData]`

1. HEAD check d'abord (`Content-Type: image/*`, `Content-Length ≤ 5MB`)
2. GET stream si HEAD valide
3. Génère nom fichier : `MD5(url).hex() + extension`
4. Sauvegarde locale optionnelle dans `data/uploads/web_images/`
5. Retourne `[ImageData(url, local_path, base64, mime_type, width, height)]`

---

## `ui_components.py` — Classe `WebNavigatorUI`

### Composants

| Composant | Description |
|-----------|-------------|
| Bouton header `🌐` | Indicateur (actif/inactif) |
| Modal config | Engine, clé Serper, max_results, domaines bloqués, cache TTL |
| Section Test | Champ requête test + résultat live |
| Section Stats | Total recherches, provider utilisé, top requêtes |

---

## `__init__.py` — API Publique

### Singleton : `_web_navigator : Optional[WebNavigatorExtension]`

### Fonctions exposées

| Fonction | Description |
|----------|-------------|
| `initialize_web_navigator(settings_manager)` | Init avec config |
| `is_available()` | `_web_navigator is not None` |
| `is_enabled()` | `config.extension_enabled` |
| `async process_search(query, options)` | Pipeline recherche complet → `str` formaté |
| `async check_message_for_search(user_message)` | Détecte + exécute si phrase magique → `Optional[str]` |
| `get_ui_components()` | Composants header |
| `get_search_stats()` | Stats usage |
| `cleanup()` | Ferme sessions aiohttp |

### `async process_search(query, options)` → `str` (pour injection)

Format de retour :
```
[Résultats web pour: "{query}"]
1. {title} ({url})
   {snippet}
   Contenu: {scraped_text_truncated}

2. ...
[Fin résultats web]
```

---

## Intégration dans `ogma_ng.py`

1. Dans `send_message()`, avant appel IA : `check_message_for_search(user_message)`
2. Si résultat → injecté dans `additional_context` du prompt système
3. L'IA répond en s'appuyant sur les données web fraîches
4. Mode `"message"` (config) → insère résultats comme message système visible dans chat

---

## Fichiers de données

| Chemin | Description |
|--------|-------------|
| `data/web_navigator_config.json` | Configuration persistée |
| `data/uploads/web_images/` | Images web téléchargées (optionnel) |
