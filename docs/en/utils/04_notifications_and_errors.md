# Notifications, NiceGUI Errors, and Client Guard

**Verified sources**: `notification_killer.py`, `nicegui_error_handler.py`, `nicegui_client_guard.py`

> French version: [../../fr/utils/04_notifications_and_errors.md](../../fr/utils/04_notifications_and_errors.md)

---

## Background problem

NiceGUI is a reactive web framework: multiple clients can connect simultaneously, and a client can disconnect mid-operation (tab close, network loss). Without protection, these disconnections cause `KeyError` on `Client.instances` that bubble up as stack traces.

Additionally, notifications can remain visible in the interface after they have expired ("ghost notifications").

---

## `nicegui_client_guard.py` — Protection decorator

Provides the `@safe_client_operation` decorator. Before executing a function, it verifies:
1. That `Client.current` exists
2. That the client identifier is still in `Client.instances`

If either condition fails, the function is silently ignored (returns `None`). `KeyError` and `AttributeError` on `Client.current` are caught and logged at debug level, never as visible errors.

---

## `nicegui_error_handler.py` — Timeout and activity tracking

Two mechanisms:

**Timeout patch**: NiceGUI's internal timeout for timers is increased from 60 seconds to **30 minutes** (`TIMER_TIMEOUT_OVERRIDE = 1800.0`). Without this patch, long streaming generations trigger client disconnections.

**Activity tracking**: `track_client_activity(client_id)` is called at each user interaction. `get_client_last_activity()` returns the timestamp. An `ACTIVITY_GRACE_PERIOD` of 10 minutes protects active clients from automatic disconnection even during a long generation.

---

## `notification_killer.py` — Ghost notification cleanup

Some NiceGUI notifications remain visible after processing (ongoing generation notifications). `force_clear_all_notifications()` uses three brute-force techniques:
1. Bombardment of empty notifications with minimal timeout
2. Replacement notifications for each type (`ongoing`, `positive`, `negative`, `warning`)
3. Quick confirmation notification to clean up

This function is accessible via a button in the OGMA interface.
