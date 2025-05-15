# 2. Structure du Code du Backend The Open Music Box

## 2.1. Organisation des Dossiers et Fichiers Principaux

La structure du code du backend est organisée de manière modulaire pour séparer les différentes préoccupations de l'application. Le répertoire principal du backend est `back/`.

```
back/
├── app/                                # Répertoire principal de l'application FastAPI
│   ├── .env                            # Fichier de configuration des variables d'environnement (non versionné)
│   ├── main.py                         # Point d'entrée de l'application FastAPI & Socket.IO, gestion du cycle de vie
│   ├── requirements_base.txt           # Dépendances Python de base
│   ├── requirements_dev.txt            # Dépendances pour le développement
│   ├── requirements_prod.txt           # Dépendances pour la production
│   ├── database/                       # Contient la base de données SQLite (ex: app.db)
│   ├── logs/                           # Fichiers de log de l'application
│   ├── static/                         # Fichiers statiques (si servis par FastAPI)
│   ├── uploads/                        # Dossier où les playlists (dossiers de fichiers audio) sont uploadées/stockées
│   └── src/                            # Code source principal de l'application
│       ├── __init__.py
│       ├── config/                     # Gestion de la configuration (factory, classes de config)
│       │   ├── __init__.py
│       │   ├── config_factory.py
│       │   ├── config_interface.py
│       │   ├── standard_config.py      # Configuration pour la production
│       │   ├── dev_config.py           # Configuration pour le développement (mocks)
│       │   ├── test_config.py          # Configuration pour les tests
│       │   └── nfc_config.py           # Configuration spécifique aux paramètres NFC
│       ├── core/                       # Composants centraux de l'application
│       │   ├── __init__.py
│       │   ├── application.py          # Classe Application principale, coordination
│       │   ├── container_async.py      # Conteneur d'injection de dépendances asynchrone
│       │   └── playlist_controller.py  # Logique de contrôle des playlists et interaction NFC/Audio
│       ├── data/                       # Accès aux données
│       │   ├── __init__.py
│       │   └── playlist_repository.py  # Opérations CRUD pour les playlists (SQLite)
│       ├── helpers/                    # Utilitaires et décorateurs
│       │   ├── __init__.py
│       │   ├── decorators.py
│       │   ├── error_handler.py
│       │   └── exceptions.py
│       ├── model/                      # Modèles de données (Pydantic ou dataclasses)
│       │   ├── __init__.py
│       │   ├── playlist.py
│       │   └── track.py
│       ├── module/                     # Modules d'interaction matérielle et leurs abstractions
│       │   ├── __init__.py
│       │   ├── audio_player/           # Gestion de la lecture audio
│       │   │   ├── audio_player.py     # Wrapper principal (AudioPlayer)
│       │   │   ├── audio_hardware.py   # Protocole pour les implémentations matérielles
│       │   │   ├── audio_factory.py    # Factory pour créer AudioPlayer (mock ou réel)
│       │   │   ├── base_audio_player.py # Classe de base avec logique commune
│       │   │   ├── audio_wm8960.py     # Implémentation pour WM8960 (utilise PygameAudioBackend)
│       │   │   ├── audio_mock.py       # Implémentation simulée
│       │   │   └── pygame_audio_backend.py # Encapsulation de Pygame
│       │   ├── controles/              # Gestion des contrôles physiques (GPIO)
│       │   │   ├── controles_manager.py # Gestionnaire central des contrôles
│       │   │   ├── controles_hardware.py # Protocole pour les implémentations matérielles
│       │   │   ├── controles_factory.py # Factory pour ControlesHardware (mock ou réel)
│       │   │   ├── controles_gpio.py   # Implémentation GPIO (utilise gpiozero)
│       │   │   ├── controles_mock.py   # Implémentation simulée
│       │   │   ├── events/             # Définition des événements de contrôle
│       │   │   │   └── controles_events.py
│       │   │   └── input_devices/      # Classes pour les types de dispositifs (bouton, encodeur)
│       │   │       ├── button.py
│       │   │       └── rotary_encoder.py
│       │   └── nfc/                    # Gestion de la lecture NFC
│       │       ├── nfc_handler.py      # Wrapper principal (NFCHandler)
│       │       ├── nfc_hardware.py     # Protocole pour les implémentations matérielles
│       │       ├── nfc_factory.py      # Factory pour NFCHandler (mock ou réel)
│       │       ├── nfc_pn532_i2c.py    # Implémentation pour PN532 I2C
│       │       ├── nfc_mock.py         # Implémentation simulée
│       │       └── tag_detection_manager.py # Logique de détection/debounce des tags
│       ├── monitoring/                 # Logging et monitoring
│       │   ├── __init__.py
│       │   ├── improved_logger.py      # Classe de logging améliorée
│       │   └── logging/                # Configuration spécifique du logging (formatters, etc.)
│       ├── routes/                     # Définition des routes API et WebSocket
│       │   ├── __init__.py
│       │   ├── api_routes.py           # Centralisation de l'initialisation des routes
│       │   ├── nfc_routes.py
│       │   ├── playlist_routes.py
│       │   ├── system_routes.py
│       │   ├── web_routes.py           # Routes pour servir des fichiers statiques/HTML
│       │   ├── websocket_handlers_async.py # Gestionnaires d'événements Socket.IO
│       │   └── youtube_routes.py
│       └── services/                   # Logique métier de l'application
│           ├── __init__.py
│           ├── nfc_service.py
│           ├── notification_service.py # Contient PlaybackSubject pour les événements de lecture
│           ├── playlist_service.py
│           ├── upload_service.py       # Service pour gérer les uploads et métadonnées
│           └── youtube/                # Service pour l'intégration YouTube
│               └── service.py
├── start_app.py                        # Script pour démarrer l'application en mode production
├── start_dev.py                        # Script pour démarrer l'application en mode développement
├── start_test.py                       # Script pour lancer les tests (pytest)
├── pytest.ini                          # Configuration de Pytest
├── .gitignore
├── app.service                         # Fichier de service systemd (exemple pour déploiement)
└── tests/                              # Répertoire des tests unitaires et d'intégration
    └── ...
```

