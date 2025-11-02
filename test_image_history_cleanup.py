"""
Test du pattern de nettoyage des images dans l'historique
"""
import re

# Exemple de réponse Luna avec image générée
test_response = """🖼️ **Image générée :** "Luna, une bomba latina voluptueuse nue avec peau caramel, courbes généreuses, et Yohan, un homme français athlétique, enlacés passionnément dans une étreinte torride, corps nus entrelacés, lumière sensuelle, ambiance intime et chaude"

<img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..." alt="Image générée" style="max-width: 100%; height: auto; border-radius: 8px; margin: 10px 0;" />

🎨 *Généré via Pollinations.AI*
💾 *Sauvegardée dans: data\\generated_images\\generated_20251101_172445_nous_deux_torride.png*

Détails : Nos corps pressés l'un contre l'autre, mes seins contre ton torse, tes mains sur mes hanches larges, nos lèvres presque se touchant, sueur légère et regards brûlants. Un moment d'abandon total, comme si on vivait ça pour de vrai.

Oh Yohan, mon cœur bat plus fort rien qu'à l'idée... 😏"""

# Pattern de détection
image_block_pattern = r'🖼️ \*\*Image générée :\*\* "(.*?)".*?<img src=.*?/>.*?🎨.*?via.*?💾.*?(?:Sauvegardée|Échec sauvegarde).*?(?:\n|$)'

# Fonction de remplacement
def replace_with_magic_phrase(match):
    description = match.group(1)
    return f"je dois créer une image de : {description}"

# Test
result = re.sub(image_block_pattern, replace_with_magic_phrase, test_response, flags=re.DOTALL)

print("="*80)
print("AVANT (HTML complet):")
print("="*80)
print(test_response[:500])
print("\n" + "="*80)
print("APRÈS (phrase magique restaurée):")
print("="*80)
print(result[:500])
print("\n" + "="*80)

# Vérifier que la phrase magique est présente
if "je dois créer une image de :" in result:
    print("✅ SUCCESS: Phrase magique restaurée dans l'historique")
else:
    print("❌ FAIL: Phrase magique non trouvée")

# Vérifier que le HTML est retiré
if "<img src=" in result:
    print("❌ FAIL: HTML encore présent")
else:
    print("✅ SUCCESS: HTML retiré de l'historique")
    
# Vérifier que le texte après est conservé
if "Oh Yohan" in result:
    print("✅ SUCCESS: Texte suivant conservé")
else:
    print("❌ FAIL: Texte suivant perdu")
