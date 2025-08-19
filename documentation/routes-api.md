# Documentation des routes API

Ce document recense **toutes les routes API** exposées par le backend FastAPI du projet, avec détails exhaustifs pour chaque endpoint : méthode, URL, description, paramètres, payloads, réponses, erreurs, et informations utiles pour le frontend (authentification, CORS, etc.).

---

## Table des matières
- [Playlists (`/api/playlists`)](#playlists)
- [Système (`/api`)](#system)
- [Lecture (`/api/playback`)](#playback)
- [NFC (`/api/nfc`)](#nfc)
- [YouTube (`/api/youtube`)](#youtube)
- [Utilitaires et fichiers](#utilitaires)
- [Web (SPA/static)](#web)

---

## <a name="playlists"></a>Playlists (`/api/playlists`)

### GET `/api/playlists/`
- **Description** : Liste paginée de toutes les playlists.
- **Méthode** : `GET`
- **Paramètres Query** :
  - `page` *(int, optionnel, défaut=1)* : Numéro de page
  - `page_size` *(int, optionnel, défaut=50)* : Nombre d'éléments par page
- **Réponse** :
```json
{
  "playlists": [
    { "id": "string", "name": "string", ... }
  ]
}
```
- **Codes d'erreur** :
  - `500` : Erreur interne (ex : accès service playlists)
- **Infos frontend** :
  - Pas d'authentification requise
  - CORS activé (voir configuration globale FastAPI)
  - **IMPORTANT** : Utiliser toujours le slash final `/` pour les routes API

### POST `/api/playlists/`
- **Description** : Crée une nouvelle playlist
- **Méthode** : `POST`
- **Payload** :
```json
{
  "title": "string"
}
```
- **Réponse** :
```json
{ "status": "success", "playlist": { ... } }
```
- **Codes d'erreur** :
  - `400` : Données invalides
  - `422` : Titre manquant ou invalide
  - `500` : Erreur serveur

### GET `/api/playlists/{playlist_id}`
- **Description** : Récupère une playlist par son ID
- **Paramètres Path** :
  - `playlist_id` *(str, requis)*
- **Réponse** :
```json
{ "playlist": { ... } }
```
- **Codes d'erreur** :
  - `404` : Playlist non trouvée

### DELETE `/api/playlists/{playlist_id}`
- **Description** : Supprime une playlist et ses fichiers
- **Paramètres Path** :
  - `playlist_id` *(str, requis)*
- **Réponse**
```json
{ "id": "string", "deleted": true }
```
- **Codes d'erreur** :
  - `404` : Playlist non trouvée
  - `500` : Erreur serveur

### POST `/api/playlists/{playlist_id}/uploads/session`
- **Description** : Initialise une session d'upload par chunks avec gestion de reprise
- **Méthode** : `POST`
- **Paramètres Path** :
  - `playlist_id` *(str, requis)* : ID de la playlist
- **Payload** :
```json
{
  "filename": "string",
  "file_size": 12345678,
  "chunk_size": 1048576,
  "file_hash": "sha256_hash_optional"
}
```
- **Réponse** :
```json
{
  "session_id": "string",
  "status": "initialized",
  "chunk_size": 1048576,
  "total_chunks": 12,
  "expires_at": "2025-08-18T17:52:13Z",
  "resume_info": {
    "uploaded_chunks": [],
    "next_chunk_index": 0
  }
}
```
- **Codes d'erreur** :
  - `400` : Données invalides, format non supporté, ou taille excessive
  - `404` : Playlist non trouvée
  - `409` : Session existante pour ce fichier (retourne session_id existant)
  - `500` : Erreur serveur
- **Infos frontend** :
  - Le `session_id` retourné doit être utilisé pour tous les appels suivants
  - Sessions expirent après 24h par défaut (configurable)
  - Support de la reprise d'upload via `file_hash`
  - Chunk size recommandé : 1MB (1048576 bytes)

### PUT `/api/playlists/{playlist_id}/uploads/{session_id}/chunks/{chunk_index}`
- **Description** : Envoie un chunk spécifique d'un fichier en cours d'upload
- **Méthode** : `PUT`
- **Paramètres Path** :
  - `playlist_id` *(str, requis)* : ID de la playlist
  - `session_id` *(str, requis)* : ID de session d'upload
  - `chunk_index` *(int, requis)* : Index du chunk (commence à 0)
- **Headers** :
  - `Content-Type: application/octet-stream`
  - `Content-Length: {chunk_size}`
  - `X-Chunk-Hash: sha256_hash` *(optionnel)*
- **Body** : Données binaires du chunk
- **Réponse** :
```json
{
  "status": "success",
  "chunk_index": 0,
  "chunk_hash": "sha256_hash",
  "progress": 10.0,
  "uploaded_chunks": [0],
  "remaining_chunks": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
  "complete": false
}
```
- **Codes d'erreur** :
  - `400` : Chunk invalide, taille incorrecte, ou hash mismatch
  - `404` : Playlist, session non trouvée, ou session expirée
  - `409` : Chunk déjà reçu (idempotent)
  - `413` : Chunk trop volumineux
  - `500` : Erreur serveur
- **Infos frontend** :
  - Opération idempotente : renvoyer le même chunk retourne 200
  - Événements Socket.IO `upload_progress` émis automatiquement
  - Validation de hash optionnelle pour intégrité des données

### POST `/api/playlists/{playlist_id}/uploads/{session_id}/finalize`
- **Description** : Finalise un upload en assemblant et validant tous les chunks
- **Méthode** : `POST`
- **Paramètres Path** :
  - `playlist_id` *(str, requis)* : ID de la playlist
  - `session_id` *(str, requis)* : ID de session d'upload
- **Payload** :
```json
{
  "final_hash": "sha256_hash_optional",
  "metadata_override": {
    "title": "string_optional",
    "artist": "string_optional",
    "album": "string_optional"
  }
}
```
- **Réponse** :
```json
{
  "status": "success",
  "filename": "string",
  "file_size": 12345678,
  "file_hash": "sha256_hash",
  "track_id": "string",
  "metadata": {
    "title": "string",
    "artist": "string",
    "album": "string",
    "duration": 123.45,
    "bitrate": 320,
    "format": "mp3"
  },
  "processing_time": 2.34
}
```
- **Codes d'erreur** :
  - `400` : Upload incomplet, chunks manquants, ou hash mismatch
  - `404` : Playlist ou session non trouvée
  - `422` : Fichier corrompu ou format invalide après assemblage
  - `500` : Erreur serveur lors de l'assemblage
- **Infos frontend** :
  - Validation automatique de l'intégrité du fichier final
  - Événement Socket.IO `upload_complete` émis avec métadonnées complètes
  - Session automatiquement nettoyée après finalisation
  - Track ajouté à la playlist avec `track_id` retourné

### GET `/api/playlists/{playlist_id}/uploads/{session_id}`
- **Description** : Récupère le statut détaillé d'une session d'upload
- **Méthode** : `GET`
- **Paramètres Path** :
  - `playlist_id` *(str, requis)* : ID de la playlist
  - `session_id` *(str, requis)* : ID de la session d'upload
- **Réponse** :
```json
{
  "status": "in_progress",
  "session_id": "string",
  "playlist_id": "string",
  "filename": "string",
  "file_size": 10485760,
  "chunk_size": 1048576,
  "total_chunks": 10,
  "uploaded_chunks": [0, 1, 2, 3, 4],
  "missing_chunks": [5, 6, 7, 8, 9],
  "current_size": 5242880,
  "progress": 50.0,
  "created_at": "2025-08-18T15:52:13Z",
  "expires_at": "2025-08-19T15:52:13Z",
  "last_activity": "2025-08-18T16:30:45Z",
  "complete": false,
  "can_resume": true
}
```
- **Codes d'erreur** :
  - `404` : Playlist ou session non trouvée
  - `410` : Session expirée
  - `500` : Erreur serveur
- **Infos frontend** :
  - Utilisé pour reprendre un upload interrompu
  - `missing_chunks` indique quels chunks doivent encore être envoyés
  - `can_resume` indique si la reprise est possible

### POST `/api/playlists/{playlist_id}/upload`
- **Description** : Upload direct d'un fichier audio (méthode traditionnelle, non chunked)
- **Méthode** : `POST`
- **Paramètres Path** :
  - `playlist_id` *(str, requis)* : ID de la playlist
- **Paramètres Form** :
  - `file` *(file, requis)* : Fichier audio à uploader
- **Réponse** :
```json
{
  "status": "success",
  "filename": "string",
  "metadata": {
    "title": "string",
    "artist": "string",
    "album": "string",
    "duration": 123.45
  }
}
```
- **Codes d'erreur** :
  - `400` : Format de fichier non supporté ou taille excessive
  - `404` : Playlist non trouvée
  - `500` : Erreur serveur
- **Infos frontend** :
  - Pour les fichiers volumineux, préférer l'upload par chunks
  - Taille maximale : 50MB (définie dans la configuration)

### POST `/api/playlists/{playlist_id}/reorder`
- **Description** : Réorganise les pistes d'une playlist
- **Méthode** : `POST`
- **Paramètres Path** :
  - `playlist_id` *(str, requis)* : ID de la playlist
- **Payload** :
```json
{
  "track_order": [3, 1, 2, 4]
}
```
- **Réponse** :
```json
{
  "status": "success",
  "message": "Tracks reordered successfully"
}
```
- **Codes d'erreur** :
  - `400` : Ordre de pistes invalide
  - `404` : Playlist non trouvée
  - `500` : Erreur serveur

### DELETE `/api/playlists/{playlist_id}/tracks`
- **Description** : Supprime des pistes d'une playlist
- **Méthode** : `DELETE`
- **Paramètres Path** :
  - `playlist_id` *(str, requis)* : ID de la playlist
- **Payload** :
```json
{
  "track_numbers": [1, 3, 5]
}
```
- **Réponse** :
```json
{
  "status": "success",
  "message": "Tracks deleted successfully"
}
```
- **Codes d'erreur** :
  - `400` : Numéros de pistes invalides
  - `404` : Playlist non trouvée
  - `500` : Erreur serveur

### POST `/api/playlists/{playlist_id}/start`
- **Description** : Démarre la lecture d'une playlist
- **Méthode** : `POST`
- **Paramètres Path** :
  - `playlist_id` *(str, requis)* : ID de la playlist
- **Réponse** :
```json
{
  "status": "success",
  "message": "Playlist started",
  "playlist_id": "string"
}
```
- **Codes d'erreur** :
  - `404` : Playlist non trouvée
  - `503` : Service audio non disponible
  - `500` : Erreur serveur

### POST `/api/playlists/{playlist_id}/play/{track_number}`
- **Description** : Joue une piste spécifique d'une playlist
- **Méthode** : `POST`
- **Paramètres Path** :
  - `playlist_id` *(str, requis)* : ID de la playlist
  - `track_number` *(int, requis)* : Numéro de la piste
- **Réponse** :
```json
{
  "status": "success",
  "message": "Track started",
  "playlist_id": "string",
  "track_number": 3
}
```
- **Codes d'erreur** :
  - `404` : Playlist ou piste non trouvée
  - `503` : Service audio non disponible
  - `500` : Erreur serveur

### POST `/api/playlists/control`
- **Description** : Contrôle la lecture (play/pause/next/previous/stop)
- **Méthode** : `POST`
- **Payload** :
```json
{
  "action": "play"
}
```
- **Actions supportées** : `play`, `pause`, `next`, `previous`, `stop`
- **Réponse** :
```json
{
  "status": "success",
  "action": "play",
  "message": "Playback started"
}
```
- **Codes d'erreur** :
  - `400` : Action invalide
  - `503` : Service audio non disponible
  - `500` : Erreur serveur

### POST `/api/playlists/nfc/{nfc_tag_id}/associate/{playlist_id}`
- **Description** : Associe un tag NFC à une playlist
- **Méthode** : `POST`
- **Paramètres Path** :
  - `nfc_tag_id` *(str, requis)* : ID du tag NFC
  - `playlist_id` *(str, requis)* : ID de la playlist
- **Réponse** :
```json
{
  "status": "success",
  "message": "NFC tag associated with playlist",
  "nfc_tag_id": "string",
  "playlist_id": "string"
}
```
- **Codes d'erreur** :
  - `404` : Playlist non trouvée
  - `500` : Erreur serveur

### DELETE `/api/playlists/nfc/{playlist_id}`
- **Description** : Supprime l'association NFC d'une playlist
- **Méthode** : `DELETE`
- **Paramètres Path** :
  - `playlist_id` *(str, requis)* : ID de la playlist
- **Réponse** :
```json
{
  "status": "success",
  "message": "NFC association removed"
}
```
- **Codes d'erreur** :
  - `404` : Playlist non trouvée
  - `500` : Erreur serveur

### GET `/api/playlists/nfc/{nfc_tag_id}`
- **Description** : Récupère la playlist associée à un tag NFC
- **Méthode** : `GET`
- **Paramètres Path** :
  - `nfc_tag_id` *(str, requis)* : ID du tag NFC
- **Réponse** :
```json
{
  "playlist": {
    "id": "string",
    "name": "string",
    "tracks": [...]
  }
}
```
- **Codes d'erreur** :
  - `404` : Aucune playlist associée à ce tag NFC
  - `500` : Erreur serveur

### POST `/api/playlists/sync`
- **Description** : Synchronise les playlists avec le système de fichiers
- **Méthode** : `POST`
- **Réponse** :
```json
{
  "status": "success",
  "message": "Filesystem sync completed",
  "playlists_added": 2,
  "playlists_updated": 1,
  "tracks_added": 15,
  "tracks_removed": 3
}
```
- **Codes d'erreur** :
  - `500` : Erreur serveur

---

## <a name="system"></a>Système (`/api`)

### GET `/api/system/info`
- **Description** : Informations système détaillées
- **Méthode** : `GET`
- **Réponse** :
```json
{
  "system": {
    "platform": "Linux",
    "platform_release": "5.15.0",
    "platform_version": "#1 SMP",
    "architecture": "armv7l",
    "hostname": "tomb-rpi",
    "python_version": "3.9.2"
  },
  "hardware": {
    "cpu_count": 4,
    "memory_total": 1073741824,
    "memory_available": 536870912,
    "disk_usage": {
      "total": 31914983424,
      "used": 12345678901,
      "free": 19569304523
    }
  },
  "application": {
    "name": "TheOpenMusicBox",
    "version": "1.0.0",
    "container_available": true,
    "pid": 1234
  }
}
```

### GET `/api/system/logs`
- **Description** : Récupère les logs système disponibles
- **Méthode** : `GET`
- **Réponse** :
```json
{
  "logs": [
    {"file": "/var/log/tomb-rpi/app.log", "line": "2025-01-17 10:30:15 - INFO - Application started"},
    {"file": "/var/log/tomb-rpi/app.log", "line": "2025-01-17 10:30:16 - INFO - Audio system initialized"}
  ],
  "log_files_available": ["/var/log/tomb-rpi/app.log", "/tmp/tomb-rpi.log"]
}
```

### POST `/api/system/restart`
- **Description** : Redémarre l'application
- **Méthode** : `POST`
- **Réponse** :
```json
{
  "status": "restart_scheduled",
  "message": "Application restart scheduled in 2 seconds"
}
```
- **Codes d'erreur** :
  - `500` : Erreur serveur

---

## <a name="nfc"></a>NFC (`/api/nfc`)

### GET `/api/nfc/status`
- **Description** : État du lecteur NFC
- **Méthode** : `GET`
- **Réponse** :
```json
{
  "status": "ready", // "ready", "error", "not_found"
  "device_info": "ACR122U"
}
```

### GET `/api/nfc/scan`
- **Description** : Scan for available NFC tags
- **Méthode** : `GET`
- **Réponse** :
```json
{
  "status": "success",
  "tags_found": [
    {"tag_id": "04:5A:B2:C3:D4", "type": "MIFARE"}
  ],
  "message": "Found 1 tag(s)"
}
```
- **Codes d'erreur** :
  - `503` : Lecteur NFC non disponible
  - `500` : Erreur lors du scan

### POST `/api/nfc/write`
- **Description** : Write data to an NFC tag
- **Méthode** : `POST`
- **Payload** :
```json
{
  "tag_id": "04:5A:B2:C3:D4",
  "data": "playlist_123"
}
```
- **Réponse** :
```json
{
  "status": "success",
  "message": "Tag written successfully"
}
```

---

## <a name="youtube"></a>YouTube (`/api/youtube`)

### GET `/api/youtube/search`
- **Description** : Search for YouTube videos
- **Méthode** : `GET`
- **Paramètres Query** :
  - `query` *(str, requis)* : Search terms
  - `max_results` *(int, optionnel, défaut=10)* : Maximum number of results
- **Réponse** :
```json
{
  "status": "success",
  "query": "search terms",
  "results": [
    {
      "id": "video_id",
      "title": "Video Title",
      "thumbnail": "thumbnail_url",
      "duration": "3:45",
      "channel": "Channel Name"
    }
  ],
  "count": 1
}
```
- **Codes d'erreur** :
  - `400` : Query parameter missing
  - `500` : Search failed

### POST `/api/youtube/download`
- **Description** : Télécharge une vidéo YouTube
- **Méthode** : `POST`
- **Payload** :
```json
{
  "video_id": "string",
  "playlist_id": "string"
}
```
- **Réponse** :
```json
{
  "status": "downloading",
  "task_id": "string"
}
```

### GET `/api/youtube/status/{task_id}`
- **Description** : Get status of a YouTube download task
- **Paramètres Path** :
  - `task_id` *(str, requis)* : Task identifier
- **Réponse** :
```json
{
  "status": "found",
  "task_id": "task_123",
  "task_status": {
    "state": "in_progress",
    "progress": 45.6,
    "message": "Downloading..."
  }
}
```
- **Codes d'erreur** :
  - `404` : Task not found or expired
  - `500` : Status check failed
  "message": "Downloading..."
}
```

---

## <a name="utilitaires"></a>Utilitaires et fichiers

### GET `/api/uploads/sessions`
- **Description** : Liste les sessions d'upload actives (pour administration/debug)
- **Méthode** : `GET`
- **Paramètres Query** :
  - `status` *(str, optionnel)* : Filtre par statut (`active`, `expired`, `completed`)
  - `playlist_id` *(str, optionnel)* : Filtre par playlist
- **Réponse** :
```json
{
  "sessions": [
    {
      "session_id": "string",
      "playlist_id": "string", 
      "filename": "string",
      "status": "in_progress",
      "progress": 45.2,
      "created_at": "2025-08-18T15:52:13Z",
      "expires_at": "2025-08-19T15:52:13Z"
    }
  ],
  "total": 1,
  "active_count": 1
}
```
- **Codes d'erreur** :
  - `500` : Erreur serveur

### DELETE `/api/uploads/sessions/{session_id}`
- **Description** : Annule et nettoie une session d'upload
- **Méthode** : `DELETE`
- **Paramètres Path** :
  - `session_id` *(str, requis)* : ID de la session à supprimer
- **Réponse** :
```json
{
  "status": "success",
  "message": "Session cancelled and cleaned up",
  "session_id": "string"
}
```
- **Codes d'erreur** :
  - `404` : Session non trouvée
  - `500` : Erreur serveur

### POST `/api/uploads/cleanup`
- **Description** : Nettoie les sessions expirées (tâche de maintenance)
- **Méthode** : `POST`
- **Réponse** :
```json
{
  "status": "success",
  "cleaned_sessions": 5,
  "freed_space_mb": 234.5
}
```

### GET `/api/playback/status`
- **Description** : Statut de la lecture en cours
- **Méthode** : `GET`
- **Paramètres** : Aucun
- **Exemple de requête** :
```bash
curl "http://localhost:8000/api/playback/status"
```
- **Réponse** :
```json
{
  "is_playing": true, // true si en cours de lecture, false sinon
  "volume": 75, // volume actuel (0-100)
  "audio_available": true // true si le système audio est disponible
}
```
- **Codes d'erreur** :
  - `503` : Système audio non disponible
  - `500` : Erreur serveur
- **Notes** : Les informations de piste (`track`) et de playlist ne sont incluses que si une lecture est en cours ou en pause.

---

## <a name="web"></a>Web (SPA/static)

### GET `/` et `/static/*`
- **Description** : Sert l'application frontend (index.html, fichiers statiques)
- **Infos frontend** :
  - Pour le routage SPA, toute URL non-API retourne index.html
  - Les fichiers statiques sont servis depuis `/static` (voir structure du dossier)

---

## Informations transverses

### Sécurité et Authentification
- **Authentification** : Aucune route n'est protégée par défaut (voir code pour évolutions futures)
- **Rate Limiting** : Recommandé pour les routes d'upload (ex: 10 uploads/minute)
- **Validation** : Tous les payloads sont validés via Pydantic

### Configuration Technique
- **CORS** : Activé globalement via FastAPI (voir `main.py`)
- **Formatage** : Toutes les réponses sont au format JSON
- **Encoding** : UTF-8 pour tous les textes, binaire pour les chunks
- **Timeouts** : 30s par défaut pour les routes API, 5min pour uploads

### Gestion des Erreurs
- **Format standard** : `{"error": "code", "message": "description", "details": {}}`
- **Codes d'erreur** : HTTP standards + codes métier spécifiques
- **Logging** : Toutes les erreurs 5xx sont loggées côté serveur
- **Retry Logic** : Codes 5xx et timeouts sont retry-able, 4xx ne le sont pas

### Performance et Scalabilité
- **Upload Sessions** : Stockage en mémoire + persistance optionnelle
- **Cleanup automatique** : Sessions expirées nettoyées toutes les heures
- **Monitoring** : Métriques disponibles via `/api/system/metrics` (non documenté)
- **Caching** : Réponses GET cachées selon les headers appropriés

### Architecture et Dépendances
- **Services** : `PlaylistService`, `UploadService`, `NFCService` injectés via FastAPI DI
- **Storage** : Système de fichiers local + métadonnées en base
- **Queue System** : Traitement asynchrone pour finalisation des uploads
- **Extensibilité** : Nouveaux endpoints via routers modulaires

### Recommandations Frontend
- **Retry Strategy** : Exponentiel backoff pour 5xx, pas de retry pour 4xx
- **Chunk Size** : 1MB optimal, ajustable selon la connexion
- **Progress Tracking** : Combiner API polling + Socket.IO events
- **Error Handling** : Distinguer erreurs récupérables vs fatales
- **Session Management** : Vérifier expiration avant envoi de chunks

## Socket.IO Events

Le serveur émet plusieurs événements Socket.IO que le client peut écouter:

### Upload Events
- **`upload_session_created`**: Émis lors de la création d'une nouvelle session
  ```json
  {
    "event": "upload_session_created",
    "playlist_id": "string",
    "session_id": "string",
    "filename": "string",
    "total_chunks": 12,
    "expires_at": "2025-08-19T15:52:13Z"
  }
  ```

- **`upload_progress`**: Émis à chaque chunk reçu avec succès
  ```json
  {
    "event": "upload_progress",
    "playlist_id": "string",
    "session_id": "string",
    "filename": "string",
    "chunk_index": 3,
    "progress": 30.0,
    "uploaded_chunks": [0, 1, 2, 3],
    "remaining_chunks": [4, 5, 6, 7, 8, 9, 10, 11],
    "speed_mbps": 2.5,
    "eta_seconds": 45,
    "complete": false
  }
  ```

- **`upload_complete`**: Émis quand un upload est finalisé avec succès
  ```json
  {
    "event": "upload_complete",
    "playlist_id": "string",
    "session_id": "string",
    "filename": "string",
    "track_id": "string",
    "file_size": 12345678,
    "processing_time": 2.34,
    "metadata": {
      "title": "string",
      "artist": "string",
      "album": "string",
      "duration": 123.45,
      "bitrate": 320,
      "format": "mp3"
    }
  }
  ```

- **`upload_error`**: Émis en cas d'erreur pendant l'upload
  ```json
  {
    "event": "upload_error",
    "playlist_id": "string",
    "session_id": "string",
    "filename": "string",
    "error_code": "CHUNK_VALIDATION_FAILED",
    "error_message": "Chunk hash mismatch at index 5",
    "chunk_index": 5,
    "retry_possible": true,
    "session_valid": true
  }
  ```

- **`upload_session_expired`**: Émis quand une session expire
  ```json
  {
    "event": "upload_session_expired",
    "session_id": "string",
    "playlist_id": "string",
    "filename": "string",
    "expired_at": "2025-08-19T15:52:13Z"
  }
  ```

### Playback Events
- **`playback_state_changed`**: Émis lors des changements d'état de lecture
  ```json
  {
    "event": "playback_state_changed",
    "state": "playing",
    "playlist_id": "string",
    "track_number": 3,
    "position": 45.2,
    "volume": 75
  }
  ```

---

*Documentation mise à jour le 2025-08-18 - Version 2.0 avec upload chunked amélioré.*