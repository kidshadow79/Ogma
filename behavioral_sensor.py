#!/usr/bin/env python3
"""
BehavioralSensor - Module de détection comportementale pour l'Archiviste OGMA
============================================================================

Détecte les patterns comportementaux de l'utilisateur :
- Absences prolongées (>2min)
- Pauses de réflexion (30s-2min) 
- Fatigue nocturne (délais croissants après 22h)
- Rythme conversationnel inhabituel

L'Archiviste utilise ces données pour contextualiser ses injections à Luna.
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
from dataclasses import dataclass


@dataclass
class BehavioralEvent:
    """Événement comportemental détecté"""
    timestamp: datetime
    event_type: str  # "absence", "reflexion", "fatigue", "retour"
    duration: float  # en secondes
    context: str     # Description pour l'Archiviste
    severity: float  # 0.0-1.0, gravité de l'événement


class BehavioralSensor:
    """
    Capteur comportemental pour l'Archiviste.
    
    Analyse les patterns temporels utilisateur et génère des observations
    contextuelles pour enrichir les interactions de Luna.
    """
    
    def __init__(self, enable_debug: bool = False):
        # Configuration des seuils
        self.thresholds = {
            "pause_courte": 10,      # 10s - normal
            "pause_reflexion": 30,   # 30s-2min - réflexion
            "pause_longue": 120,     # >2min - absence probable  
            "heure_fatigue": 22,     # 22h+ - surveillance fatigue
            "vitesse_baseline": 3.0, # 3s/réponse moyenne
            "facteur_fatigue": 2.0   # x2 plus lent = fatigue
        }
        
        # État de session
        self.session_start = datetime.now()
        self.last_user_message = None
        self.response_times = []  # Historique des temps de réponse
        self.behavioral_events = []  # Événements détectés
        self.conversation_count = 0
        
        # Configuration
        self.enable_debug = enable_debug
        self.max_events_memory = 50  # Limite mémoire événements
        
        if self.enable_debug:
            print(f"[BehavioralSensor] 🧠 Capteur comportemental initialisé")
            print(f"[BehavioralSensor] ⏱️ Session commencée: {self.session_start.strftime('%H:%M:%S')}")
    
    def register_user_message(self, message: str) -> Optional[BehavioralEvent]:
        """
        Enregistre un message utilisateur et analyse le pattern temporel.
        
        Args:
            message: Contenu du message utilisateur
            
        Returns:
            BehavioralEvent: Événement détecté ou None
        """
        now = datetime.now()
        self.conversation_count += 1
        
        # Premier message de la session
        if self.last_user_message is None:
            self.last_user_message = now
            if self.enable_debug:
                print(f"[BehavioralSensor] 📝 Premier message de session enregistré")
            return None
        
        # Calcul du délai depuis le dernier message
        time_gap = (now - self.last_user_message).total_seconds()
        self.response_times.append(time_gap)
        
        # Analyse du pattern
        event = self._analyze_timing_pattern(time_gap, now)
        
        # Mise à jour état
        self.last_user_message = now
        
        if event:
            self.behavioral_events.append(event)
            self._cleanup_old_events()
            
            if self.enable_debug:
                print(f"[BehavioralSensor] 🎯 Événement détecté: {event.event_type}")
                print(f"[BehavioralSensor] 📊 Délai: {time_gap:.1f}s | Contexte: {event.context}")
        
        return event
    
    def _analyze_timing_pattern(self, delay: float, timestamp: datetime) -> Optional[BehavioralEvent]:
        """Analyse le pattern temporel et génère un événement si pertinent."""
        
        # 1. Détection absence prolongée (>2min)
        if delay >= self.thresholds["pause_longue"]:
            return BehavioralEvent(
                timestamp=timestamp,
                event_type="absence",
                duration=delay,
                context=f"Absence de {delay//60:.0f} minutes détectée. L'utilisateur était probablement interrompu.",
                severity=min(0.8, delay / 300)  # Cap à 5min = severity 0.8
            )
        
        # 2. Détection pause réflexion (30s-2min)
        elif delay >= self.thresholds["pause_reflexion"]:
            return BehavioralEvent(
                timestamp=timestamp,
                event_type="reflexion", 
                duration=delay,
                context=f"Pause réflexive de {delay:.0f} secondes. L'utilisateur semble prendre le temps de formuler sa réponse.",
                severity=0.3
            )
        
        # 3. Détection fatigue nocturne
        elif self._is_fatigue_pattern(delay, timestamp):
            avg_recent = self._get_recent_response_average()
            return BehavioralEvent(
                timestamp=timestamp,
                event_type="fatigue",
                duration=delay,
                context=f"Ralentissement nocturne détecté ({delay:.1f}s vs {avg_recent:.1f}s habituels). Possibilité de fatigue.",
                severity=0.5
            )
        
        # 4. Détection retour après absence
        elif len(self.behavioral_events) > 0 and self.behavioral_events[-1].event_type == "absence":
            if delay <= self.thresholds["pause_courte"]:
                return BehavioralEvent(
                    timestamp=timestamp,
                    event_type="retour",
                    duration=delay,
                    context="Retour rapide après absence. L'utilisateur semble de nouveau disponible.",
                    severity=0.2
                )
        
        return None
    
    def _is_fatigue_pattern(self, current_delay: float, timestamp: datetime) -> bool:
        """Détecte un pattern de fatigue nocturne."""
        # Vérifier si c'est l'heure de fatigue
        if timestamp.hour < self.thresholds["heure_fatigue"]:
            return False
        
        # Besoin d'historique pour comparaison
        if len(self.response_times) < 3:
            return False
        
        # Comparer avec la moyenne récente
        recent_avg = self._get_recent_response_average()
        
        # Pattern fatigue : délai actuel significativement plus lent
        return current_delay > (recent_avg * self.thresholds["facteur_fatigue"])
    
    def _get_recent_response_average(self, window: int = 5) -> float:
        """Calcule la moyenne des derniers temps de réponse."""
        if not self.response_times:
            return self.thresholds["vitesse_baseline"]
        
        recent = self.response_times[-window:]
        return sum(recent) / len(recent)
    
    def _cleanup_old_events(self):
        """Nettoie les anciens événements pour éviter la surcharge mémoire."""
        if len(self.behavioral_events) > self.max_events_memory:
            self.behavioral_events = self.behavioral_events[-self.max_events_memory:]
    
    def get_archiviste_context(self) -> str:
        """
        Génère un contexte comportemental pour l'Archiviste.
        
        Returns:
            str: Résumé comportemental pour injection à Luna
        """
        if not self.behavioral_events:
            return ""
        
        # Récupérer les événements récents significatifs
        recent_events = [e for e in self.behavioral_events[-3:] if e.severity >= 0.3]
        
        if not recent_events:
            return ""
        
        # Construire le contexte
        context_lines = []
        for event in recent_events:
            context_lines.append(f"• {event.context}")
        
        return f"Observations comportementales récentes :\n" + "\n".join(context_lines)
    
    def get_session_summary(self) -> Dict:
        """Résumé de session pour debug/monitoring."""
        now = datetime.now()
        session_duration = (now - self.session_start).total_seconds()
        
        events_by_type = {}
        for event in self.behavioral_events:
            events_by_type[event.event_type] = events_by_type.get(event.event_type, 0) + 1
        
        return {
            "session_duration_minutes": session_duration / 60,
            "total_messages": self.conversation_count,
            "events_detected": len(self.behavioral_events),
            "events_by_type": events_by_type,
            "average_response_time": self._get_recent_response_average(),
            "current_hour": now.hour,
            "fatigue_monitoring_active": now.hour >= self.thresholds["heure_fatigue"]
        }
    
    def test_behavior_detection(self):
        """Test des capacités de détection comportementale."""
        print("\n" + "="*60)
        print("🧪 TEST DÉTECTION COMPORTEMENTALE")
        print("="*60)
        
        # Simulation de patterns
        test_scenarios = [
            (5, "Message normal"),
            (35, "Pause réflexion"), 
            (150, "Absence prolongée"),
            (8, "Retour après absence"),
            (25, "Réponse nocturne lente (si 22h+)")
        ]
        
        print("\n📊 SIMULATION DE PATTERNS:")
        print("-" * 40)
        
        for delay, description in test_scenarios:
            # Simuler le délai
            test_time = datetime.now()
            if self.last_user_message:
                test_time = self.last_user_message + timedelta(seconds=delay)
            
            event = self._analyze_timing_pattern(delay, test_time)
            
            print(f"\n{description}:")
            print(f"   Délai: {delay}s")
            if event:
                print(f"   ✅ Détecté: {event.event_type} (sévérité: {event.severity:.1f})")
                print(f"   📝 Contexte: {event.context}")
            else:
                print(f"   ⭕ Aucun événement détecté")
            
            # Mettre à jour l'état pour la suite du test
            self.last_user_message = test_time
            self.response_times.append(delay)


if __name__ == "__main__":
    print("🧠 OGMA - MODULE DÉTECTION COMPORTEMENTALE")
    print("==========================================")
    
    # Test du module
    sensor = BehavioralSensor(enable_debug=True)
    
    # Tests de détection
    sensor.test_behavior_detection()
    
    print("\n" + "="*60)
    print("✅ MODULE PRÊT POUR INTÉGRATION ARCHIVISTE")
    print("="*60)
    print("📝 Instructions d'intégration:")
    print("1. Importer: from behavioral_sensor import BehavioralSensor")
    print("2. Initialiser: sensor = BehavioralSensor()")
    print("3. Enregistrer: event = sensor.register_user_message(message)")
    print("4. Contexte: context = sensor.get_archiviste_context()")
    print("5. Injecter le contexte dans les prompts de l'Archiviste")
    print("\n🎯 Résultat: Archiviste contextuellement conscient du comportement utilisateur!")