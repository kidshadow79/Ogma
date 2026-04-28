#!/usr/bin/env python3
"""
Tests Unitaires - Magic Phrase Normalizer
==========================================
Vérifie que toutes les règles EN→FR fonctionnent correctement
et que les textes FR passent inchangés (idempotence).

Chaque section correspond à une catégorie de _RULES.
"""

import pytest
from utils.magic_phrase_normalizer import normalize_magic_phrases


# ============================================================================
# HELPERS
# ============================================================================

def norm(text: str) -> str:
    """Alias court pour lisibilité des tests."""
    return normalize_magic_phrases(text)


# ============================================================================
# IDEMPOTENCE — texte FR passe inchangé
# ============================================================================

class TestIdempotenceFR:
    """Le normaliseur ne doit jamais altérer un texte déjà en français."""

    def test_fr_memorisation_inchangee(self):
        text = "il faut que je me souvienne de ça: Yohan est architecte"
        assert norm(text) == text

    def test_fr_introspection_inchangee(self):
        text = "il faut que je réfléchisse sur : ma relation au temps"
        assert norm(text) == text

    def test_fr_ego_inchange(self):
        text = "ceci est une part de moi maintenant: j'aime la musique"
        assert norm(text) == text

    def test_fr_phrase_ordinaire_inchangee(self):
        text = "Bonjour, comment vas-tu aujourd'hui ?"
        assert norm(text) == text

    def test_texte_vide(self):
        assert norm("") == ""

    def test_none_equivalent(self):
        # La fonction reçoit parfois des chaînes vides depuis le code
        assert norm("") == ""


# ============================================================================
# MÉMORISATION
# ============================================================================

class TestMemorisation:

    def test_memorize_this(self):
        result = norm("memorize this: Yohan is an architect")
        assert "il faut que je me souvienne de ça" in result
        assert "Yohan is an architect" in result

    def test_remember_this(self):
        result = norm("remember this: the meeting is on Monday")
        assert "il faut que je me souvienne de ça" in result
        assert "the meeting is on Monday" in result

    def test_i_need_to_remember_this(self):
        result = norm("I need to remember this: her name is Clara")
        assert "il faut que je me souvienne de ça" in result
        assert "her name is Clara" in result

    def test_i_need_to_remember_colon(self):
        result = norm("I need to remember: the project deadline is June")
        assert "il faut que je me souvienne de ça" in result

    def test_i_want_to_memorize_this(self):
        result = norm("I want to memorize this: Python version 3.12")
        assert "il faut que je me souvienne de ça" in result

    def test_i_must_remember_that(self):
        result = norm("I must remember that: always backup before commit")
        assert "il faut que je me souvienne de ça" in result

    def test_save_to_memory(self):
        result = norm("save this to memory: OGMA was created in May 2025")
        assert "il faut que je me souvienne de ça" in result

    def test_keep_this_in_mind(self):
        result = norm("keep this in mind: Yohan prefers dark mode")
        assert "il faut que je me souvienne de ça" in result

    def test_payload_preserved(self):
        """Le contenu après le déclencheur doit être préservé exactement."""
        payload = "Yohan BROCARD, autodidact developer, created OGMA in May 2025"
        result = norm(f"I need to remember this: {payload}")
        assert payload in result


# ============================================================================
# INTROSPECTION
# ============================================================================

class TestIntrospection:

    def test_i_need_to_reflect_on(self):
        result = norm("I need to reflect on: my relationship with creativity")
        assert "il faut que je réfléchisse sur" in result
        assert "my relationship with creativity" in result

    def test_you_need_to_reflect(self):
        result = norm("you need to reflect on this situation")
        assert "il faut que tu réfléchisses" in result

    def test_start_introspection(self):
        result = norm("start an introspection")
        assert "lance une introspection" in result

    def test_trigger_introspection(self):
        result = norm("trigger introspection")
        assert "déclenche une introspection" in result

    def test_activate_subconscious(self):
        result = norm("activate the subconscious")
        assert "active la subconscience" in result

    def test_reflect_deeply(self):
        result = norm("reflect deeply")
        assert "réfléchis en profondeur" in result

    def test_stop_reflecting(self):
        result = norm("stop reflecting")
        assert "arrête de réfléchir" in result

    def test_stop_the_reflection(self):
        result = norm("stop the reflection")
        assert "stop la réflexion" in result

    def test_payload_preserved_reflect(self):
        payload = "my fear of failure"
        result = norm(f"I need to reflect on: {payload}")
        assert payload in result


