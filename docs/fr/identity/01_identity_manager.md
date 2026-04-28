# Gestionnaire d'identités

**Sources vérifiées** : `identity_manager.py`, `data/identities.json`, `data/identities.default.json`

---

## Rôle

OGMA peut fonctionner avec différents profils utilisateur-IA. L'`IdentityManager` abstrait les noms et descriptions pour éviter tout codage en dur. Au lieu de références fixes à "Yohan" et "Luna", tous les composants passent par ce gestionnaire.

---

## Structure des données

`data/identities.json` contient un dictionnaire de profils et le profil actif :

```json
{
  "current_profile": "profile_1",
  "profiles": {
    "profile_1": {
      "user_name": "Utilisateur",
      "ai_name": "Assistant",
      "ai_description": "...",
      "relationship_type": "collaborative",
      "relationship_context": "..."
    }
  },
  "defaults": { ... }
}
```

Le champ `relationship_context` supporte la variable `{user_name}` qui est remplacée à l'utilisation.

---

## Bootstrap

Si `data/identities.json` n'existe pas au démarrage, le système cherche `data/identities.default.json` et le copie. Si aucun fichier par défaut n'est disponible non plus, une configuration minimale est générée et sauvegardée. Ce pattern est identique à celui du `SettingsManager` avec `settings.example.json`.

---

## API principale

| Fonction | Rôle |
|---|---|
| `get_current_user_name()` | Retourne le nom de l'utilisateur du profil actif |
| `get_current_ai_name()` | Retourne le nom de l'IA du profil actif |
| `get_relationship_context()` | Retourne la description relationnelle avec `{user_name}` résolu |
| `set_current_profile(id)` | Change le profil actif |
| `create_profile(...)` | Crée un nouveau profil |

---

## Multi-profils

Plusieurs profils peuvent coexister (famille, travail, test). La commutation entre profils est instantanée. Le profil actif est persisté dans `identities.json` et restauré au redémarrage.
