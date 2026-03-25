# 🎤 Guide des Triggers Vocaux OGMA

## Comment Modifier les Triggers

### 1️⃣ Via le Frontend (Interface OGMA)
1. Ouvrez les paramètres (⚙️)
2. Section "Voice" 
3. Modifiez `trigger_activation` et/ou `trigger_send`
4. Sauvegardez

### 2️⃣ Via settings.json
Éditez directement `data/settings.json` :
```json
{
  "voice": {
    "trigger_activation": "votre trigger ici",
    "trigger_send": "votre trigger envoi"
  }
}
```

## ⚡ Prise en Compte en Temps Réel

Les triggers sont **rechargés automatiquement** quand vous :
- **Focus** sur le champ de message (clic dedans)
- **Blur** puis **refocus** si déjà actif

**Vous n'avez PAS besoin de redémarrer OGMA !**

### Exemple de workflow :
1. OGMA tourne avec trigger "louna louna"
2. Vous changez pour "ma louna" dans les settings
3. **Cliquez hors du champ message** (blur)
4. **Recliquez dans le champ** (focus)
5. ✅ Le nouveau trigger "ma louna" est actif !

## 🎯 Triggers Prédéfinis avec Variantes

### Trigger d'Activation

| Trigger configuré | Variantes automatiques |
|-------------------|------------------------|
| `louna louna` | luna luna, l'une l'une, lune lune, louis louis, etc. |
| `ma louna` | ma luna, malouna, ma l'une, ma lune, etc. |
| **Personnalisé** | Version sans espace uniquement |

### Trigger d'Envoi

| Trigger configuré | Variantes automatiques |
|-------------------|------------------------|
| `point final` | pointfinal, fini, terminé, fin, envoi, etc. |
| `envoie` | envoi, envois, envoie le, envoie ça, etc. |
| `c'est bon` | cest bon, c bon, ok c'est bon, etc. |
| `gogogo` | go go go, gogo, gaugaugau, etc. |
| **Personnalisé** | Version sans espace uniquement |

## 🧪 Tester Vos Triggers

### Dans le Terminal
```bash
python test_trigger_variants.py
```

### Via les Logs
Activez le mode vocal et regardez les logs :
```
[TRIGGERS-DEBUG] 🔍 Variantes pour 'ma louna': ...
[TRIGGERS-DEBUG] 📤 Variantes ENVOI pour 'point final': ...
```

### Test en Live
1. Activez mode vocal (focus champ message)
2. Dites votre trigger d'activation
3. Si détecté : `[TRIGGERS] 🎯 Activation détectée: '...'`
4. Parlez votre message
5. Dites votre trigger d'envoi
6. Si détecté : `[TRIGGERS] 🚀 Envoi détecté: '...'`

## 💡 Conseils pour Choisir un Bon Trigger

### ✅ Bonnes Pratiques
- **Court** : 2-3 syllabes max
- **Distinct** : Pas utilisé dans conversation normale
- **Phonétique claire** : Sons bien distincts
- **Répétable** : Facile à prononcer plusieurs fois

### ❌ À Éviter
- Mots trop courants ("oui", "non", "ok" seuls)
- Triggers trop longs (> 4 mots)
- Homophones ambigus
- Combinaisons difficiles à prononcer

### 🎯 Exemples Recommandés

**Activation :**
- "hey luna" (anglais-français mixte)
- "ma louna" (français, affectif)
- "écoute moi" (français naturel)
- "oh lala" (français distinctif)

**Envoi :**
- "c'est bon" (naturel en français)
- "envoie" (court, efficace)
- "valider" (formel, clair)
- "go go" (court, dynamique)

## 🔧 Dépannage

### Le trigger ne se met pas à jour
1. Vérifiez `data/settings.json` :
   ```bash
   python -c "import json; print(json.load(open('data/settings.json'))['voice'])"
   ```
2. **Blur/refocus** le champ message
3. Vérifiez les logs : `[VOICE] 📋 Config: activation='...'`

### Le mauvais trigger se déclenche encore
- Les variantes hardcodées ne s'activent que pour triggers exacts
- "luna luna" ne se déclenche plus si trigger = "ma louna"
- Vérifiez les logs `[TRIGGERS-DEBUG]` pour voir les variantes actives

### Le trigger ne détecte pas ma voix
1. Vérifiez calibration micro : `[AUDIO] 🎚️ Seuil détection: ...`
2. Seuil trop haut ? Réduisez dans settings : `energy_threshold: 200`
3. Testez transcription : parlez et vérifiez `[AUDIO] ✅ Transcrit: '...'`

## 🚀 Contribution

Pour ajouter des variantes pour un nouveau trigger :
1. Éditez `modules/voice/voice_triggers.py`
2. Ajoutez un bloc `elif base == "votre trigger":`
3. Listez les variantes phonétiques probables
4. Testez avec `test_trigger_variants.py`

---

**Dernière mise à jour** : 15 janvier 2026  
**Version OGMA** : 2.2+  
**Auteur** : Yohan BROCARD & Assistant IA