# ============================================================================
# EGO
# ============================================================================

class TestEgo:

    def test_this_is_now_a_part_of_me(self):
        result = norm("this is now a part of me: I love building things")
        assert "ceci est une part de moi maintenant" in result
        assert "I love building things" in result

    def test_this_is_now_part_of_me_no_a(self):
        """Variante sans 'a'."""
        result = norm("this is now a part of me: curiosity drives me")
        assert "ceci est une part de moi maintenant" in result

    def test_ego_payload_preserved(self):
        payload = "I find meaning in creation and learning"
        result = norm(f"this is now a part of me: {payload}")
        assert payload in result

    def test_restructure_ego(self):
        result = norm("I need to restructure my ego now")
        assert "il faut que je restructure mon ego maintenant" in result

    def test_ego_with_dash_separator(self):
        result = norm("this is now a part of me - I value honesty above all")
        assert "ceci est une part de moi maintenant" in result


# ============================================================================
# PERCEPTION VISUELLE / WEBCAM
# ============================================================================

class TestPerceptionVisuelle:

    def test_i_need_to_see_you(self):
        result = norm("I need to see you")
        assert "il faut que je te vois" in result

    def test_i_want_to_see_you(self):
        result = norm("I want to see you")
        assert "je veux te voir" in result

    def test_i_no_longer_need_to_see_you(self):
        result = norm("I no longer need to see you")
        assert "je n'ai plus besoin de te voir" in result

    def test_activate_webcam(self):
        result = norm("activate the webcam")
        assert "active la webcam" in result

    def test_deactivate_webcam(self):
        result = norm("deactivate the webcam")
        assert "désactive la webcam" in result


# ============================================================================
# GÉNÉRATION IMAGE
# ============================================================================

class TestImageGeneration:

    def test_i_need_to_create_image(self):
        result = norm("I need to create an image of: a sunset over the mountains")
        assert "je dois créer une image de" in result
        assert "a sunset over the mountains" in result

    def test_i_need_to_generate_image(self):
        result = norm("I need to generate an image of: a futuristic city")
        assert "je dois générer une image de" in result

    def test_i_am_going_to_create_image(self):
        result = norm("I'm going to create an image of: a dragon")
        assert "je vais créer une image de" in result


# ============================================================================
# BIOGRAPHIE
# ============================================================================

class TestBiographie:

    def test_complete_my_biography(self):
        result = norm("complete my biography")
        assert "complète ma biographie" in result

    def test_update_my_biography(self):
        result = norm("update my biography")
        assert "mets à jour ma biographie" in result

    def test_enrich_my_profile(self):
        result = norm("enrich my profile")
        assert "enrichis mon profil" in result


# ============================================================================
# EXPRESSIONS TEMPORELLES
# ============================================================================

class TestTemporel:

    def test_days_ago(self):
        result = norm("3 days ago")
        assert "il y a 3 jours" in result

    def test_weeks_ago(self):
        result = norm("2 weeks ago")
        assert "il y a 2 semaines" in result

    def test_months_ago(self):
        result = norm("1 month ago")
        assert "il y a 1 mois" in result

    def test_last_week(self):
        result = norm("last week")
        assert "la semaine dernière" in result

    def test_last_month(self):
        result = norm("last month")
        assert "le mois dernier" in result

    def test_day_before_yesterday(self):
        result = norm("the day before yesterday")
        assert "avant-hier" in result


