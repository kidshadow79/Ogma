# Web Navigator — The AI That Searches the Internet

**Verified source**: `extensions/web_navigator/__init__.py`

> French version: [../../fr/extensions/04_web_navigator.md](../../fr/extensions/04_web_navigator.md)

---

## Concept

Web Navigator gives OGMA the ability to search the internet in response to a natural request or explicit command. The AI is no longer limited to its training knowledge — it can verify recent facts, check news, find images.

---

## Trigger

Two modes coexist:

**Explicit commands**: `/web`, `/news`, `/image`, `/scholar` — prefixes recognized by the extension.

**Magic phrases**: automatic detection of conversational patterns ("search online", "news about", "find images of"). The extension scans each message and triggers a search if a pattern is recognized.

---

## Providers

The extension uses the Serper API as its search engine. Serper aggregates Google results and supports four search types: general web, news, images, academic (Google Scholar).

---

## Processing flow

1. Request detection (command or magic phrase)
2. Serper API call with extracted query
3. Results retrieval and formatting
4. Injection into current message context
5. Main AI responds with access to results

For images, files are downloaded and saved in `data/uploads/`.

---

## Usage

```
/web artificial intelligence
/news latest AI news
/image fantasy landscape
/scholar transformer architecture
"search online for the weather in Paris"
```
