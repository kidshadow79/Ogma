"""
Proposition: Ajout d'un champ "Custom Model" pour Kie.ai

Similaire à Ollama, permettre la saisie manuelle du nom de modèle.
Format des modèles Kie: family/variant
Exemples:
- flux-2/pro-text-to-image
- flux-2/flex-text-to-image  
- flux-2/pro-image-to-image
- seedream-4.5/edit
- qwen-image/edit
- gpt-image-1.5/text-to-image
"""

# Modifications à apporter dans ogma_image_config.py

# 1. SECTION TEXT-TO-IMAGE
# Après le sélecteur de modèle, ajouter :

# === Pour Kie: Champ Custom Model (style Ollama) ===
if current_provider == "Kie":
    with ui.row().classes('gap-2 items-center w-full mt-2'):
        ui.label('🔧 Ou').classes('text-sm text-gray-400')
        custom_model_input = ui.input(
            label='Custom Model (ex: flux-2/pro-text-to-image)',
            value=''
        ).classes('flex-1').tooltip(
            'Entrez manuellement un nom de modèle Kie.ai (format: family/variant). '
            'Consultez https://kie.ai/market pour la liste complète.'
        )
        
        def use_custom_model():
            custom = custom_model_input.value.strip()
            if custom:
                # Ajouter à la liste si pas déjà présent
                if custom not in model_select.options:
                    model_select.options.append(custom)
                model_select.value = custom
                model_select.update()
                ui.notify(f'✅ Modèle custom activé: {custom}', type='positive')
            else:
                ui.notify('⚠️ Veuillez entrer un nom de modèle', type='warning')
        
        ui.button(
            icon='add',
            on_click=use_custom_model
        ).props('flat dense').classes('text-cyan-400').tooltip('Utiliser ce modèle')


# 2. SECTION IMAGE-TO-IMAGE
# Même chose pour la section img2img

if img2img_provider == "Kie":
    with ui.row().classes('gap-2 items-center w-full mt-2'):
        ui.label('🔧 Ou').classes('text-sm text-gray-400')
        custom_img2img_input = ui.input(
            label='Custom Model I2I (ex: flux-2/pro-image-to-image)',
            value=''
        ).classes('flex-1').tooltip(
            'Entrez manuellement un nom de modèle I2I Kie.ai (format: family/variant). '
            'Consultez https://kie.ai/market pour la liste complète.'
        )
        
        def use_custom_img2img():
            custom = custom_img2img_input.value.strip()
            if custom:
                if custom not in img2img_model_select.options:
                    img2img_model_select.options.append(custom)
                img2img_model_select.value = custom
                img2img_model_select.update()
                ui.notify(f'✅ Modèle I2I custom activé: {custom}', type='positive')
            else:
                ui.notify('⚠️ Veuillez entrer un nom de modèle', type='warning')
        
        ui.button(
            icon='add',
            on_click=use_custom_img2img
        ).props('flat dense').classes('text-blue-400').tooltip('Utiliser ce modèle')


# 3. AVANTAGES DE CETTE APPROCHE:
# 
# ✅ Pas besoin de maintenir une liste exhaustive
# ✅ Nouveaux modèles disponibles immédiatement
# ✅ Flexibilité comme Ollama
# ✅ Les modèles hardcodés restent accessibles
# ✅ Pas de refresh API nécessaire pour Kie
# ✅ L'utilisateur consulte kie.ai/market pour voir les modèles
#
# 4. WORKFLOW UTILISATEUR:
# 
# 1. Va sur https://kie.ai/market
# 2. Trouve un modèle (ex: "flux-2/pro-text-to-image")
# 3. Copie le nom depuis le Playground Kie
# 4. Le colle dans le champ "Custom Model"
# 5. Clique sur le bouton +
# 6. Le modèle est ajouté et sélectionné
#
# C'est exactement comme Ollama où on fait:
# ollama pull llama3.2:latest
# Sauf qu'ici c'est juste une saisie manuelle sans "pull"
