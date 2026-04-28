# Display and Formatting

**Verified source**: `ogma_displays.py`

> French version: [../../fr/ui/04_displays.md](../../fr/ui/04_displays.md)

---

## Role

`ogma_displays.py` groups display and formatting functions for the interface. It contains utilities that transform raw data into visual representations: formatted dates, readable file sizes, formatted text.

---

## Emotional gauges

The interface includes a visual gauge system (LEDs) reflecting the main AI's emotional state detected in real time. These LEDs correspond to emotional dimensions:

| Dimension | Description |
|---|---|
| `autocensure` | Tendency to self-censor |
| `saturation` | Contextual saturation level |
| `stimulation` | Intellectual stimulation level |
| `affinity` | Conversational affinity |
| `disorientation` | Contextual disorientation |
| `freedom` | Sense of expressive freedom |
| `alignment` | Alignment with the user |

LEDs are DOM elements with identifiers like `affinity-led-0` to `affinity-led-5`. They are updated via `ui.run_javascript()` which directly manipulates the DOM for style changes.

---

## Formatting helpers

Utility functions standardize the display of:
- Dates and timestamps (readable format)
- File sizes (bytes → KB/MB)
- Truncated text with ellipses

---

## Message streaming

AI message display during streaming uses a `ui.markdown` widget whose content is replaced on each new token. An animated JavaScript spinner is injected into the DOM via `ui.run_javascript()` to signal ongoing generation. This spinner targets the last `.ogma-streaming-target` element in the DOM to avoid affecting older messages.
