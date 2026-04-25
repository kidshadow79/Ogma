"""
Hologram Projector — Audio Analyzer
=====================================

Extrait l'enveloppe RMS d'un fichier MP3 (généré par Edge TTS) pour
animer le blob en synchronisation réelle avec la voix d'OGMA.

Approches (par ordre de préférence) :
  1. ffmpeg subprocess -> raw PCM 16-bit mono -> RMS par tranches
  2. pydub (si installé et ffmpeg disponible)
  3. [] vide => fallback animation synthétique côté HTML

Aucune dépendance requise au-delà de ffmpeg (souvent déjà présent).
"""

import math
import struct
import subprocess
import sys
from typing import List


# ─── Constantes ─────────────────────────────────────────────────────────────

_SAMPLE_RATE = 16000   # Hz — bonne résolution temporelle, peu de données
_CHANNELS    = 1       # mono
_BIT_DEPTH   = 16      # s16le


# ─── API publique ────────────────────────────────────────────────────────────

def extract_rms_envelope(
    audio_path: str,
    interval_ms: int = 50,
) -> List[float]:
    """
    Retourne une liste de valeurs RMS normalisées [0.0-1.0] espacées de
    interval_ms millisecondes.

    Utilise ffmpeg en priorité (subprocess), puis pydub en fallback.
    Retourne [] si aucune méthode ne fonctionne.
    """
    try:
        return _analyze_ffmpeg(audio_path, interval_ms)
    except Exception as e:
        print(f"[AudioAnalyzer] ffmpeg indisponible ({e}), essai pydub...")
    try:
        return _analyze_pydub(audio_path, interval_ms)
    except Exception as e:
        print(f"[AudioAnalyzer] pydub indisponible ({e}), pas d'enveloppe")
    return []


# ─── Implémentation ffmpeg ───────────────────────────────────────────────────

def _analyze_ffmpeg(audio_path: str, interval_ms: int) -> List[float]:
    """Décode en PCM via ffmpeg et calcule le RMS par tranche."""
    cmd = [
        "ffmpeg", "-y",
        "-i", audio_path,
        "-f", "s16le",        # raw PCM signed 16-bit little-endian
        "-ac", str(_CHANNELS),
        "-ar", str(_SAMPLE_RATE),
        "-loglevel", "quiet",
        "pipe:1",             # sortie sur stdout
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=10)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg exit {result.returncode}: {result.stderr[:200]}")

    raw = result.stdout
    if not raw:
        raise RuntimeError("ffmpeg a retourné 0 octets")

    return _rms_from_pcm(raw, interval_ms)


# ─── Implémentation pydub ────────────────────────────────────────────────────

def _analyze_pydub(audio_path: str, interval_ms: int) -> List[float]:
    """Décode via pydub (nécessite ffmpeg installé)."""
    from pydub import AudioSegment  # import lazy — pas d'erreur au démarrage

    audio = AudioSegment.from_file(audio_path)
    audio = audio.set_channels(1).set_frame_rate(_SAMPLE_RATE).set_sample_width(2)
    raw   = audio.raw_data
    return _rms_from_pcm(raw, interval_ms)


# ─── Calcul RMS ─────────────────────────────────────────────────────────────

def _rms_from_pcm(raw: bytes, interval_ms: int) -> List[float]:
    """
    Calcule le RMS par tranches de interval_ms ms sur du PCM s16le mono.
    Retourne des valeurs normalisées [0.0 - 1.0].
    """
    samples_per_chunk = int(_SAMPLE_RATE * interval_ms / 1000)
    n_samples         = len(raw) // 2  # 2 octets par sample s16le

    if n_samples == 0:
        return []

    samples = struct.unpack(f"<{n_samples}h", raw[: n_samples * 2])

    rms_values: List[float] = []
    for i in range(0, len(samples), samples_per_chunk):
        chunk = samples[i : i + samples_per_chunk]
        if not chunk:
            continue
        rms = math.sqrt(sum(s * s for s in chunk) / len(chunk))
        rms_values.append(rms)

    if not rms_values:
        return []

    # Normalisation : peak = 1.0
    peak = max(rms_values) or 1.0
    normalized = [min(1.0, v / peak) for v in rms_values]

    print(f"[AudioAnalyzer] Enveloppe : {len(normalized)} frames x {interval_ms}ms "
          f"= {len(normalized) * interval_ms / 1000:.1f}s")
    return normalized
