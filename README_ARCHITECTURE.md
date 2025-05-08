# Architecture de TheMusicBox - Documentation Technique

## Architecture générale

TheMusicBox est une application audio qui utilise des tags NFC pour déclencher la lecture de playlists. L'architecture est divisée en deux composants principaux :

1. **Backend** (Python/FastAPI) :
   - Gestion des playlists et fichiers audio
   - Détection NFC et contrôle audio
   - API REST et communications Socket.IO

2. **Frontend** (VueJS) :
   - Interface utilisateur pour gérer les playlists
   - Association des tags NFC
   - Visualisation de l'état de lecture

## Composants principaux du backend

### 1. Conteneur d'injection de dépendances (`ContainerAsync`)
- Point central pour l'initialisation et l'accès aux services
- Responsable de la coordination entre les différents modules

### 2. Application Core (`Application`)
- Orchestrateur principal qui initialise les différents services
- Coordonne la synchronisation des playlists
- Configure le `PlaylistController` et les liaisons NFC

### 3. Playlist Controller (`PlaylistController`)
- Manages selection and control of playlists via NFC tags
- Coordinates interactions between NFC service and audio player
- Maintains the current tag and handles playlist transitions
- Uses only the public `is_playing` and `is_paused` properties from the audio player for all playback state decisions

### 4. Audio Player (`AudioPlayerWM8960`)
- Interfaces with audio hardware via pygame
- Manages playback, pause, and track progression
- Maintains playback state and current position
- Exposes public properties `is_playing` and `is_paused` to describe the playback state
- All state checks by controllers and other modules must use these public properties only (no private/protected attribute access)

### 5. Service NFC (`NFCService`)
- Communique avec le matériel NFC via `NFCHandler`
- Détecte les tags NFC et émet des événements
- Gère le mode d'association de tags aux playlists

### 6. Gestionnaire de détection de tags (`TagDetectionManager`)
- Logique de détection des tags et gestion du debounce
- Détermine quand un tag est considéré comme nouveau ou retiré
- Émet des événements pour informer les autres composants

### 7. Service de notification (`PlaybackSubject`)
- Communique l'état de lecture aux clients via Socket.IO
- Gère les événements de progression de piste et de statut

## Flux de travail actuel (workflow)

Le flux principal de l'application fonctionne comme suit :

### 1. Initialisation
- Le système démarre et initialise tous les composants
- Le lecteur audio est préparé, le lecteur NFC est activé
- Les playlists sont synchronisées depuis le dossier d'uploads

### 2. Détection de tag NFC
- Un tag NFC est détecté par le `NFCHandler`
- Le `TagDetectionManager` traite l'événement, applique le debouncing
- Le `NFCService` reçoit l'événement et le transmet au `PlaylistController`

### 3. Contrôle de lecture

Le contrôle de la lecture via les tags NFC repose sur une logique stricte pour garantir une expérience utilisateur fiable et prévisible. Voici le fonctionnement attendu et les cas d'usage principaux :

#### Cas d'usage typiques

- **A. Présentation d'un tag NFC associé à une playlist**
  - Si aucun tag n'était présent, la playlist associée à ce tag est chargée et la lecture démarre depuis le début.
  - Si un autre tag était déjà présent, la nouvelle playlist remplace l'ancienne et la lecture démarre depuis le début de la nouvelle playlist.

- **B. Présentation du même tag NFC alors que la lecture est en pause**
  - Si la lecture était en pause (par exemple après un retrait du tag), présenter à nouveau le même tag reprend la lecture exactement à la position où elle avait été interrompue.

- **C. Présentation d'un tag inconnu (non associé à une playlist)**
  - Aucun changement d'état n'a lieu. La lecture reste en pause ou arrêtée. Aucun son ne doit être joué.

- **D. Retrait du tag NFC**
  - Dès que le tag est retiré, la lecture est automatiquement mise en pause et la position courante est mémorisée.

- **E. Présentation d'un tag différent**
  - Si un tag différent (associé à une autre playlist) est présenté, la nouvelle playlist est chargée et la lecture démarre depuis le début de cette playlist.

#### Description détaillée du workflow

1. **Détection d'un tag NFC**
    - Le `TagDetectionManager` identifie le tag et applique le debouncing pour éviter les faux positifs.
    - Le `NFCService` transmet l'événement au `PlaylistController`.
    - Le `PlaylistController` vérifie si le tag est associé à une playlist :
      - **Si oui** :
        - Si c'est un nouveau tag ou un tag différent, il charge la nouvelle playlist et démarre la lecture depuis le début.
        - Si c'est le même tag que précédemment et que la lecture était en pause, il reprend la lecture à la position mémorisée.
      - **Si non** :
        - Aucun changement, la lecture reste en pause ou arrêtée.

