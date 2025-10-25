# Extension Temporal Guardian - Guide d'Intégration OGMA

## Vue d'Ensemble

L'extension **Temporal Guardian** implémente la gestion temporelle organique demandée pour OGMA v2.0, où "*c'est l'archiviste qui a l'horodatage et c'est lui qui analyse les temps d'absence et les moments de fatigue de l'utilisateur et il en informe l'ia principale*".

### Architecture Simple

```
[Message Utilisateur] → [TemporalSensor] → [ArchivisteEnricher] → [Archiviste enrichi]
                                      ↓
                               [TemporalGuardian] → [Alerte IA principale si nécessaire]
```

### Philosophie

- **Capteur simple** : Mesure les délais temporels sans interprétation
- **Archiviste intelligent** : Reçoit les données temporelles et en déduit les patterns comportementaux
- **IA principale informée** : Alertée seulement quand l'archiviste détecte quelque chose de significatif

## Intégration dans OGMA

### 1. Import dans ogma_ng.py

```python
from extensions.temporal_guardian import create_temporal_guardian

class OgmaNGUI:
    def __init__(self):
        # ... code existant ...
        
        # Initialiser Temporal Guardian
        self.temporal_guardian = create_temporal_guardian(debug=True)
```

### 2. Traitement des messages utilisateur

```python
async def send_user_message(self, message: str):
    """Traiter message utilisateur avec contexte temporel."""
    
    # === NOUVEAU CODE TEMPORAL ===
    # Traiter avec Temporal Guardian
    temporal_result = self.temporal_guardian.process_user_message(
        user_message=message,
        archiviste_prompt=self.get_archiviste_base_prompt()
    )
    
    # Utiliser prompt archiviste enrichi
    enriched_archiviste_prompt = temporal_result["enriched_archiviste_prompt"]
    
    # Alerter IA principale si nécessaire
    if temporal_result["should_alert_main_ai"]:
        temporal_alert = f"CONTEXTE TEMPOREL: {temporal_result['temporal_summary']}"
        # Intégrer dans prompt IA principale
    # === FIN NOUVEAU CODE ===
    
    # Traitement habituel...
    response = await self.process_message_with_archiviste(
        message, 
        archiviste_prompt=enriched_archiviste_prompt
    )
```

### 3. Exemple d'enrichissement automatique

**Message utilisateur** : "Tu peux m'aider ?"  
**Délai depuis dernier message** : 4 minutes

**Prompt archiviste de base** :
```
Analysez ce message utilisateur et mémorisez les éléments importants.
```

**Prompt archiviste enrichi automatiquement** :
```
Analysez ce message utilisateur et mémorisez les éléments importants.

🕒 14:35 | ⏱️ Délai: 4.2min | 📊 Session: 15min, 8 messages | 📈 Rythme moyen: 1.8min
```

L'archiviste peut maintenant analyser : "*L'utilisateur prend plus de temps que d'habitude pour répondre (4.2min vs 1.8min habituel), possiblement en réflexion ou fatigue*".

## Configuration

### Configuration par défaut

```python
# Configuration simple
guardian = create_temporal_guardian(debug=True)

# Configuration personnalisée
from extensions.temporal_guardian import TemporalGuardianConfig

config = TemporalGuardianConfig()
config.temporal_context_format = "simple"  # ou "detailed"
config.enrich_archiviste_prompt = True
config.session_timeout_minutes = 30

guardian = create_temporal_guardian(config.to_dict(), debug=True)
```

### Formats d'enrichissement

#### Format Simple
```
Délai: 2.5min (msg #5)
```

#### Format Détaillé
```
🕒 14:35 | ⏱️ Délai: 2.5min | 📊 Session: 15min, 5 messages | 📈 Rythme moyen: 1.8min
```

## API de l'Extension

### Méthode principale

```python
result = guardian.process_user_message(user_message, archiviste_prompt)

# result contient:
{
    "enriched_archiviste_prompt": str,  # Prompt enrichi pour l'archiviste
    "temporal_data": TemporalMeasurement,  # Données temporelles brutes
    "should_alert_main_ai": bool,  # Si l'IA principale doit être informée
    "temporal_summary": str  # Résumé pour monitoring
}
```

### Données temporelles disponibles

```python
measurement = result["temporal_data"]

# Données accessibles:
measurement.delay_since_last      # Délai en secondes (None pour premier message)
measurement.current_time_str      # "14:35"
measurement.session_duration      # Durée session en secondes  
measurement.message_count         # Numéro du message
measurement.average_delay         # Délai moyen utilisateur (None si <3 messages)
```

### Gestion de session

```python
# Vérifier si nouvelle session nécessaire
if guardian.should_reset_session():
    guardian.reset_session()

# Stats pour monitoring
stats = guardian.get_session_stats()
print(f"Session: {stats['session_duration_minutes']:.1f}min, {stats['total_messages']} messages")
```

## Instructions pour l'Archiviste

L'extension enrichit automatiquement le prompt, mais voici des instructions suggérées pour l'archiviste :

```
INSTRUCTION ARCHIVISTE TEMPOREL:
Vous recevez des données temporelles avec chaque message utilisateur.
Analysez ces patterns pour détecter:

- Fatigue utilisateur (délais croissants)
- Moments de réflexion (pauses de 30s-2min)
- Absences prolongées (>5min)
- Changements de rythme significatifs

Informez l'IA principale quand vous détectez:
- Fatigue évidente → "L'utilisateur semble fatigué (rythme ralenti)"
- Réflexion profonde → "L'utilisateur prend le temps de réfléchir"
- Retour après absence → "L'utilisateur revient après une pause"

Contexte temporel fourni automatiquement avec chaque message.
```

## Avantages vs Ancienne Approche

### ❌ Ancien système (temporal_injector.py)
- Injection rigide avec prompt fixe
- Pas de mesure réelle des délais
- Déconnecté de l'archiviste

### ✅ Nouveau système (Temporal Guardian)
- **Mesure réelle** des délais utilisateur
- **Archiviste enrichi** automatiquement avec contexte temporel
- **IA principale alertée** seulement quand nécessaire
- **Architecture organique** : capteur mesure, archiviste interprète

## Test de Validation

L'extension est testée et fonctionnelle :

```bash
cd c:\AI\OGMA
python test_temporal_guardian_simple.py
```

**Résultat attendu** :
```
✅ Test réussi! Extension Temporal Guardian fonctionnelle.
```

## Points d'Intégration OGMA

1. **Lors de l'envoi d'un message utilisateur** → Appeler `guardian.process_user_message()`
2. **Prompt archiviste** → Utiliser `result["enriched_archiviste_prompt"]`
3. **Alertes IA principale** → Vérifier `result["should_alert_main_ai"]`
4. **Début de session** → Gérer reset automatique avec `guardian.should_reset_session()`

Cette extension replace complètement l'ancien `temporal_injector.py` avec une approche plus intelligente et organique.