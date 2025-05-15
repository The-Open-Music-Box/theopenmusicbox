# 1. Architecture Technique du Backend The Open Music Box

## 1.1. Schéma de l'Architecture Globale

Le schéma détaillé de l'architecture globale est disponible dans le fichier [06_Architecture_Diagram.md](./06_Architecture_Diagram.md).

## 1.2. Description de l'Architecture Globale

Le backend de The Open Music Box est construit autour d'une architecture modulaire en couches, visant à séparer les préoccupations et à faciliter la maintenance et les tests.

*   **Couche Web & API (FastAPI & Uvicorn)**:
    *   Gérée par `FastAPI` et servie par `Uvicorn`.
    *   `app.main:app_sio` est le point d'entrée ASGI, combinant l'application FastAPI et le serveur `Socket.IO`.
    *   `APIRoutes` centralise l'initialisation de tous les groupes de routes (Playlists, NFC, Système, YouTube, Web statique).
    *   `WebSocketHandlersAsync` gère la logique des événements Socket.IO, souvent en lien avec `NFCService` et `PlaylistController` pour les mises à jour d'état.

*   **Logique Applicative & Contrôle (Core)**:
    *   `Application` (`app/src/core/application.py`): Classe centrale qui initialise et coordonne les composants majeurs comme les services NFC, audio, et le `PlaylistController`. Gère le cycle de vie via le `lifespan` de FastAPI.
    *   `ContainerAsync` (`app/src/core/container_async.py`): Conteneur d'injection de dépendances (DI) asynchrone. Il instancie et fournit les services essentiels (configuration, services NFC/Audio/Playlist, `PlaybackSubject`).
    *   `PlaylistController` (`app/src/core/playlist_controller.py`): Orchestre la logique principale de l'application : réagit aux événements NFC (via `NFCService`), interagit avec `PlaylistService` pour obtenir les données des playlists, et commande l'`AudioPlayer` pour la lecture. Gère également la logique de pause automatique et la priorité des contrôles manuels.
    *   `Configuration` (`app/src/config/`): Gérée par `ConfigFactory` et des classes spécifiques (`StandardConfig`, `DevConfig`, `TestConfig`) qui lisent les variables d'environnement (fichier `.env`) et fournissent les paramètres à l'application. `config_singleton` est l'instance active.

*   **Couche Services (Logique Métier)**:
    *   `PlaylistService`: Contient la logique métier pour la gestion des playlists (CRUD, synchronisation avec le système de fichiers, association NFC).
    *   `NFCService`: Gère la logique d'interaction NFC, y compris le mode d'association de tags et la communication des états NFC via Socket.IO. S'abonne aux événements du `NFCHandler`.
    *   `NotificationService` (principalement `PlaybackSubject`): Un système basé sur RxPy `Subject` pour diffuser les événements de lecture (début/fin de piste, progression, pause, etc.) auxquels d'autres composants (comme `AudioPlayerWM8960` ou `Socket.IO handlers`) peuvent s'abonner.
    *   `UploadService`: Utilisé par `PlaylistService` pour extraire les métadonnées des fichiers audio lors de la création/synchronisation de playlists.
    *   `YouTubeService`: Gère le téléchargement de contenu YouTube et sa conversion en playlists.

*   **Couche d'Accès aux Données**:
    *   `PlaylistRepository`: Responsable des opérations CRUD directes avec la base de données SQLite (`app.db`). Isole la logique de la base de données du reste de l'application.

*   **Couche d'Abstraction Matérielle**:
    *   Cette couche est cruciale pour permettre à l'application de fonctionner avec du matériel réel (sur Raspberry Pi) ou des simulations (mocks) pour le développement/test.
    *   **Module NFC**:
        *   `nfc_factory.py`: Fournit une instance de `NFCHandler` avec l'implémentation matérielle appropriée (`PN532I2CNFC` ou `MockNFC`).
        *   `NFCHandler`: Wrapper générique autour de l'implémentation matérielle.
        *   `TagDetectionManager`: Gère la logique de détection de tag (debounce, cooldown, détection de retrait) et émet des événements via un RxPy `Subject`.
        *   `PN532I2CNFC`: Implémentation pour le lecteur NFC PN532 via I2C.
        *   `MockNFC`: Simulation du lecteur NFC.
    *   **Module Audio**:
        *   `audio_factory.py`: Fournit une instance d'`AudioPlayer` avec l'implémentation matérielle appropriée (`AudioPlayerWM8960` ou `MockAudioPlayer`).
        *   `AudioPlayer`: Wrapper générique.
        *   `BaseAudioPlayer`: Classe de base contenant la logique commune de gestion de playlist et de notification de progression (utilisée par `MockAudioPlayer` et `AudioPlayerWM8960`).
        *   `AudioPlayerWM8960`: Implémentation pour la carte son WM8960, utilisant `PygameAudioBackend`.
        *   `PygameAudioBackend`: Encapsule les appels directs à la bibliothèque Pygame pour la lecture audio.
        *   `MockAudioPlayer`: Simulation de la lecture audio.
    *   **Module Contrôles GPIO**:
        *   `controles_factory.py`: Fournit une instance de `ControlesHardware` (`ControlesGPIO` ou `ControlesMock`).
        *   `ControlesManager`: Gère l'initialisation des dispositifs de contrôle (boutons, encodeurs rotatifs) et centralise leurs événements via un RxPy `Subject`.
        *   `Button`, `RotaryEncoder`: Classes représentant les dispositifs individuels, qui utilisent l'implémentation `ControlesHardware`.
        *   `ControlesGPIO`: Implémentation pour les contrôles GPIO utilisant `gpiozero`.
        *   `ControlesMock`: Simulation des contrôles GPIO.