2. **Retrait du tag NFC**
    - Le `TagDetectionManager` détecte l'absence du tag et envoie l'événement d'absence.
    - Le `PlaylistController` met automatiquement la lecture en pause et mémorise la position courante.

3. **Représentation d'un tag**
    - Si le tag présenté est le même que précédemment, la lecture reprend à la position mémorisée.
    - Si c'est un tag différent, le workflow redémarre avec la nouvelle playlist.

4. **Sécurité et robustesse**
    - Un tag inconnu ne doit jamais déclencher de lecture.
    - Seul le tag associé à une playlist peut la reprendre et la démarrer.
    - Les états de lecture, pause, et arrêt sont strictement synchronisés avec la présence ou l'absence du tag NFC.

### 4. Absence de tag
- Quand un tag est retiré, `TagDetectionManager.process_tag_absence` est appelé
- Un événement d'absence est émis vers `NFCService`
- `PlaylistController.handle_tag_absence` est censé mettre en pause la lecture
- `auto_pause_enabled` contrôle si la pause automatique est active

### 5. Reprise de lecture
- Quand un tag réapparaît, le cycle recommence
- La décision de reprise ou nouvelle playlist dépend de la comparaison avec le tag courant

## Technologies et dépendances

### 1. Frameworks Web
- **FastAPI** : Framework web principal asynchrone
- **Socket.IO** (via `socketio.AsyncServer`) : Communication bidirectionnelle en temps réel
- **CORS Middleware** : Gestion des accès cross-origin

### 2. ORM et base de données
- **SQLite** : Stockage des données via un fichier DB local
- **SQLAlchemy** : ORM pour l'accès à la base de données

### 3. Multiprocessing et asynchronicité
- **asyncio** : Programmation asynchrone
- **threading** : Gestion des threads
- **concurrent.futures** : Exécution asynchrone
- **rx.subject** (ReactiveX) : Programmation réactive pour les événements

### 4. Hardware et Audio
- **pygame** : Lecture audio
- Modules personnalisés pour NFC (basés sur PN532 I2C)

### 5. Utilitaires
- **os**, **sys**, **time** : Manipulation système
- **pathlib.Path** : Gestion des chemins de fichiers
- **typing** (`Optional`, `Dict`, `List`, etc.) : Annotations de type
- **uuid** : Génération d'identifiants uniques
- **logging** : Journalisation (amélioré par un module personnalisé)
- **pydub** : Manipulation audio (pour analyses)

## Fichiers de Configuration et Scripts

### 1. Configuration
- **`.env`** : Variables d'environnement pour la configuration de l'application
- **`config.py`** : Singleton qui charge les configurations depuis `.env`

### 2. Scripts de démarrage/développement
- **`synchronise_tmbdev.sh`** : Script de synchronisation du code vers l'environnement de développement
- **`app.service`** : Service systemd pour le démarrage automatique

### 3. Gestion des environnements
- Support pour les modes REAL et MOCK (hardware réel vs. simulé)
- Configuration différenciée pour développement et production

## Architecture du Backend

L'architecture du backend est organisée en plusieurs couches :

### 1. Module Core
- **`application.py`** : Point d'entrée principal qui initialise tous les composants
- **`container_async.py`** : Conteneur d'injection de dépendances
- **`playlist_controller.py`** : Contrôle logique pour la gestion des playlists

### 2. Services
- **`notification_service.py`** : Communication avec les clients via Socket.IO
- **`nfc_service.py`** : Interface avec le matériel NFC
- **`playlist_service.py`** : CRUD et logique métier pour les playlists

### 3. Repositories
- **`playlist_repository.py`** : Accès aux données des playlists
- Abstractions pour la couche de persistance

### 4. Modules matériels
- **`audio_player/`** : Lecteurs audio (avec implémentation principale **`audio_wm8960.py`**)
- **`nfc/`** : Gestionnaires NFC (avec support pour PN532 en I2C)

### 5. Routes API
- **`playlist_routes.py`** : Endpoints pour la gestion des playlists
- **`nfc_routes.py`** : Endpoints pour l'association NFC
- **`websocket_handlers_async.py`** : Handlers Socket.IO

### 6. Modèles
- **`playlist.py`**, **`track.py`** : Modèles de données
- Représentations ORM pour la base de données

## Service API et Routes

### Routes REST

