# Depth Analysis and Contours

**Verified sources**: `extensions/perception_agent.py` (imports and usage), extension structure (`depth_manager.py`, `contour_analyzer.py` referenced)

> French version: [../../fr/perception/03_depth_and_contours.md](../../fr/perception/03_depth_and_contours.md)

---

## DepthManager

DepthManager estimates the depth of the scene captured by the webcam. It produces a depth map that allows the main AI to understand the spatial arrangement of elements: what is close, what is far.

This module is optional: the perception agent checks its availability at startup and works without it if dependencies are not installed.

---

## ContourAnalyzer

ContourAnalyzer detects shapes and contours in webcam frames. It identifies distinct objects in the scene and can provide a structured description of the visual elements present.

Like DepthManager, it is optional and checked separately at startup.

---

## Integration in the agent

The perception agent (`perception_agent.py`) uses these two modules if available to enrich the events it places in `event_queue`. Events can thus carry depth and contour information in addition to basic detection (movement, presence).

These enrichments are transmitted to the main AI via the visual context injected into the prompt (see [docs/en/pipeline/02_context_injection.md](../pipeline/02_context_injection.md)).

---

Note: These modules were not inspected directly. Behaviors described from imports and usages in `perception_agent.py`. [NOT VERIFIED in detail — internal structure of modules not inspected]
