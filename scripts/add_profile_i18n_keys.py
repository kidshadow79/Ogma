"""Ajoute les clés i18n manquantes pour le modal profil dans ui_en.json et ui_fr.json.
Insertion à la fin du dict, en préservant ordre et indentation 2 espaces.
Idempotent : ne touche pas aux clés déjà présentes.
"""
import json
from pathlib import Path
from collections import OrderedDict

BASE = Path(__file__).resolve().parent.parent / "data" / "i18n"
EN_PATH = BASE / "ui_en.json"
FR_PATH = BASE / "ui_fr.json"

# Mapping key -> (FR, EN)
NEW_KEYS = OrderedDict([
    # Modal title + close
    ("profile_modal_title", ("👤 Profil Utilisateur", "👤 User Profile")),
    ("profile_btn_close", ("Fermer", "Close")),
    ("profile_btn_cancel", ("Annuler", "Cancel")),
    ("profile_btn_validate", ("Valider", "Validate")),
    ("profile_settings_mgr_unavailable", ("❌ Settings Manager non disponible", "❌ Settings Manager not available")),

    # Section Debug
    ("profile_section_debug", ("🔍 Options de Debug", "🔍 Debug Options")),
    ("profile_debug_archiviste_label", ("Afficher les injections de contexte de l'Archiviste dans le chat", "Show Archivist context injections in chat")),
    ("profile_debug_archiviste_desc", ("Quand activé, vous verrez les notes de contexte injectées par l'Archiviste en tant que messages système dans la conversation.", "When enabled, you will see context notes injected by the Archivist as system messages in the conversation.")),
    ("profile_debug_saved", ("Paramètre debug sauvegardé", "Debug setting saved")),

    # Section Vision
    ("profile_section_vision", ("👁️ Vision Avancée (Traitement d'Images)", "👁️ Advanced Vision (Image Processing)")),
    ("profile_vision_desc", ("Ces options s'appliquent aux images envoyées en pièce jointe. Si les deux sont activées, une image 3 colonnes sera générée.", "These options apply to attached images. If both are enabled, a 3-column image will be generated.")),
    ("profile_depth_label", ("🌊 Carte de Profondeur (Depth Map 3D)", "🌊 Depth Map (3D depth map)")),
    ("profile_depth_saved", ("Paramètre Depth Map sauvegardé", "Depth Map setting saved")),
    ("profile_contour_label", ("✏️ Analyse de Contours (Canny, Sobel — traits rouges épais)", "✏️ Contour Analysis (Canny, Sobel — thick red lines)")),
    ("profile_contour_saved", ("Paramètre Analyse Contours sauvegardé", "Contour Analysis setting saved")),
    ("profile_contour_methods", ("Méthodes de détection :", "Detection methods:")),
    ("profile_contour_canny", ("Canny (contours nets - recommandé)", "Canny (sharp contours - recommended)")),
    ("profile_contour_sobel", ("Sobel (gradients directionnels)", "Sobel (directional gradients)")),
    ("profile_contour_laplacian", ("Laplacian (contours fins)", "Laplacian (fine contours)")),
    ("profile_contour_adaptive", ("Adaptatif (formes contrastées)", "Adaptive (contrasted shapes)")),
    ("profile_canny_params", ("Paramètres Canny :", "Canny parameters:")),
    ("profile_canny_low", ("Seuil bas", "Low threshold")),
    ("profile_canny_high", ("Seuil haut", "High threshold")),
    ("profile_canny_thickness", ("Épaisseur", "Thickness")),
    ("profile_line_color", ("Couleur des tracés :", "Line color:")),
    ("profile_color_red", ("Rouge", "Red")),
    ("profile_color_white", ("Blanc", "White")),
    ("profile_color_black", ("Noir", "Black")),
    ("profile_render_mode", ("Mode de rendu :", "Render mode:")),
    ("profile_render_overlay", ("Sur l'image (overlay)", "On the image (overlay)")),
    ("profile_render_black_bg", ("Sur fond noir", "On black background")),
    ("profile_render_white_bg", ("Sur fond blanc", "On white background")),
    ("profile_vision_autosave", ("Les images traitées sont automatiquement sauvegardées dans le dossier captures/.", "Processed images are automatically saved in the captures/ folder.")),

    # Section Gestion Profil Unique
    ("profile_section_mgmt", ("🏗️ Gestion du Profil Unique", "🏗️ Single Profile Management")),
    ("profile_current_card_title", ("📊 Profil Actuel", "📊 Current Profile")),
    ("profile_current_user", ("👤 Utilisateur : {name}", "👤 User: {name}")),
    ("profile_current_ai", ("🤖 IA : {name}", "🤖 AI: {name}")),
    ("profile_current_desc", ("📝 Description : {desc}", "📝 Description: {desc}")),
    ("profile_current_memories", ("🧠 Mémoires : {n} souvenirs", "🧠 Memories: {n} entries")),
    ("profile_current_founders", ("🏛️ Fondateurs : {n} préservés", "🏛️ Founders: {n} preserved")),
    ("profile_current_size", ("💾 Taille totale : {size} MB", "💾 Total size: {size} MB")),

    # Save profile dialog
    ("profile_save_dialog_title", ("💾 Sauvegarder le Profil Actuel", "💾 Save Current Profile")),
    ("profile_save_name_label", ("Nom du profil", "Profile name")),
    ("profile_save_desc_label", ("Description (optionnel)", "Description (optional)")),
    ("profile_save_default_desc", ("Sauvegarde de {name} - {date}", "Backup of {name} - {date}")),
    ("profile_save_size_info", ("Cette sauvegarde inclura toutes les données du profil actuel ({size} MB)", "This backup will include all data from the current profile ({size} MB)")),
    ("profile_save_name_required", ("Le nom du profil est obligatoire", "Profile name is required")),
    ("profile_save_success", ("Profil sauvegardé avec succès !", "Profile saved successfully!")),
    ("profile_btn_save", ("💾 Sauvegarder", "💾 Save")),
    ("profile_btn_save_profile", ("💾 Sauvegarder Profil", "💾 Save Profile")),

    # Delete profile dialog
    ("profile_delete_dialog_title", ("🗑️ Supprimer le Profil Actuel", "🗑️ Delete Current Profile")),
    ("profile_delete_warning_title", ("⚠️ ATTENTION - SUPPRESSION DÉFINITIVE", "⚠️ WARNING - PERMANENT DELETION")),
    ("profile_delete_warning_text", ("Cette action va supprimer DÉFINITIVEMENT :", "This action will PERMANENTLY delete:")),
    ("profile_delete_item_memories", ("🧠 {n} souvenirs (fondateurs préservés)", "🧠 {n} memories (founders preserved)")),
    ("profile_delete_item_conversations", ("💬 Toutes les conversations", "💬 All conversations")),
    ("profile_delete_item_ego", ("🎭 Données de personnalité (ego)", "🎭 Personality data (ego)")),
    ("profile_delete_item_images", ("📸 Images générées + captures webcam", "📸 Generated images + webcam captures")),
    ("profile_delete_item_biographies", ("📚 Biographies", "📚 Biographies")),
    ("profile_delete_item_journal", ("📖 Journal de bord", "📖 Journal")),
    ("profile_delete_item_planner", ("📅 Organic Planner (agenda)", "📅 Organic Planner (agenda)")),
    ("profile_delete_item_apikeys", ("🔑 TOUTES les clés API (sécurité)", "🔑 ALL API keys (security)")),
    ("profile_delete_item_extensions", ("🔧 Configurations extensions", "🔧 Extension configurations")),
    ("profile_delete_item_logs", ("🗂️ Fichiers temporaires et logs", "🗂️ Temporary files and logs")),
    ("profile_delete_save_before", ("💾 Sauvegarder avant suppression (recommandé)", "💾 Save before deletion (recommended)")),
    ("profile_delete_confirm_label", ("Pour confirmer, tapez: DELETE-PROFILE-OGMA", "To confirm, type: DELETE-PROFILE-OGMA")),
    ("profile_delete_confirm_input", ("Code de confirmation", "Confirmation code")),
    ("profile_delete_wrong_code", ("Code de confirmation incorrect", "Incorrect confirmation code")),
    ("profile_delete_saving", ("💾 Sauvegarde en cours...", "💾 Saving in progress...")),
    ("profile_delete_auto_save_desc", ("Sauvegarde automatique avant suppression du profil", "Automatic backup before profile deletion")),
    ("profile_delete_save_created", ("💾 Sauvegarde créée", "💾 Backup created")),
    ("profile_delete_save_error", ("Erreur sauvegarde : {msg}", "Backup error: {msg}")),
    ("profile_delete_deleting", ("🗑️ Suppression du profil en cours...", "🗑️ Deleting profile in progress...")),
    ("profile_delete_success", ("✅ Profil supprimé avec succès !", "✅ Profile deleted successfully!")),
    ("profile_delete_restart_note", ("🔄 Redémarrez OGMA pour finaliser la réinitialisation.", "🔄 Restart OGMA to finalise the reset.")),
    ("profile_btn_delete_permanently", ("🗑️ Supprimer Définitivement", "🗑️ Delete Permanently")),
    ("profile_btn_delete_profile", ("🗑️ Supprimer Profil", "🗑️ Delete Profile")),

    # Backups list
    ("profile_section_backups", ("📂 Sauvegardes Disponibles", "📂 Available Backups")),
    ("profile_no_backup", ("Aucune sauvegarde trouvée", "No backup found")),
    ("profile_load_dialog_title", ("📂 Charger une Sauvegarde", "📂 Load a Backup")),
    ("profile_load_warning", ("⚠️ ATTENTION : Cette action va REMPLACER le profil actuel", "⚠️ WARNING: This action will REPLACE the current profile")),
    ("profile_load_name_label", ("Profil à charger : {name}", "Profile to load: {name}")),
    ("profile_load_size_label", ("💾 Taille : {size} MB", "💾 Size: {size} MB")),
    ("profile_load_restored", ("✅ Sera restauré : Mémoires, Clés API, Instructions, Journal, Captures...", "✅ Will be restored: Memories, API keys, Instructions, Journal, Captures...")),
    ("profile_load_auto_save_note", ("💾 Le profil actuel sera automatiquement sauvegardé avant remplacement.", "💾 The current profile will be automatically saved before replacement.")),
    ("profile_load_success", ("Profil chargé avec succès !", "Profile loaded successfully!")),
    ("profile_btn_load_profile", ("📂 Charger ce Profil", "📂 Load this Profile")),
    ("profile_btn_load", ("📂 Charger", "📂 Load")),
    ("profile_delete_backup_title", ("🗑️ Supprimer cette sauvegarde", "🗑️ Delete this backup")),
    ("profile_delete_backup_irreversible", ("⚠️ Cette action est IRRÉVERSIBLE", "⚠️ This action is IRREVERSIBLE")),
    ("profile_delete_backup_text", ("Le dossier complet sera supprimé du disque. Aucune restauration possible.", "The complete folder will be deleted from disk. No restoration possible.")),
    ("profile_deleting_backup", ("🗑️ Suppression en cours...", "🗑️ Deletion in progress...")),
    ("profile_btn_delete_def", ("🗑️ Supprimer définitivement", "🗑️ Delete permanently")),

    # Config snapshot
    ("profile_section_config_snapshot", ("🔑 Sauvegarde Config (Clés API + Instructions)", "🔑 Config Backup (API Keys + Instructions)")),
    ("profile_config_snapshot_desc", ("Snapshot léger : sauvegarde uniquement les clés API, instructions générales et instructions images (t2i/i2i). Quelques KB seulement.", "Lightweight snapshot: saves only API keys, general instructions and image instructions (t2i/i2i). A few KB only.")),
    ("profile_config_save_dialog_title", ("🔑 Sauvegarder Config", "🔑 Save Config")),
    ("profile_config_name_label", ("Nom de la config", "Config name")),
    ("profile_config_saved_content", ("Contenu sauvegardé :", "Saved content:")),
    ("profile_config_save_name_required", ("Le nom est obligatoire", "Name is required")),
    ("profile_btn_save_config", ("💾 Sauvegarder Config", "💾 Save Config")),
    ("profile_config_load_dialog_title", ("📂 Charger Config", "📂 Load Config")),
    ("profile_config_load_warning", ("⚠️ Les clés API et instructions actuelles seront remplacées.", "⚠️ Current API keys and instructions will be replaced.")),
    ("profile_config_load_reset_note", ("Les contrôleurs IA seront réinitialisés pour utiliser les nouvelles clés.", "AI controllers will be reset to use the new keys.")),
    ("profile_config_delete_dialog_title", ("🗑️ Supprimer Config", "🗑️ Delete Config")),
    ("profile_config_delete_text", ("Supprimer : {name}", "Delete: {name}")),
    ("profile_config_irreversible", ("Cette action est irréversible.", "This action is irreversible.")),
    ("profile_no_config_snapshot", ("Aucun snapshot de config sauvegardé", "No config snapshot saved")),
    ("profile_btn_delete", ("🗑️ Supprimer", "🗑️ Delete")),

    # Hologram
    ("profile_hologram_title", ("Hologramme Projector", "Hologram Projector")),
    ("profile_hologram_experimental", ("Expérimental", "Experimental")),
    ("profile_hologram_desc", ("Projetez le visage animé d'OGMA sur une pyramide de Pepper's Ghost. Cette extension est expérimentale : elle nécessite une page ouverte sur un second écran (téléphone ou tablette) connecté au même réseau local.", "Project the animated face of OGMA onto a Pepper's Ghost pyramid. This extension is experimental: it requires a page open on a second screen (phone or tablet) connected to the same local network.")),
    ("profile_hologram_toggle", ("Activer l'hologramme", "Enable hologram")),
    ("profile_hologram_state_on", ("activé", "enabled")),
    ("profile_hologram_state_off", ("désactivé", "disabled")),
    ("profile_hologram_notify_state", ("Hologramme {state}", "Hologram {state}")),
    ("profile_hologram_error", ("Erreur hologramme : {err}", "Hologram error: {err}")),
    ("profile_btn_hologram_howto", ("Comment ça marche ?", "How does it work?")),
    ("profile_hologram_howto_title", ("Hologramme Projector — Comment ça marche ?", "Hologram Projector — How does it work?")),
    ("profile_hologram_pyramid_title", ("🔺 La pyramide de Pepper's Ghost", "🔺 The Pepper's Ghost pyramid")),
    ("profile_hologram_pyramid_desc", ("La technique de Pepper's Ghost date du XIXe siècle. Une pyramide creuse en plastique transparent (4 faces triangulaires) posée sur l'écran de votre téléphone reflète l'image sous 4 angles, créant l'illusion d'un hologramme flottant au centre.", "The Pepper's Ghost technique dates from the 19th century. A hollow transparent plastic pyramid (4 triangular faces) placed on your phone's screen reflects the image from 4 angles, creating the illusion of a hologram floating in the centre.")),
    ("profile_hologram_steps_title", ("📱 Étapes d'utilisation", "📱 Usage steps")),
    ("profile_hologram_step_1", ("1. Activez l'hologramme avec le switch ci-dessus.", "1. Enable the hologram with the switch above.")),
    ("profile_hologram_step_2", ("2. Connectez votre téléphone/tablette au même réseau Wi-Fi que ce PC.", "2. Connect your phone/tablet to the same Wi-Fi network as this PC.")),
    ("profile_hologram_step_3", ("3. Ouvrez l'adresse ci-dessous dans le navigateur de votre appareil mobile.", "3. Open the address below in the browser of your mobile device.")),
    ("profile_hologram_step_4", ("4. Passez en mode plein écran (touchez l'icône ⛶ ou utilisez le menu du navigateur).", "4. Switch to full-screen mode (tap the ⛶ icon or use the browser menu).")),
    ("profile_hologram_step_5", ("5. Posez la pyramide de Pepper's Ghost au centre de l'écran.", "5. Place the Pepper's Ghost pyramid at the centre of the screen.")),
    ("profile_hologram_step_6", ("6. Éteignez les lumières et profitez !", "6. Turn off the lights and enjoy!")),
    ("profile_hologram_url_title", ("🌐 Adresse à ouvrir sur votre appareil mobile", "🌐 Address to open on your mobile device")),
    ("profile_hologram_url_copied", ("URL copiée !", "URL copied!")),
    ("profile_btn_copy_url", ("Copier l'URL", "Copy URL")),
    ("profile_hologram_url_warning", ("⚠️ Cette adresse est celle de votre réseau local. Elle change si votre machine obtient une nouvelle adresse IP (redémarrage du routeur, etc.).", "⚠️ This address is on your local network. It changes if your machine gets a new IP address (router reboot, etc.).")),
    ("profile_hologram_alt_title", ("🖥️ Page sphère alternative", "🖥️ Alternative sphere page")),
    ("profile_hologram_alt_desc", ("Version sphère wireframe Three.js : {url}", "Three.js wireframe sphere version: {url}")),

    # Identités
    ("profile_section_identity", ("👤 Identités", "👤 Identities")),
    ("profile_username_label", ("Nom utilisateur", "Username")),
    ("profile_ai_name_label", ("Nom IA", "AI Name")),
    ("profile_username_updated", ("Nom utilisateur mis à jour : {name}", "Username updated: {name}")),
    ("profile_username_empty_err", ("Le nom utilisateur ne peut pas être vide", "Username cannot be empty")),
    ("profile_ai_updated", ("Nom IA mis à jour : {name}", "AI name updated: {name}")),
    ("profile_ai_empty_err", ("Le nom IA ne peut pas être vide", "AI name cannot be empty")),
    ("profile_update_err", ("Erreur lors de la mise à jour", "Update error")),
    ("profile_identity_instr_label", ("📋 Instruction d'identité", "📋 Identity instruction")),
    ("profile_identity_instr_desc", ("Cette instruction sera injectée à chaque conversation pour clarifier qui vous êtes.", "This instruction will be injected into every conversation to clarify who you are.")),
    ("profile_identity_textarea_label", ("Instruction", "Instruction")),
    ("profile_identity_updated", ("✅ Instruction d'identité mise à jour", "✅ Identity instruction updated")),
    ("profile_identity_empty_err", ("L'instruction ne peut pas être vide", "Instruction cannot be empty")),
    ("profile_identity_reset_btn", ("Réinitialiser au défaut", "Reset to default")),

    # Mode Conversation Vocale
    ("profile_section_voice", ("🎙️ Mode Conversation Vocale", "🎙️ Voice Conversation Mode")),
    ("profile_voice_card_title", ("🎤 Conversation Vocale Intelligente", "🎤 Smart Voice Conversation")),
    ("profile_voice_enable", ("Activer le mode conversation vocale", "Enable voice conversation mode")),
    ("profile_voice_activated_notify", ("🎙️ Mode vocal activé ! Cliquez dans la zone de message pour commencer.", "🎙️ Voice mode activated! Click in the message area to start.")),
    ("profile_voice_deactivated_notify", ("Mode vocal désactivé", "Voice mode disabled")),
    ("profile_badge_active", ("🎙️ ACTIF", "🎙️ ACTIVE")),
    ("profile_badge_inactive", ("⏸️ INACTIF", "⏸️ INACTIVE")),
    ("profile_voice_principle", ("Principe : Cliquez dans la zone de message pour activer l'écoute. Dites le mot d'activation pour commencer à dicter, puis le mot d'envoi pour envoyer.", "Principle: Click in the message area to activate listening. Say the activation word to start dictating, then the send word to send.")),
    ("profile_voice_continuous_mode", ("🔄 Mode Conversation Continue", "🔄 Continuous Conversation Mode")),
    ("profile_badge_continuous", ("🔥 CONTINU", "🔥 CONTINUOUS")),
    ("profile_voice_continuous_activated_notify", ("🔄 Mode conversation continue activé ! Plus besoin du trigger d'activation.", "🔄 Continuous conversation mode activated! No more need for activation trigger.")),
    ("profile_voice_continuous_deactivated_notify", ("Mode conversation continue désactivé", "Continuous conversation mode disabled")),
    ("profile_voice_continuous_desc_1", ("⚡ Mode continu : Dès que l'IA principale finit de parler, le micro s'active automatiquement.", "⚡ Continuous mode: As soon as the main AI finishes speaking, the microphone activates automatically.")),
    ("profile_voice_continuous_desc_2", ("Pas besoin du trigger d'activation - seul le trigger d'envoi est nécessaire.", "No activation trigger needed - only the send trigger is required.")),
    ("profile_voice_activation_saved", ("Mot d'activation : \"{word}\"", "Activation word: \"{word}\"")),
    ("profile_voice_send_saved", ("Mot d'envoi : \"{word}\"", "Send word: \"{word}\"")),
    ("profile_voice_tips_activation", ("💡 Dites \"{word}\" pour commencer à dicter ou interrompre l'IA principale.", "💡 Say \"{word}\" to start dictating or interrupt the main AI.")),
    ("profile_voice_tips_send", ("💡 Dites \"{word}\" pour envoyer votre message.", "💡 Say \"{word}\" to send your message.")),
    ("profile_voice_advanced_params", ("🎚️ Paramètres Audio Avancés", "🎚️ Advanced Audio Parameters")),
    ("profile_voice_timeout_saved", ("Timeout d'écoute : {val}s", "Listening timeout: {val}s")),
    ("profile_voice_duration_saved", ("Durée max par segment : {val}s", "Max duration per segment: {val}s")),
    ("profile_voice_pause_saved", ("Seuil de pause : {val}s", "Pause threshold: {val}s")),
    ("profile_voice_autosend_enabled", ("Envoi automatique après {val}s de silence", "Auto-send after {val}s of silence")),
    ("profile_voice_autosend_disabled", ("Envoi automatique désactivé", "Auto-send disabled")),
    ("profile_voice_invalid_value", ("Valeur invalide", "Invalid value")),
    ("profile_voice_tip_timeout", ("💡 Timeout = délai max avant de commencer à parler", "💡 Timeout = max delay before speaking")),
    ("profile_voice_tip_duration", ("💡 Durée max = durée totale d'enregistrement par segment", "💡 Max duration = total recording time per segment")),
    ("profile_voice_tip_pause", ("💡 Seuil pause = silence nécessaire pour couper (ne pas couper au milieu d'une phrase)", "💡 Pause threshold = silence needed to cut (don't cut mid-sentence)")),
    ("profile_voice_tip_autosend", ("💡 Envoi auto = silence total avant d'envoyer le message (5s recommandé, 30s+ pour désactiver)", "💡 Auto-send = total silence before sending the message (5s recommended, 30s+ to disable)")),

    # TTS
    ("profile_section_tts", ("🔊 Synthèse Vocale (TTS)", "🔊 Voice Synthesis (TTS)")),
    ("profile_tts_enable", ("🔊 Activer la synthèse vocale", "🔊 Enable voice synthesis")),
    ("profile_tts_status_active", ("✅ ACTIF", "✅ ACTIVE")),
    ("profile_tts_status_inactive", ("❌ INACTIF", "❌ INACTIVE")),
    ("profile_tts_state_on", ("activée", "enabled")),
    ("profile_tts_state_off", ("désactivée", "disabled")),
    ("profile_tts_notify_state", ("Synthèse vocale {state}", "Voice synthesis {state}")),
    ("profile_tts_enable_desc", ("Active le système de synthèse vocale. Décoché = pas de TTS du tout.", "Enables the voice synthesis system. Unchecked = no TTS at all.")),
    ("profile_tts_auto_read", ("▶️ Lecture automatique des réponses IA", "▶️ Automatic reading of AI responses")),
    ("profile_tts_auto_read_state_on", ("activée", "enabled")),
    ("profile_tts_auto_read_state_off", ("désactivée", "disabled")),
    ("profile_tts_auto_read_notify", ("Lecture automatique {state}", "Automatic reading {state}")),
    ("profile_tts_auto_read_desc", ("Coché = lecture automatique | Décoché = bouton ▶️ manuel sous chaque réponse.", "Checked = automatic playback | Unchecked = manual ▶️ button under each response.")),
    ("profile_tts_streaming", ("🔊 Mode streaming (lecture phrase par phrase)", "🔊 Streaming mode (sentence by sentence)")),
    ("profile_tts_streaming_state_on", ("activé", "enabled")),
    ("profile_tts_streaming_state_off", ("désactivé", "disabled")),
    ("profile_tts_streaming_notify", ("TTS streaming {state}", "TTS streaming {state}")),
    ("profile_tts_streaming_desc", ("Coché = lecture progressive pendant le streaming | Décoché = lecture après réponse complète.", "Checked = progressive reading during streaming | Unchecked = reading after complete response.")),
    ("profile_tts_config_title", ("⚙️ Configuration TTS", "⚙️ TTS Configuration")),
    ("profile_tts_engine_conflict_free", ("🎵 TTS Sans Conflit (recommandé)", "🎵 Conflict-Free TTS (recommended)")),
    ("profile_tts_engine_gtts", ("🌐 Google TTS Offline (Gratuit)", "🌐 Google TTS Offline (Free)")),
    ("profile_tts_engine_system", ("🖥️ Système (pyttsx3)", "🖥️ System (pyttsx3)")),
    ("profile_tts_engine_azure", ("☁️ Azure AI Speech (API)", "☁️ Azure AI Speech (API)")),
    ("profile_tts_engine_google", ("☁️ Google Cloud TTS (API)", "☁️ Google Cloud TTS (API)")),
    ("profile_tts_engine_elevenlabs", ("🎯 ElevenLabs (API Premium)", "🎯 ElevenLabs (API Premium)")),
    ("profile_tts_engine_fish_audio", ("🐟 Fish Audio (API)", "🐟 Fish Audio (API)")),
    ("profile_tts_engine_cartesia", ("🎭 Cartesia AI (API)", "🎭 Cartesia AI (API)")),
    ("profile_tts_engine_hume_ai", ("🧠 Hume AI / Octave (API)", "🧠 Hume AI / Octave (API)")),
    ("profile_tts_engine_conflict_free_activated", ("🎵 TTS sans conflit activé (optimal)", "🎵 Conflict-free TTS activated (optimal)")),
    ("profile_tts_engine_changed", ("Moteur TTS : {engine}", "TTS engine: {engine}")),
    ("profile_tts_config_label", ("Configuration : {name}", "Configuration: {name}")),
    ("profile_btn_test_voice", ("🎤 Tester la voix", "🎤 Test voice")),
    ("profile_tts_audio_mgr_unavailable", ("❌ Audio manager non disponible", "❌ Audio manager not available")),
    ("profile_tts_test_in_progress", ("🔊 Test TTS en cours...", "🔊 TTS test in progress...")),
    ("profile_tts_test_text", ("Bonjour ! Test de la synthèse vocale. Ça fonctionne parfaitement !", "Hello! Voice synthesis test. It works perfectly!")),
    ("profile_tts_test_success", ("✅ Test TTS réussi !", "✅ TTS test successful!")),
    ("profile_tts_test_failed", ("❌ Échec test TTS", "❌ TTS test failed")),
    ("profile_tts_test_error", ("❌ Erreur test TTS : {err}", "❌ TTS test error: {err}")),
    ("profile_tts_config_module_unavailable", ("❌ Module de configuration TTS non disponible", "❌ TTS configuration module not available")),

    # STT
    ("profile_section_stt", ("🎙️ Transcription Audio (Speech-to-Text)", "🎙️ Audio Transcription (Speech-to-Text)")),
    ("profile_stt_engine_google", ("🌐 Google Speech Recognition (Gratuit)", "🌐 Google Speech Recognition (Free)")),
    ("profile_stt_engine_whisper", ("🤖 OpenAI Whisper (API - Haute précision)", "🤖 OpenAI Whisper (API - High accuracy)")),
    ("profile_stt_whisper_key_label", ("Clé API OpenAI Whisper", "OpenAI Whisper API Key")),
    ("profile_stt_whisper_key_saved", ("✅ Clé API Whisper sauvegardée", "✅ Whisper API key saved")),
    ("profile_stt_whisper_key_configured", ("✅ Clé configurée : {key}", "✅ Key configured: {key}")),
    ("profile_stt_whisper_no_key", ("⚠️ Aucune clé API configurée - ajoutez votre clé OpenAI", "⚠️ No API key configured - add your OpenAI key")),
    ("profile_stt_whisper_desc", ("OpenAI Whisper offre une transcription de haute précision. Nécessite une clé API OpenAI.", "OpenAI Whisper offers high-accuracy transcription. Requires an OpenAI API key.")),
    ("profile_stt_google_free", ("✅ Google Speech Recognition est gratuit et ne nécessite aucune configuration.", "✅ Google Speech Recognition is free and requires no configuration.")),
    ("profile_stt_google_precision", ("Précision correcte pour le français. Requiert une connexion internet.", "Reasonable accuracy for French. Requires an internet connection.")),
    ("profile_stt_engine_changed", ("Moteur STT : {engine}", "STT engine: {engine}")),
    ("profile_btn_test_stt", ("🎤 Tester la transcription", "🎤 Test transcription")),
    ("profile_stt_speak_now", ("🎙️ Parlez maintenant pendant 3 secondes...", "🎙️ Speak now for 3 seconds...")),
    ("profile_stt_transcription", ("✅ Transcription : \"{text}\"", "✅ Transcription: \"{text}\"")),
    ("profile_stt_no_transcription", ("❌ Aucune transcription obtenue", "❌ No transcription obtained")),
    ("profile_stt_record_unavailable", ("❌ Fonction record_once non disponible", "❌ record_once function not available")),
    ("profile_stt_test_error", ("❌ Erreur test STT : {err}", "❌ STT test error: {err}")),

    # Journal
    ("profile_section_journal", ("📔 Extension Journal de Bord", "📔 Journal Extension")),
    ("profile_journal_enable", ("Activer l'extension Journal de Bord", "Enable Journal extension")),
    ("profile_journal_desc", ("Quand activé, le journal injecte automatiquement le contexte de la journée au début des nouvelles conversations (max 3 entrées).", "When enabled, the journal automatically injects the day's context at the start of new conversations (max 3 entries).")),
    ("profile_journal_status_enabled", ("✅ Injection automatique de contexte", "✅ Automatic context injection")),
    ("profile_journal_status_disabled", ("❌ Pas d'injection de contexte", "❌ No context injection")),
    ("profile_journal_status_label", ("{icon} Statut: {status}", "{icon} Status: {status}")),
    ("profile_journal_state_on", ("activée", "enabled")),
    ("profile_journal_state_off", ("désactivée", "disabled")),
    ("profile_journal_toggled_notify", ("Extension Journal de Bord {state}", "Journal extension {state}")),
    ("profile_journal_not_init", ("Erreur : Journal non initialisé", "Error: Journal not initialised")),
    ("profile_journal_toggle_err", ("Erreur lors du basculement : {err}", "Toggle error: {err}")),
    ("profile_journal_not_available", ("❌ Extension Journal de Bord non disponible", "❌ Journal extension not available")),
    ("profile_journal_not_loaded", ("L'extension n'est pas chargée ou a rencontré une erreur au démarrage.", "The extension is not loaded or encountered an error at startup.")),

    # Hardware
    ("profile_section_hardware", ("🖥️ Caractéristiques Hardware", "🖥️ Hardware Characteristics")),
    ("profile_hardware_desc", ("Ces valeurs sont utilisées pour calculer les paramètres Ollama optimaux (context_length, max_tokens, low_vram). Modifiez-les si l'auto-détection est incorrecte.", "These values are used to calculate optimal Ollama parameters (context_length, max_tokens, low_vram). Modify them if auto-detection is incorrect.")),
    ("profile_hardware_detecting", ("Détection en cours...", "Detection in progress...")),
    ("profile_hardware_gpu_name_label", ("GPU (nom)", "GPU (name)")),
    ("profile_hardware_gpu_tooltip", ("Nom de votre carte graphique.\nExemple : NVIDIA RTX 4060, RTX 3080, etc.\nSi vous n'avez qu'un GPU intégré (Intel UHD, AMD Vega),\nlaissez vide — le modèle sera chargé en RAM CPU.", "Name of your graphics card.\nExample: NVIDIA RTX 4060, RTX 3080, etc.\nIf you only have an integrated GPU (Intel UHD, AMD Vega),\nleave empty — the model will be loaded into CPU RAM.")),
    ("profile_hardware_detected", ("Détecté : RAM {ram} Go, CPU {cpu} threads, GPU {gpu} ({vram} Go VRAM)", "Detected: RAM {ram} GB, CPU {cpu} threads, GPU {gpu} ({vram} GB VRAM)")),
    ("profile_hardware_detected_short", ("Hardware détecté", "Hardware detected")),
    ("profile_hardware_detect_error", ("Erreur détection : {err}", "Detection error: {err}")),
    ("profile_hardware_estimates_title", ("Estimations Ollama", "Ollama Estimates")),
    ("profile_hardware_enter_ram", ("Renseignez votre RAM pour voir les estimations.", "Enter your RAM to see estimates.")),
    ("profile_hardware_ram_usable", ("RAM utilisable estimée : ~{ram_usable} Go (70% de {ram})", "Estimated usable RAM: ~{ram_usable} GB (70% of {ram})")),
    ("profile_hardware_gpu_detected", ("GPU détecté ({vram} Go VRAM) — modèles chargés en VRAM (rapide)", "GPU detected ({vram} GB VRAM) — models loaded in VRAM (fast)")),
    ("profile_hardware_low_vram_off_gpu", ("low_vram conseillé : OFF (tout sur le GPU)", "Recommended low_vram: OFF (everything on GPU)")),
    ("profile_hardware_no_gpu", ("Pas de GPU dédié — modèles chargés en RAM CPU (plus lent)", "No dedicated GPU — models loaded in CPU RAM (slower)")),
    ("profile_hardware_low_vram_off_cpu", ("low_vram conseillé : OFF (sans GPU, ce paramètre n'a pas d'effet)", "Recommended low_vram: OFF (without GPU, this parameter has no effect)")),
    ("profile_hardware_mem_for_models", ("Mémoire dispo pour les modèles : ~{ram_usable} Go", "Memory available for models: ~{ram_usable} GB")),
    ("profile_hardware_models_ctx", ("Modèles Ollama — context_length conseillé :", "Ollama models — recommended context_length:")),
    ("profile_hardware_ollama_unavailable", ("Ollama non disponible — démarrez Ollama pour voir les estimations.", "Ollama not available — start Ollama to see estimates.")),
    ("profile_hardware_ollama_timeout", ("Ollama non joignable (timeout) — démarrez Ollama pour voir les estimations.", "Ollama unreachable (timeout) — start Ollama to see estimates.")),
    ("profile_btn_recalculate", ("Recalculer estimations", "Recalculate estimates")),
])


def _add_keys(path: Path, lang_idx: int):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f, object_pairs_hook=OrderedDict)
    added = 0
    for k, vals in NEW_KEYS.items():
        if k not in data:
            data[k] = vals[lang_idx]
            added += 1
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return added


if __name__ == "__main__":
    en_added = _add_keys(EN_PATH, 1)
    fr_added = _add_keys(FR_PATH, 0)
    print(f"EN: {en_added} keys added")
    print(f"FR: {fr_added} keys added")
