# Web Navigator — L'IA qui cherche sur internet

**Source vérifiée** : `extensions/web_navigator/__init__.py`

---

## Concept

Le Web Navigator donne à OGMA la capacité de chercher sur internet en réponse à une requête naturelle ou une commande explicite. L'IA n'est plus limitée à ses connaissances d'entraînement — elle peut vérifier des faits récents, consulter des actualités, trouver des images.

---

## Déclenchement

Deux modes coexistent :

**Commandes explicites** : `/web`, `/news`, `/image`, `/scholar` — préfixes compris par l'extension.

**Phrases magiques** : détection automatique de patterns conversationnels ("cherche sur internet", "actualités sur", "trouve des images de"). L'extension scanne chaque message et déclenche la recherche si un pattern est reconnu.

---

## Providers

L'extension utilise l'API Serper comme moteur de recherche. Serper agrège les résultats Google et supporte quatre types de recherche : web général, actualités, images, académique (Google Scholar).

---

## Flux de traitement

1. Détection de la requête (commande ou phrase magique)
2. Appel API Serper avec la requête extraite
3. Récupération et formatage des résultats
4. Injection dans le contexte du message courant
5. L'IA principale répond avec accès aux résultats

Pour les images, les fichiers sont téléchargés et sauvegardés dans `data/uploads/`.

---

## Usage

```
/web intelligence artificielle
/news dernières nouvelles IA
/image paysage fantasy
/scholar transformer architecture
"cherche sur internet la météo à Paris"
```