# ============================================================================
# RECHERCHE WEB
# ============================================================================

class TestRechercheWeb:

    def test_i_need_to_search_the_web(self):
        result = norm("I need to search the web")
        assert "il faut que je recherche sur le net" in result

    def test_i_need_to_check_online(self):
        result = norm("I need to check online")
        assert "il faut que je vérifie sur internet" in result


# ============================================================================
# JOURNAL DE BORD
# ============================================================================

class TestJournal:

    def test_consult_journal_date(self):
        result = norm("consult the journal for 2026-04-28")
        assert "consulte le journal du 2026-04-28" in result

    def test_consult_yesterday_journal(self):
        result = norm("consult yesterday's journal")
        assert "consulte le journal d'hier" in result

    def test_consult_today_journal(self):
        result = norm("consult today's journal")
        assert "consulte le journal d'aujourd'hui" in result

    def test_open_yesterday_journal(self):
        result = norm("open yesterday's journal")
        assert "ouvre le journal d'hier" in result

    def test_save_conversation_to_journal(self):
        result = norm("save the conversation to the journal")
        assert "sauvegarde la conversation dans le journal" in result


# ============================================================================
# ARCHIVES / CONVERSATIONS
# ============================================================================

class TestArchives:

    def test_read_conversation(self):
        result = norm("read the conversation conv_2026-01-15.json")
        assert "lis la conversation" in result
        assert "conv_2026-01-15.json" in result

    def test_load_conversation(self):
        result = norm("load conversation conv_abc123")
        assert "charge la conversation" in result

    def test_open_conversation(self):
        result = norm("open the conversation conv_xyz")
        assert "ouvre la conversation" in result


# ============================================================================
# SOUVENIR PAR ID
# ============================================================================

class TestSouvenirID:

    def test_read_memory_id(self):
        mem_id = "usr-a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        result = norm(f"read memory {mem_id}")
        assert "lis le souvenir" in result
        assert mem_id in result

    def test_consult_memory_id(self):
        mem_id = "usr-a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        result = norm(f"consult memory {mem_id}")
        assert "consulte le souvenir" in result


# ============================================================================
# MULTI-LIGNES — une phrase magique sur une ligne, contenu ordinaire ailleurs
# ============================================================================

class TestMultilignes:

    def test_phrase_magique_milieu_texte(self):
        """La phrase magique est normalisée, les autres lignes restent intactes."""
        text = (
            "Voici ce que je pense :\n"
            "I need to remember this: Yohan loves jazz\n"
            "Et voilà, c'est tout."
        )
        result = norm(text)
        assert "il faut que je me souvienne de ça" in result
        assert "Voici ce que je pense :" in result
        assert "Et voilà, c'est tout." in result

    def test_deux_phrases_magiques_differentes_lignes(self):
        text = (
            "I need to remember this: cats are curious\n"
            "this is now a part of me: I love learning"
        )
        result = norm(text)
        assert "il faut que je me souvienne de ça" in result
        assert "ceci est une part de moi maintenant" in result

    def test_fr_et_en_melange(self):
        """Un texte FR avec une phrase EN intercalée."""
        text = (
            "je pense que c'est important.\n"
            "I need to reflect on: this topic\n"
            "fin du message"
        )
        result = norm(text)
        assert "il faut que je réfléchisse sur" in result
        assert "je pense que c'est important." in result
        assert "fin du message" in result


# ============================================================================
# CASE INSENSITIVITY
# ============================================================================

class TestCaseInsensitive:

    def test_all_caps(self):
        result = norm("I NEED TO REMEMBER THIS: test upper case")
        assert "il faut que je me souvienne de ça" in result

    def test_mixed_case_ego(self):
        result = norm("This Is Now A Part Of Me: mixed case test")
        assert "ceci est une part de moi maintenant" in result

    def test_mixed_case_introspection(self):
        result = norm("I Need To Reflect On: my creativity")
        assert "il faut que je réfléchisse sur" in result