*   **Systèmes Externes/OS**:
    *   **Système de Fichiers**: Utilisé pour stocker les fichiers audio uploadés (`uploads/`).
    *   **Matériel OS**: Accès bas niveau aux bus I2C, aux pins GPIO, et au système audio ALSA (via Pygame ou directement en fallback).
    *   **Variables d'Environnement**: Fichier `.env` pour la configuration.

## 1.3. Technologies Utilisées

*   **Langage**: Python 3.x
*   **Framework Web**: FastAPI
*   **Serveur ASGI**: Uvicorn
*   **Communication Temps Réel**: python-socketio (AsyncServer avec intégration ASGI)
*   **Programmation Réactive**: RxPy (pour la gestion des événements NFC et des contrôles physiques)
*   **Audio**:
    *   Pygame (bibliothèque principale pour la lecture audio via `PygameAudioBackend`)
    *   Mutagen (pour lire les métadonnées des fichiers audio, notamment la durée)
    *   ALSA (Advanced Linux Sound Architecture) : utilisé implicitement par Pygame sur Raspberry Pi, et directement via `aplay`/`mpg123` comme fallback.
*   **NFC**:
    *   `adafruit-circuitpython-pn532` (pour l'interaction avec le lecteur PN532 via I2C)
    *   `pyserial` ou dépendances similaires pour la communication I2C via Blinka.
*   **Contrôles GPIO**:
    *   `gpiozero` (avec le backend `lgpio` pour l'interaction avec les GPIO du Raspberry Pi)
*   **Base de Données**: SQLite (via le module `sqlite3` de Python)
*   **Gestion des Dépendances**: Fichiers `requirements_*.txt` (base, dev, prod).
*   **Configuration**: python-dotenv (pour charger les variables d'environnement depuis `.env`)
*   **Tests**: Pytest (structure de tests présente dans `tests/`)
*   **Logging**: Module `logging` standard de Python, amélioré par `ImprovedLogger`.

## 1.4. Échanges entre Modules ou Services

*   **Frontend <=> Backend (API)**: Le frontend communique avec le backend via des requêtes HTTP à l'API REST définie par FastAPI pour des actions telles que la gestion des playlists, l'association NFC, le contrôle de la lecture.
*   **Frontend <=> Backend (WebSocket)**: Le frontend maintient une connexion Socket.IO avec le backend pour recevoir des mises à jour d'état en temps réel (statut NFC, lecture en cours, progression de la piste, etc.). Ces messages sont émis par `NFCService`, `NotificationService` (via `PlaylistController` et `AudioPlayer`).
*   **NFC Hardware -> `TagDetectionManager` -> `NFCHandler` -> `NFCService`**:
    *   Le matériel NFC (`PN532I2CNFC`) lit les tags.
    *   `TagDetectionManager` filtre et traite ces lectures brutes pour émettre des événements de détection ou d'absence de tag via un `Subject` RxPy.
    *   `NFCHandler` expose ce `Subject`.
    *   `NFCService` s'abonne à ce `Subject`. Si le tag n'est pas destiné à une association, `NFCService` émet l'événement sur son propre `playback_subject`.
*   **`NFCService` -> `PlaylistController`**:
    *   `PlaylistController` s'abonne au `playback_subject` de `NFCService` pour être notifié des scans de tags destinés à la lecture.
*   **`PlaylistController` -> `PlaylistService` & `AudioPlayer`**:
    *   Sur détection d'un tag pertinent, `PlaylistController` utilise `PlaylistService` pour récupérer les informations de la playlist.
    *   Puis, il commande à `AudioPlayer` de jouer cette playlist (via `PlaylistService.play_playlist_with_validation`).
*   **Contrôles Physiques -> `ControlesManager` -> `PlaylistController` (ou autre handler)**:
    *   Les classes `Button` et `RotaryEncoder` (utilisant `ControlesGPIO` ou `ControlesMock`) détectent les actions physiques.
    *   Elles émettent des `ControlesEvent` sur le `_event_subject` du `ControlesManager`.
    *   Le `PlaylistController` (ou une logique similaire dans `app.main.py` lors de l'initialisation des contrôles physiques) s'abonne à cet `event_observable` pour réagir aux actions (ex: changer de piste, ajuster le volume).
*   **`AudioPlayer` (`AudioPlayerWM8960`) -> `NotificationService` (`PlaybackSubject`)**:
    *   L'implémentation réelle de l'audio (`AudioPlayerWM8960`, via `BaseAudioPlayer`) utilise `PlaybackSubject` pour émettre des événements sur l'état de la lecture (piste en cours, progression, pause, arrêt, fin de piste).
    *   Ces événements peuvent être consommés par `PlaylistController` (pour la logique interne) et par les handlers WebSocket pour informer le frontend.
*   **Services -> Repository**: Les services (`PlaylistService`) utilisent le `PlaylistRepository` pour toutes les interactions avec la base de données SQLite.
*   **`Application` -> Services & Factories**: La classe `Application` et le `ContainerAsync` initialisent et connectent les différents services et utilisent les factories pour obtenir les implémentations matérielles.