## 2.2. Rôles des Modules Principaux

*   **`app/main.py`**:
    *   Point d'entrée principal de l'application ASGI.
    *   Initialise l'application FastAPI (`app`).
    *   Initialise le serveur Socket.IO asynchrone (`sio`).
    *   Combine FastAPI et Socket.IO en une seule application ASGI (`app_sio`).
    *   Gère le cycle de vie de l'application (démarrage/arrêt des ressources) via le décorateur `@asynccontextmanager lifespan`. C'est ici que le `ContainerAsync` est initialisé, l'instance `Application` est créée, les routes sont mises en place, et les abonnements aux événements NFC sont configurés.

*   **`app/src/config/`**:
    *   `config_factory.py`: Fournit la configuration appropriée (`StandardConfig`, `DevConfig`, `TestConfig`) en fonction de l'environnement.
    *   `standard_config.py`, `dev_config.py`, `test_config.py`: Implémentations de `IConfig` chargeant les paramètres depuis les variables d'environnement (`.env`) ou des valeurs par défaut. `DevConfig` surcharge typiquement `use_mock_hardware` à `True`.
    *   `nfc_config.py`: Dataclass ou configuration spécifique pour les paramètres du module NFC (cooldown, timeouts).

*   **`app/src/core/`**:
    *   `application.py` (`Application`): Classe centrale orchestrant l'initialisation et la liaison des principaux services (NFC, Audio, PlaylistService, PlaylistController). Gère la logique de synchronisation des playlists au démarrage et l'abonnement aux événements NFC bruts pour les router vers le `PlaylistController`.
    *   `container_async.py` (`ContainerAsync`): Conteneur d'injection de dépendances. Il est responsable de la création et de la fourniture des instances des services majeurs (config, audio, nfc, playlist_service, playback_subject). Gère l'initialisation asynchrone des ressources comme le matériel NFC.
    *   `playlist_controller.py` (`PlaylistController`): Cerveau de l'interaction entre NFC et lecture. Reçoit les événements NFC (filtrés par `NFCService`), récupère les playlists via `PlaylistService`, et commande l'`AudioPlayer`. Gère l'état de lecture automatique/manuel et la pause automatique.

*   **`app/src/data/`**:
    *   `playlist_repository.py` (`PlaylistRepository`): Seule classe responsable des interactions directes avec la base de données SQLite. Gère les opérations CRUD pour les playlists et les pistes, ainsi que les associations NFC.

