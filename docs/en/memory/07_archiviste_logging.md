# Archivist Logs

**Verified sources**: `archiviste_logger.py`, `data/archiviste_tokens_debug.jsonl`

> French version: [../../fr/memory/07_archiviste_logging.md](../../fr/memory/07_archiviste_logging.md)

---

## Objective

The Archivist operates behind the scenes on every request. Without monitoring, it is impossible to know how many tokens it consumes, which operations invoke it most, and whether its activity stays within acceptable limits. `ArchivisteLogger` addresses this need.

---

## Token estimation

The Archivist Logger does not have access to the real token counter from APIs (which would require an additional call). It uses an approximation: 1 token ≈ 4 characters. This is a conservative estimate sufficient to detect consumption drift.

---

## Dual persistence

Each Archivist call is recorded in two places:

**In-session memory**: the `calls` list in the instance, enabling instant aggregate calculations.

**On disk in JSONL**: `data/archiviste_tokens_debug.jsonl`, in append mode. Each line is a standalone JSON object with the timestamp, call source, estimated tokens, and metadata. This format allows post-session analysis with external tools.

---

## Tracked sources

Each call is labeled with its source:

| Source | Operation |
|---|---|
| `semantic_analysis` | User intent analysis |
| `memory_synthesis` | Memory context synthesis |
| `memory_enrichment` | Memory enrichment when adding |
| `ego_analysis` | Identity trait analysis |
| `introspection` | Cognitive Mirror sessions |

---

## Session report

`get_summary()` aggregates statistics by source: call count, input tokens, output tokens, input/output ratio. The 5 most consuming sources are isolated for quick identification of hotspots.

`save_report()` saves this report to `data/archiviste_monitoring.json`.
