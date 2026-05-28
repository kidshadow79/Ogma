"""
project_cache_ui.py
-------------------
Interface modulaire pour la gestion du Prompt Caching (NotebookLM style).
Gère la bascule de cache, le chronomètre asynchrone et l'estimation des coûts.
"""

from nicegui import ui
import json
from pathlib import Path
from typing import Callable, Optional

class ProjectCacheUI:
    def __init__(self, container, config, settings_manager=None, on_toggle_callback: Optional[Callable[[bool], None]] = None):
        self.config = config
        self.settings_manager = settings_manager
        self.on_toggle_callback = on_toggle_callback

        # Charger les tarifs dynamiquement ou depuis la config
        if not hasattr(self.config, 'cache_pricing_data'):
            self.config.cache_pricing_data = {}
        self.pricing_data = self.config.cache_pricing_data
        
        pricing_file = Path(__file__).parent / "pricing_config.json"
        if not self.pricing_data:
            try:
                if pricing_file.exists():
                    with open(pricing_file, "r", encoding="utf-8") as f:
                        self.config.cache_pricing_data = json.load(f)
                        self.pricing_data = self.config.cache_pricing_data
            except Exception as e:
                print(f"[PROJECT-CACHE-UI] Erreur chargement prix: {e}")
                
        # Lancer la mise à jour des prix en tâche de fond
        ui.timer(0.5, lambda: self._fetch_live_pricing(pricing_file), once=True)
        
        # Restaurer l'état
        import time
        if not hasattr(self.config, 'cache_expiration_timestamp'):
            old_rem = getattr(self.config, 'cache_remaining_seconds', 0)
            if old_rem > 0:
                self.config.cache_expiration_timestamp = time.time() + old_rem
            else:
                self.config.cache_expiration_timestamp = 0.0
        if not hasattr(self.config, 'cache_current_cost') or self.config.cache_current_cost == 0.0:
            self.config.cache_current_cost = 0.0
            ui.timer(0.6, self._estimate_initial_cost, once=True)
            
        self.cache_active = getattr(self.config, 'use_full_cache', False)
        
        # Le timer NiceGUI
        self._timer = ui.timer(1.0, self._tick, active=(self.cache_active and self.get_remaining_seconds() > 0))
        
        with container:
            self._render()

    async def _fetch_live_pricing(self, pricing_file: Path):
        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://openrouter.ai/api/v1/models", timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        models = data.get("data", [])
                        
                        if "models" not in self.pricing_data:
                            self.pricing_data["models"] = {}
                            
                        updated = False
                        for m in models:
                            m_id = m.get("id", "")
                            # Filtrer sur les principaux providers pour éviter un fichier trop lourd
                            if any(k in m_id.lower() for k in ["anthropic", "google", "openai", "deepseek", "mistral", "x-ai"]):
                                pricing = m.get("pricing", {})
                                try:
                                    # OpenRouter donne le prix pour 1 token, on le ramène à 1M
                                    prompt_cost = float(pricing.get("prompt", 0)) * 1000000
                                    completion_cost = float(pricing.get("completion", 0)) * 1000000
                                    
                                    # Heuristiques de cache (souvent 10% lecture, 125% écriture pour Anthropic/DeepSeek)
                                    cache_read = prompt_cost * 0.1
                                    cache_write = prompt_cost * 1.25
                                    
                                    # OGMA peut envoyer "provider/model" ou juste "model"
                                    short_name = m_id.split("/")[-1]
                                    
                                    entry = {
                                        "base_input": round(prompt_cost, 4),
                                        "cache_write": round(cache_write, 4),
                                        "cache_read": round(cache_read, 4),
                                        "output": round(completion_cost, 4)
                                    }
                                    
                                    self.pricing_data["models"][short_name] = entry
                                    self.pricing_data["models"][m_id] = entry
                                    updated = True
                                except Exception:
                                    continue
                        
                        if updated:
                            with open(pricing_file, "w", encoding="utf-8") as f:
                                json.dump(self.pricing_data, f, indent=2)
                            print("[PROJECT-CACHE-UI] 🔄 Tarifs mis à jour automatiquement depuis OpenRouter.")
        except Exception as e:
            print(f"[PROJECT-CACHE-UI] ⚠️ Echec MAJ prix OpenRouter (mode hors-ligne actif) : {e}")

    def _is_gguf_active(self) -> bool:
        """Vérifie si l'IA Principale utilise GGUF (auquel cas le cache API n'a pas de sens)."""
        if not self.settings_manager:
            return False
        return self.settings_manager.settings.get('active_provider', '').lower() == 'gguf'

    def _render(self):
        with ui.row().classes('items-center gap-2'):
            # Switch de bascule
            is_gguf = self._is_gguf_active()
            has_direct_inject = len(getattr(self.config, 'direct_inject_files', [])) > 0

            with ui.column().classes('gap-0'):
                self.switch = ui.switch(
                    'Mise en cache complet', 
                    value=self.cache_active,
                    on_change=self._on_switch_change
                ).props('color="purple"')
                
                # Label dynamique explicatif pour l'UX
                self.mode_label = ui.label(
                    "Mode: Cache Complet API (NotebookLM)" if self.cache_active else "Mode: Super Chunk (Vectoriel FAISS)"
                ).classes('text-xs italic').style('color: #8a7e74;' if not is_gguf else 'color: #555555;')

            if is_gguf:
                self.switch.props('disable')
                self.switch.tooltip("Le cache intégral API n'est pas compatible avec le modèle local GGUF.")
            elif has_direct_inject:
                self.switch.props('disable')
                self.switch.tooltip("Désélectionne les fichiers en injection directe pour activer le cache complet.")
            else:
                self.switch.tooltip("Charge tout le projet en RAM serveur (coût initial plus élevé, mais vision parfaite du texte). Désactivez pour utiliser FAISS.")

            # Affichage du statut (Temps + Coût)
            with ui.row().classes('items-center gap-2').bind_visibility_from(self, 'cache_active'):
                with ui.column().classes('col-span-1 items-center justify-center border-r border-slate-700'):
                    ui.icon('schedule', size='sm', color='slate-400')
                    
                    remaining = self.get_remaining_seconds()
                    mins = remaining // 60
                    secs = remaining % 60
                    self.time_label = ui.label(f"{mins:02d}:{secs:02d}" if remaining > 0 else "EXPIRÉ").classes('text-xs text-slate-300 font-mono')
                    ui.label('RESTANT').classes('text-[10px] text-slate-500 font-bold tracking-wider')

                # Section Coût
                with ui.column().classes('col-span-1 items-center justify-center'):
                    ui.icon('payments', size='sm', color='emerald-500')
                    self.cost_label = ui.label(f"${self.config.cache_current_cost:.4f}").classes('text-xs text-emerald-400 font-mono')

    def _on_switch_change(self, e):
        # Bloquer si Mode 3 actif
        if e.value and len(getattr(self.config, 'direct_inject_files', [])) > 0:
            self.switch.set_value(False)
            ui.notify("Désélectionne les fichiers en injection directe avant d'activer le cache complet.", type='warning')
            return
        self.cache_active = e.value
        # Sauvegarde dans la config
        self.config.use_full_cache = self.cache_active
        
        if hasattr(self, 'mode_label'):
            self.mode_label.set_text("Mode: Cache Complet API (NotebookLM)" if self.cache_active else "Mode: Super Chunk (Vectoriel FAISS)")
            
        if self.cache_active:
            ui.notify("Mise en cache activée : l'IA va lire l'intégralité du projet.", type='info')
            # Reset timer si on l'active
            # Reset timer si on l'active
            if self.get_remaining_seconds() <= 0:
                self.reset_timer()
            self._timer.activate()
        else:
            ui.notify("Retour au Super Chunk (FAISS classique).", type='warning')
            self._timer.deactivate()
            
        if self.on_toggle_callback:
            self.on_toggle_callback(self.cache_active)

    def update_state(self):
        """Rafraichit l'etat du switch selon la config (appele apres un toggle Mode 3)."""
        if not hasattr(self, 'switch'):
            return
        has_direct = len(getattr(self.config, 'direct_inject_files', [])) > 0
        is_gguf = self._is_gguf_active()
        if has_direct or is_gguf:
            self.switch.props('disable')
            tooltip = (
                "Désélectionne les fichiers en injection directe pour activer le cache complet."
                if has_direct else
                "Le cache intégral API n'est pas compatible avec le modèle local GGUF."
            )
            self.switch.tooltip(tooltip)
        else:
            self.switch.props(remove='disable')
            self.switch.tooltip("Charge tout le projet en RAM serveur (coût initial plus élevé, mais vision parfaite du texte). Désactivez pour utiliser FAISS.")

    def get_remaining_seconds(self) -> int:
        """Calcule dynamiquement le nombre de secondes restantes."""
        import time
        exp = getattr(self.config, 'cache_expiration_timestamp', 0.0)
        rem = max(0, int(exp - time.time()))
        # Maintenir pour compatibilité externe si besoin
        self.config.cache_remaining_seconds = rem
        return rem

    def _tick(self):
        """Met à jour le chronomètre chaque seconde sans modifier la valeur sur disque."""
        remaining = self.get_remaining_seconds()
        if remaining > 0:
            mins = remaining // 60
            secs = remaining % 60
            if hasattr(self, 'time_label'):
                try:
                    self.time_label.set_text(f"{mins:02d}:{secs:02d}")
                except Exception:
                    pass
        else:
            if hasattr(self, 'time_label'):
                try:
                    self.time_label.set_text("EXPIRÉ")
                except Exception:
                    pass
            self._timer.deactivate()

    def reset_timer(self, minutes: int = 60):
        """Réinitialise le chronomètre à la durée spécifiée (ex: lors d'un Cache Hit)."""
        import time
        self.config.cache_expiration_timestamp = time.time() + minutes * 60
        remaining = minutes * 60
        self.config.cache_remaining_seconds = remaining
        mins = remaining // 60
        secs = remaining % 60
        if hasattr(self, 'time_label'):
            try:
                self.time_label.set_text(f"{mins:02d}:{secs:02d}")
            except Exception:
                pass
        if self.cache_active:
            self._timer.activate()

    def add_cost(self, dollars: float):
        """Ajoute un montant au coût de la session en direct."""
        print(f"[PROJECT-CACHE-UI] add_cost appelé avec : {dollars}$")
        self.config.cache_current_cost += dollars
        self.update_ui_display()

    def update_ui_display(self):
        """Met à jour l'affichage en direct de l'UI."""
        if hasattr(self, 'cost_label'):
            try:
                self.cost_label.set_text(f"${self.config.cache_current_cost:.4f}")
            except Exception as e:
                print(f"[PROJECT-CACHE-UI] Erreur màj UI cost: {e}")
        self._tick()

    def _estimate_project_tokens(self) -> int:
        """Estime le nombre total de tokens dans les documents du projet."""
        total_tokens = 0
        try:
            for f_record in self.config.files:
                file_id = f_record.get('id')
                filename = f_record.get('filename')
                text_path = self.config.files_dir / f"{file_id}.txt"
                if text_path.exists():
                    text = text_path.read_text(encoding='utf-8', errors='ignore')
                    total_tokens += len(text) // 4
                else:
                    total_tokens += f_record.get('file_size', 0) // 4
        except Exception as e:
            print(f"[PROJECT-CACHE-UI] Erreur estimation tokens: {e}")
        return max(0, total_tokens)

    def _estimate_initial_cost(self):
        """Calcule le coût d'écriture initial estimé basé sur les documents RAG et le modèle actif."""
        try:
            # Récupérer le modèle actif
            model_name = "default"
            try:
                import sys
                ogma_ng = sys.modules.get('ogma_ng')
                if ogma_ng and hasattr(ogma_ng, '_ensure_chat_controller'):
                    model_name = ogma_ng._ensure_chat_controller().model
            except Exception:
                pass

            pricing = self.pricing_data.get('models', {}) or {}
            
            # Normalisation et nettoyage du nom de modèle
            def clean_model_name(n):
                return n.lower().replace('.', '').replace('-', '').replace('_', '').replace('/', '')
            
            cleaned_ctrl = clean_model_name(model_name)
            model_price = None
            
            # 1. Recherche exacte
            for k, v in pricing.items():
                if k.lower() == model_name.lower():
                    model_price = v
                    break
            
            # 2. Recherche partielle
            if not model_price:
                for k, v in pricing.items():
                    cleaned_k = clean_model_name(k)
                    if cleaned_k == cleaned_ctrl or cleaned_k in cleaned_ctrl or cleaned_ctrl in cleaned_k:
                        model_price = v
                        break
            
            # 3. Fallback
            if not model_price:
                model_price = pricing.get('default', {
                    "base_input": 3.0,
                    "cache_write": 3.75,
                    "cache_read": 0.30,
                    "output": 15.0
                })
            
            est_tokens = self._estimate_project_tokens()
            write_rate = model_price.get('cache_write', 3.75)
            self.config.cache_current_cost = (est_tokens * write_rate) / 1000000
            print(f"[PROJECT-CACHE-UI] 💸 Coût d'écriture estimé initial pour {est_tokens} tokens : {self.config.cache_current_cost:.4f}$ (Modèle détecté: {model_name})")
            
            self.update_ui_display()
        except Exception as e:
            print(f"[PROJECT-CACHE-UI] Erreur lors de l'estimation du coût d'écriture: {e}")