*   **`app/src/services/`**:
    *   `playlist_service.py` (`PlaylistService`): Contient la logique métier pour les playlists : création, suppression, récupération, synchronisation avec le système de fichiers, association/dissociation NFC. Utilise `PlaylistRepository`.
    *   `nfc_service.py` (`NFCService`): Orchestre les opérations NFC. Gère les modes (association vs lecture), communique l'état au frontend via Socket.IO, et filtre/transmet les événements de tag au `PlaylistController` via un `Subject` RxPy (`playback_subject`).
    *   `notification_service.py` (`PlaybackSubject`): Un `Subject` RxPy central pour diffuser les événements liés à la lecture audio (statut, progression). L'`AudioPlayerWM8960` (via `BaseAudioPlayer`) publie sur ce subject, et d'autres parties (ex: `WebSocketHandlersAsync`) s'y abonnent.
    *   `upload_service.py` (`UploadService`): Aide à l'extraction de métadonnées des fichiers audio.
    *   `youtube/service.py` (`YouTubeService`): Gère la logique de téléchargement depuis YouTube.

*   **`app/src/module/` (NFC, Audio, Contrôles)**:
    *   Chaque sous-module (NFC, audio_player, controles) suit un schéma similaire :
        *   Un **protocole matériel** (ex: `NFCHardware`) définissant l'interface.
        *   Une **implémentation réelle** pour le matériel (ex: `PN532I2CNFC`, `AudioPlayerWM8960`, `ControlesGPIO`).
        *   Une **implémentation simulée** (mock) (ex: `MockNFC`, `MockAudioPlayer`, `ControlesMock`).
        *   Une **factory** (ex: `get_nfc_handler`) qui retourne un wrapper (ex: `NFCHandler`) initialisé avec l'implémentation réelle ou simulée en fonction de la configuration.
        *   Des **wrappers/managers** (ex: `NFCHandler`, `AudioPlayer`, `ControlesManager`) qui fournissent une interface stable et de plus haut niveau à la logique applicative, en utilisant l'implémentation matérielle fournie par la factory.
    *   `nfc/tag_detection_manager.py`: Logique spécifique pour traiter les lectures brutes de tags NFC et émettre des événements de détection/absence plus fiables (debounce, cooldown).
    *   `audio_player/pygame_audio_backend.py`: Encapsule les interactions directes avec Pygame pour la lecture audio, utilisé par `AudioPlayerWM8960`.
    *   `controles/input_devices/`: Classes `Button` et `RotaryEncoder` qui représentent des dispositifs spécifiques et utilisent l'implémentation `ControlesHardware` pour interagir avec les pins et émettre des événements.

*   **`app/src/routes/`**:
    *   `api_routes.py` (`APIRoutes`): Classe qui instancie et enregistre tous les routeurs FastAPI (pour les playlists, NFC, système, etc.) et les handlers WebSocket.
    *   Les fichiers individuels (ex: `playlist_routes.py`) définissent les endpoints spécifiques pour chaque domaine fonctionnel, utilisant les services correspondants et le `PlaylistController`.
    *   `websocket_handlers_async.py`: Définit les gestionnaires pour les événements Socket.IO, permettant la communication bidirectionnelle avec le frontend.

*   **`app/src/model/`**:
    *   `playlist.py`, `track.py`: Définissent les structures de données (probablement des dataclasses ou des modèles Pydantic) pour les playlists et les pistes, utilisées à travers l'application.

## 2.3. Points d'Entrée de l'Application

1.  **Scripts de Démarrage**:
    *   `start_app.py`: Point d'entrée pour lancer l'application en mode **production**. Il configure l'application pour utiliser `StandardConfig` (matériel réel) et démarre le serveur Uvicorn avec `app.main:app_sio`.
    *   `start_dev.py`: Point d'entrée pour lancer l'application en mode **développement**. Il configure l'application pour utiliser `DevConfig` (matériel simulé, rechargement automatique) et démarre le serveur Uvicorn.

2.  **Application ASGI**:
    *   `app.main.app_sio`: L'objet application ASGI lui-même, qui est passé à Uvicorn. Il est créé dans `app/main.py` en combinant l'instance FastAPI et l'instance Socket.IO.

3.  **Gestionnaire de Cycle de Vie (`lifespan` dans `app/main.py`)**:
    *   Le contexte `lifespan` dans `app/main.py` est un point d'entrée crucial pour l'initialisation et le nettoyage des ressources de l'application au démarrage et à l'arrêt du serveur. C'est ici que le conteneur DI, l'instance `Application`, les routes, et les abonnements aux événements sont mis en place.

4.  **Tests**:
    *   `start_test.py` (et `pytest.ini`): Point d'entrée pour l'exécution des tests automatisés, qui utiliseront typiquement `TestConfig` et les implémentations simulées.
