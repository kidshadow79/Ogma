"""
i18n.py — Internationalisation FR/EN pour OGMA

Architecture :
- data/settings.json["ui_lang"] : langue courante ("fr" ou "en")
- data/i18n/ui_fr.json et ui_en.json : dictionnaires de traduction
- get_lang() relit le fichier à chaque appel (pas de cache) pour supporter
  un changement de langue suivi d'un ui.navigate.reload()
- t(key) retourne la clé elle-même si elle est absente (jamais d'erreur)

Règle absolue : ce module ne touche JAMAIS aux instructions personnalisées
de l'utilisateur (settings.json["prompts"], persistent_context.txt, etc.).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Optional

# Racine du projet OGMA (utils/i18n.py → racine = parent)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SETTINGS_FILE = _PROJECT_ROOT / "data" / "settings.json"
_I18N_DIR = _PROJECT_ROOT / "data" / "i18n"

DEFAULT_LANG = "fr"
SUPPORTED_LANGS = ("fr", "en")

# Cache des dictionnaires de strings (chargés une seule fois par langue)
# La langue courante elle-même n'est PAS cachée — relue à chaque get_lang()
_strings_cache: Dict[str, Dict[str, str]] = {}


def _load_lang_file(lang: str) -> Dict[str, str]:
    """Charge data/i18n/ui_{lang}.json. Retourne {} si absent."""
    if lang in _strings_cache:
        return _strings_cache[lang]

    path = _I18N_DIR / f"ui_{lang}.json"
    try:
        if path.is_file():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                _strings_cache[lang] = data
                return data
    except (json.JSONDecodeError, OSError) as e:
        print(f"[i18n] Erreur lecture {path}: {e}")

    _strings_cache[lang] = {}
    return {}


def get_lang() -> str:
    """
    Retourne la langue UI courante depuis settings.json["ui_lang"].
    Relit le fichier à chaque appel (pas de cache de la valeur) pour
    supporter le changement de langue + reload de page.
    Fallback : DEFAULT_LANG si fichier absent ou clé manquante.
    """
    try:
        if _SETTINGS_FILE.is_file():
            with open(_SETTINGS_FILE, "r", encoding="utf-8") as f:
                settings = json.load(f)
            lang = settings.get("ui_lang")
            if lang in SUPPORTED_LANGS:
                return lang
    except (json.JSONDecodeError, OSError) as e:
        print(f"[i18n] Erreur lecture settings.json: {e}")
    return DEFAULT_LANG


def set_lang(lang: str) -> bool:
    """
    Définit la langue UI dans settings.json["ui_lang"].
    Retourne True si succès, False sinon.
    Ne touche à AUCUN autre champ de settings.json.
    """
    if lang not in SUPPORTED_LANGS:
        print(f"[i18n] Langue non supportée: {lang}")
        return False

    try:
        # Relire la totalité du fichier pour ne pas perdre les autres clés
        if _SETTINGS_FILE.is_file():
            with open(_SETTINGS_FILE, "r", encoding="utf-8") as f:
                settings = json.load(f)
        else:
            settings = {}

        settings["ui_lang"] = lang

        # Écriture atomique : tmp puis remplacement
        tmp_path = _SETTINGS_FILE.with_suffix(".json.tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, _SETTINGS_FILE)
        return True
    except (json.JSONDecodeError, OSError) as e:
        print(f"[i18n] Erreur écriture settings.json: {e}")
        return False


def t(key: str, **kwargs) -> str:
    """
    Retourne la traduction du `key` dans la langue courante.
    Si la clé est absente : fallback sur FR, puis sur la clé elle-même.
    Supporte les variables via .format() : t("notify_loaded", n=5).

    Exemples :
        t("btn_send")                       → "Envoyer" en FR / "Send" en EN
        t("notify_memory_loaded", n=5)      → "Souvenir 5 chargé"
    """
    lang = get_lang()
    strings = _load_lang_file(lang)
    value = strings.get(key)

    # Fallback FR si clé absente dans la langue courante
    if value is None and lang != DEFAULT_LANG:
        value = _load_lang_file(DEFAULT_LANG).get(key)

    # Fallback ultime : la clé elle-même (jamais d'erreur affichée)
    if value is None:
        value = key

    # Substitution de variables si demandée
    if kwargs:
        try:
            return value.format(**kwargs)
        except (KeyError, IndexError) as e:
            print(f"[i18n] Erreur format '{key}': {e}")
            return value

    return value


def reload_strings() -> None:
    """Vide le cache des dictionnaires (force un rechargement au prochain t())."""
    _strings_cache.clear()


def get_supported_langs() -> tuple:
    """Retourne le tuple des langues supportées."""
    return SUPPORTED_LANGS