#### 1. Playlists (`/api/playlists`)
- **`GET /`** : Liste des playlists
- **`GET /{playlist_id}`** : Détails d'une playlist
- **`POST /`** : Créer une playlist
- **`PUT /{playlist_id}`** : Mettre à jour une playlist
- **`DELETE /{playlist_id}`** : Supprimer une playlist
- **`POST /{playlist_id}/tracks`** : Ajouter des pistes
- **`DELETE /{playlist_id}/tracks/{track_id}`** : Supprimer une piste

#### 2. NFC (`/api/nfc`)
- **`GET /status`** : État du service NFC
- **`POST /start_observe`** : Démarrer l'observation NFC
- **`POST /start`** : Démarrer l'association de tag
- **`POST /stop`** : Arrêter l'association
- **`POST /link`** : Associer un tag à une playlist
- **`POST /override`** : Configurer le mode override

#### 3. Healthcheck
- **`GET /health`** : Vérification de l'état du système

### Handlers Socket.IO

#### 1. Connexion
- **`connect`** : Gestion des connexions client
- **`disconnect`** : Nettoyage à la déconnexion

#### 2. Contrôles de lecture
- **`start_playlist`** : Démarrer une playlist
- **`pause_playback`** : Mettre en pause
- **`resume_playback`** : Reprendre la lecture
- **`next_track`** : Piste suivante
- **`prev_track`** : Piste précédente

#### 3. Notifications
- Événements **`playback_status`** : Statut de lecture
- Événements **`track_progress`** : Progression de lecture
- Événements **`nfc_status`** : État du NFC

## Système de Monitoring

Le monitoring est géré via un module personnalisé `improved_logger.py` qui :

### 1. Améliore le logging standard
- Ajoute des niveaux de log personnalisés
- Enrichit les logs avec des informations contextuelles
- Formatage amélioré pour meilleure lisibilité

### 2. Gestionnaire d'erreurs (`error_handler.py`)
- Capture et traite les exceptions
- Enregistre les détails des erreurs avec contexte
- Permet l'ajout de métadonnées aux erreurs

### 3. Remontée d'information
- Les logs peuvent être consultés via `journalctl` pour le service systemd
- Interface Socket.IO pour remonter les informations de statut au frontend

## Modèle et Accès à la Base de Données

### 1. Modèles ORM
- **`Playlist`** : Entité principale pour les collections audio
- **`Track`** : Pistes audio individuelles
- Modèle relationnel pour l'association playlist-pistes

### 2. Repositories
- Pattern Repository pour isoler l'accès aux données
- **`playlist_repository.py`** : Opérations CRUD pour les playlists
- Requêtes optimisées pour minimiser les accès disque

### 3. Configuration SQLite
- Base de données fichier en SQLite
- Path configurable via variables d'environnement
- Initialisation au démarrage avec migrations automatiques

## Module Core de l'Application

Le cœur de l'application est organisé autour de plusieurs classes clés :

### 1. `Application`
- Orchestrateur principal qui initialise l'environnement
- Coordonne les services et la configuration
- Gère le cycle de vie de l'application

### 2. `ContainerAsync`
- Implémentation du pattern d'injection de dépendances
- Crée et fournit les instances des services
- Gère les dépendances asynchrones

### 3. `PlaylistController`
- Logique métier principale pour la lecture audio
- Interprète les événements NFC
- Coordonne le lecteur audio et la gestion des playlists

## Asynchronicité et Multithreading

L'application utilise un modèle mixte :

### 1. Asynchrone (asyncio)
- API FastAPI entièrement asynchrone
- Handlers Socket.IO asynchrones
- Initialisation des services avec `await`

### 2. Multithreading
- Thread dédié pour la détection NFC continue
- Thread pour le suivi de progression audio
- Thread pour l'émission d'événements Socket.IO

### 3. Communication inter-processus
- Utilisation de `rx.subject.Subject` pour les événements
- Files asyncio pour communiquer entre threads
- Synchronisation via les événements asyncio

## Système de Verrouillage (Locks)

Pour éviter les conflits d'accès, plusieurs mécanismes de verrouillage sont mis en place :

### 1. Locks threading
- `threading.Lock()` pour protéger les ressources partagées
- Utilisés notamment dans le gestionnaire audio

### 2. Sémaphores asyncio
- `asyncio.Semaphore` pour limiter l'accès concurrent aux ressources
- Protection des opérations de base de données

### 3. Flags de protection
- État `_auto_pause_enabled` pour contrôler quand la pause est autorisée
- État `_is_playing` dans le lecteur audio

### 4. Verrous logiques
- Fenêtre temporelle `_manual_action_priority_window` pour éviter les conflits
- Délais de debounce dans le `TagDetectionManager`
