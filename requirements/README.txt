OGMA - Guide des dépendances
=============================

Convention Python : requirements.txt à la racine est LE fichier standard.
Il documente l'état réel d'OGMA (CPU, sans audio avancé).
Les variantes sont dans ce dossier requirements/.


FICHIER RACINE
-------------------------------------

requirements.txt  (à la racine du projet)
  → Installation standard, identique à l'environnement OGMA actuel
  → CPU uniquement, TTS de base (Fish Audio, Edge-TTS, pyttsx3)
  → Inclut Whisper local (torch CPU) mais pas librosa/VAD
  → Commande : pip install -r requirements.txt


VARIANTES (du plus léger au plus complet)
-------------------------------------

requirements-minimal.txt
  → Sans Whisper local, sans torch, sans perception visuelle
  → Pour tester rapidement ou sur machine très légère
  → Fonctionne uniquement avec TTS cloud (clé API requise)
  → Commande : pip install -r requirements/requirements-minimal.txt

requirements-full-nvidia.txt            ← RECOMMANDÉ si GPU NVIDIA
  → Standard + accélération GPU CUDA (remplace torch CPU → GPU)
  → Débloque llama-cpp et Whisper sur GPU
  → Prérequis : CUDA 12.8, drivers NVIDIA 581+
  → Commande : pip install -r requirements/requirements-full-nvidia.txt

requirements-full-nvidia-audio.txt      ← TOUT INCLUS
  → Standard + GPU CUDA + audio avancé (librosa, soundfile, VAD)
  → Pour analyse audio poussée, détection d'activité vocale (VAD)
  → Prérequis : CUDA 12.8, drivers NVIDIA 581+
  → Commande : pip install -r requirements/requirements-full-nvidia-audio.txt


BLOCS SUPPLÉMENTAIRES STANDALONE
-------------------------------------
Ces fichiers peuvent être installés seuls en complément de requirements.txt :

requirements-nvidia.txt
  → Uniquement la surcharge GPU (torch CUDA + llama-cpp GPU)
  → À utiliser si requirements.txt est déjà installé
  → Commande : pip install -r requirements/requirements-nvidia.txt

requirements-audio.txt
  → Uniquement l'audio avancé (librosa, soundfile, webrtcvad + TTS cloud)
  → À utiliser si requirements.txt est déjà installé
  → Commande : pip install -r requirements/requirements-audio.txt


TABLEAU RÉCAPITULATIF
-------------------------------------

                           racine   minimal  standard  full-nvidia  full-nvidia-audio
  NiceGUI, APIs IA           ✅        ✅        ✅         ✅              ✅
  FAISS, SQLite, mémoire     ✅        ✅        ✅         ✅              ✅
  Whisper local (torch CPU)  ✅        ❌        ✅         ✅              ✅
  TTS de base                ✅        ✅        ✅         ✅              ✅
  OpenCV, perception         ✅        ❌        ✅         ✅              ✅
  GPU CUDA (torch+llama)     ❌        ❌        ❌         ✅              ✅
  Audio avancé (VAD, etc.)   ❌        ❌        ❌         ❌              ✅


NOTES
-------------------------------------
- mistralai>=1.0.0 requis (rupture d'API entre 0.x et 1.x)
- nicegui>=2.0.0 requis (OGMA utilise les API NiceGUI v2)
- gradio n'est PAS requis par OGMA
- mediapipe n'est PAS requis (aucune extension active ne l'utilise)
