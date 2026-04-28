# Global Stop Signal

**Verified source**: `stop_signal.py`

> French version: [../../fr/core/03_stop_signal.md](../../fr/core/03_stop_signal.md)

---

## What it's for

Some operations in OGMA take time: generating a response token by token, analyzing memories, running the Archivist. If the user clicks "Stop" while one of these operations is running, there needs to be a clean way to interrupt it — without killing the process, without leaving inconsistent state.

`stop_signal.py` provides this mechanism: a simple global flag (`_stop_requested`) that any part of the code can raise or check.

---

## How it works

The principle is intentionally simple. There are three possible actions:

- **Raise the signal**: `request_stop()` sets the flag to `True`. This is what the stop button in the interface calls.
- **Reset**: `reset_stop()` sets the flag back to `False`. This is called at the start of a new operation, to ensure that a previous stop does not block the next one.
- **Check and interrupt**: `check_stop_and_raise()` raises a `StopAsyncIteration` exception if the signal is active. Streaming generators call this function at regular intervals — as soon as the signal is raised, generation stops cleanly.

---

## Limitations

This module does not know *who* requested the stop, or *which* operation is running. It is a binary global signal. If two long operations are running in parallel (rare but possible), raising the signal interrupts both.

The module also does not handle threads: if a blocking operation is running in a separate Python thread (e.g. loading a GGUF model), the signal does not reach it directly.
