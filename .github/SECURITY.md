# Politique de Sécurité — OGMA

## 📋 Versions supportées

| Version | Supportée |
|---------|-----------|
| v2.x (actuelle) | ✅ Oui |
| v1.x | ❌ Non |

## 🔒 Signaler une vulnérabilité

**Ne pas ouvrir une issue publique pour signaler une faille de sécurité.**

Envoyez un email à : **ogma.contact@etik.com**

Merci d'inclure dans votre rapport :
- Description de la vulnérabilité
- Étapes pour reproduire
- Impact potentiel estimé
- Votre suggestion de correction (si applicable)

## ⏱️ Délai de réponse

- **Accusé de réception** : sous 72 heures
- **Évaluation initiale** : sous 7 jours
- **Correction** : selon la criticité

## ℹ️ Périmètre

OGMA est un assistant IA **à usage personnel et local**. Les risques principaux concernent :
- Les clés API éventuellement exposées dans la configuration
- L'accès non autorisé aux données de mémoire locale (`data/memory/`)
- Les injections via les prompts système

Les failles liées aux dépendances tierces (NiceGUI, FAISS, etc.) doivent être signalées directement à leurs mainteneurs respectifs.
