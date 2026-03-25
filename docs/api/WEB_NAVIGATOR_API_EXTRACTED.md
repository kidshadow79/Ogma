# 🌐 API Web Navigator - Extraction Complète

**Date**: 2025-11-05
**Extension**: `extensions/web_navigator/`
**Total Méthodes**: 63

---

## 📊 Statistiques Globales

- **Fichiers analysés**: 6
- **Méthodes totales**: 63
- **Méthodes async**: 12
- **Méthodes sync**: 51

---

## 📄 `extension.py`

**Méthodes**: 7

### Classe: `WebNavigatorExtension`

- `__init__()` - ⚙️ Sync - Ligne 30
- `is_enabled()` - ⚙️ Sync - Ligne 64
- `is_web_search_enabled()` - ⚙️ Sync - Ligne 68
- `has_api_key()` - ⚙️ Sync - Ligne 72
- `get_status()` - ⚙️ Sync - Ligne 76
- `process_message()` - 🔄 Async - Ligne 85
- `get_extension_info()` - ⚙️ Sync - Ligne 103

## 📄 `serper_client.py`

**Méthodes**: 10

### Classe: `SerperClient`

- `__init__()` - ⚙️ Sync - Ligne 19
- `search_with_intelligent_scraping()` - 🔄 Async - Ligne 81
- `search_web()` - ⚙️ Sync - Ligne 239
- `search_news()` - ⚙️ Sync - Ligne 263
- `search_images()` - ⚙️ Sync - Ligne 287
- `search_scholar()` - ⚙️ Sync - Ligne 311
- `format_web_results_for_ogma()` - ⚙️ Sync - Ligne 334
- `format_news_results_for_ogma()` - ⚙️ Sync - Ligne 425
- `format_images_results_for_ogma()` - ⚙️ Sync - Ligne 482
- `close()` - ⚙️ Sync - Ligne 509

## 📄 `web_scraper.py`

**Méthodes**: 8

### Fonctions Module

- `test_scraper()` - 🔄 Async - Ligne 287
- `scrape_url()` - ⚙️ Sync - Ligne 467
- `format_for_ai()` - ⚙️ Sync - Ligne 542
- `close()` - ⚙️ Sync - Ligne 573
- `scrape_with_semaphore()` - 🔄 Async - Ligne 255

### Classe: `WebContentScraper`

- `__init__()` - ⚙️ Sync - Ligne 40
- `scrape_page()` - 🔄 Async - Ligne 156
- `scrape_multiple()` - 🔄 Async - Ligne 239

## 📄 `image_fetcher.py`

**Méthodes**: 4

### Classe: `ImageFetcher`

- `__init__()` - ⚙️ Sync - Ligne 18
- `download_image()` - ⚙️ Sync - Ligne 114
- `get_image_info()` - ⚙️ Sync - Ligne 237
- `close()` - ⚙️ Sync - Ligne 278

## 📄 `commands.py`

**Méthodes**: 13

### Classe: `WebNavigatorCommands`

- `__init__()` - ⚙️ Sync - Ligne 17
- `clean_search_query()` - ⚙️ Sync - Ligne 35
- `is_internet_request()` - ⚙️ Sync - Ligne 102
- `extract_search_intent_and_query()` - ⚙️ Sync - Ligne 152
- `download_image_from_url()` - 🔄 Async - Ligne 227
- `handle_web_search()` - 🔄 Async - Ligne 288
- `handle_news_search()` - 🔄 Async - Ligne 351
- `handle_image_search()` - 🔄 Async - Ligne 395
- `handle_config_command()` - ⚙️ Sync - Ligne 451
- `process_internet_request()` - 🔄 Async - Ligne 488
- `handle_scholar_search()` - 🔄 Async - Ligne 525
- `get_help_text()` - ⚙️ Sync - Ligne 581
- `get_stats()` - ⚙️ Sync - Ligne 610

## 📄 `config.py`

**Méthodes**: 21

### Classe: `WebNavigatorConfig`

- `__init__()` - ⚙️ Sync - Ligne 14
- `load_config()` - ⚙️ Sync - Ligne 54
- `get()` - ⚙️ Sync - Ligne 97
- `set()` - ⚙️ Sync - Ligne 102
- `is_enabled()` - ⚙️ Sync - Ligne 124
- `is_web_search_enabled()` - ⚙️ Sync - Ligne 128
- `is_image_search_enabled()` - ⚙️ Sync - Ligne 132
- `is_news_search_enabled()` - ⚙️ Sync - Ligne 136
- `has_valid_api_key()` - ⚙️ Sync - Ligne 140
- `get_serper_api_key()` - ⚙️ Sync - Ligne 145
- `get_image_save_path()` - ⚙️ Sync - Ligne 149
- `get_serper_base_url()` - ⚙️ Sync - Ligne 156
- `get_request_timeout()` - ⚙️ Sync - Ligne 160
- `get_rate_limit()` - ⚙️ Sync - Ligne 164
- `get_results_per_query()` - ⚙️ Sync - Ligne 168
- `get_language()` - ⚙️ Sync - Ligne 172
- `get_country()` - ⚙️ Sync - Ligne 176
- `get_max_image_size_bytes()` - ⚙️ Sync - Ligne 180
- `get_supported_image_formats()` - ⚙️ Sync - Ligne 185
- `export_config()` - ⚙️ Sync - Ligne 189
- `reset_to_defaults()` - ⚙️ Sync - Ligne 193

---

**Généré automatiquement par**: `scripts/extract_web_navigator_api.py`