"""
Hologram Projector - Serveur de diffusion
==========================================

Routes FastAPI sur l'app NiceGUI :
  GET  /hologram      -> hologram.html
  WS   /hologram/ws  -> WebSocket etat live (emotion + speaking)

Le worker broadcast est lance au premier client WS qui se connecte,
garantissant qu il tourne dans le bon event loop NiceGUI.
"""

from pathlib import Path
from fastapi import Response, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, PlainTextResponse

_STATIC_DIR = Path(__file__).parent / "static"
_worker_started = False


def register_routes():
    """
    Enregistre /hologram et /hologram/ws sur l app FastAPI de NiceGUI.
    """
    try:
        from nicegui import app as nicegui_app
        from .state_emitter import register_client, unregister_client, get_state, is_enabled, drain_broadcast_queue
        import json
        import asyncio

        # -- Route /hologram -> visage dans la fumee (par defaut) -----------
        async def hologram_page(request) -> Response:
            html_file = _STATIC_DIR / "hologram_v2.html"
            if not html_file.exists():
                return PlainTextResponse(
                    f"hologram_v2.html introuvable dans {_STATIC_DIR}",
                    status_code=404
                )
            return FileResponse(str(html_file), media_type="text/html")

        nicegui_app.add_route("/hologram", hologram_page, methods=["GET"])

        # -- Fichier statique Three.js (servi localement) -------------------
        async def three_js(request) -> Response:
            js_file = _STATIC_DIR / "three.min.js"
            if not js_file.exists():
                return PlainTextResponse("three.min.js introuvable", status_code=404)
            return FileResponse(str(js_file), media_type="application/javascript")

        nicegui_app.add_route("/hologram/three.min.js", three_js, methods=["GET"])

        # -- Route /hologram2 -> sphere wireframe Three.js ------------------
        async def hologram_v2_page(request) -> Response:
            html_file = _STATIC_DIR / "hologram.html"
            if not html_file.exists():
                return PlainTextResponse(
                    f"hologram.html introuvable dans {_STATIC_DIR}",
                    status_code=404
                )
            return FileResponse(str(html_file), media_type="text/html")

        nicegui_app.add_route("/hologram2", hologram_v2_page, methods=["GET"])
        print("[HologramProjector] Route /hologram2 enregistree")

        # -- WebSocket etat live ----------------------------------------------
        async def _broadcast_worker():
            print("[HologramProjector] Worker broadcast demarre")
            while True:
                await drain_broadcast_queue()
                await asyncio.sleep(0.05)

        @nicegui_app.websocket("/hologram/ws")
        async def hologram_ws(websocket: WebSocket):
            global _worker_started
            # Demarrer le worker au premier client (on est dans le bon event loop)
            if not _worker_started:
                _worker_started = True
                asyncio.create_task(_broadcast_worker())
                print("[HologramProjector] Worker broadcast lance (premier client)")

            await websocket.accept()
            register_client(websocket)
            try:
                # Etat initial au client qui vient de se connecter
                await websocket.send_text(json.dumps({**get_state(), "enabled": is_enabled()}))
                # Maintenir la connexion ouverte
                while True:
                    await websocket.receive_text()
            except WebSocketDisconnect:
                pass
            except Exception:
                pass
            finally:
                unregister_client(websocket)

        print("[HologramProjector] Route /hologram enregistree")
        print("[HologramProjector] WebSocket /hologram/ws enregistre")
        return True

    except Exception as e:
        print(f"[HologramProjector] Erreur enregistrement routes : {e}")
        return False