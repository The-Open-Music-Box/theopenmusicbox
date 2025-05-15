# 3. Fonctionnement Détaillé du Backend The Open Music Box

## 3.1. Parcours de Données et Logique Applicative

### 3.1.1. Scénario Principal : Scan d'un Tag NFC et Lecture de Playlist

Ce scénario est au cœur de l'application.

1.  **Détection Matérielle (Module NFC)**:
    *   Sur Raspberry Pi, `PN532I2CNFC` scrute en continu le lecteur NFC via I2C (`_nfc_reader_loop`).
    *   Lorsqu'un tag est détecté, `read_nfc()` lit son UID.
    *   L'UID brut est passé au `TagDetectionManager` (`process_tag_detection`).
    *   `TagDetectionManager` applique une logique de debounce/cooldown et vérifie si c'est une nouvelle détection, une réapparition, ou un tag déjà présent. Si l'événement est jugé pertinent, il émet un dictionnaire (ex: `{'uid': '...', 'timestamp': ..., 'new_detection': True}`) sur son `tag_subject` (RxPy Subject).
    *   Si aucun tag n'est lu, `process_tag_absence()` est appelé, qui peut émettre un événement d'absence sur le `tag_subject`.
    *   En mode mock, `MockNFC` simule ces événements périodiquement.

2.  **Gestion par `NFCHandler` et `NFCService`**:
    *   `NFCHandler` (wrapper) expose le `tag_subject` du `TagDetectionManager` (ou du `MockNFC`).
    *   `NFCService` s'abonne à ce `tag_subject` via sa méthode `_on_tag_subject`.
    *   Si `NFCService` n'est **pas** en mode association (`_association_mode == False`):
        *   Il prend le `tag_uid` (et `tag_data`) et l'émet sur son propre `_playback_subject` (un autre RxPy Subject). Cet événement est destiné à déclencher la lecture.
    *   Si `NFCService` **est** en mode association (déclenché via une route API, ex: `/nfc/listen/{playlist_id}`):
        *   Il gère la logique d'association du tag avec `current_playlist_id`, communique avec le client via Socket.IO, et utilise `PlaylistService` pour persister l'association. Il peut forcer une re-détection du tag après association pour initier la lecture.

3.  **Réception par `PlaylistController`**:
    *   Lors de son initialisation (via `Application` et `main.py`), `PlaylistController` s'abonne au `playback_subject` de `NFCService` (méthode `set_nfc_service`).
    *   La méthode `handle_tag_scanned(tag_uid, tag_data)` du `PlaylistController` est donc invoquée.

4.  **Logique du `PlaylistController`**:
    *   `handle_tag_scanned` vérifie d'abord si le scan doit être ignoré (mode association NFC, action manuelle récente, etc. via `_should_ignore_tag_scan`).
    *   Il récupère les données de la playlist associée au `tag_uid` en appelant `self._playlist_service.get_playlist_by_nfc_tag(tag_uid)`.
    *   En fonction de l'état actuel de la lecture (joue, pause, arrêté, terminé) et si le tag est nouveau ou le même, il applique une logique de décision (Cas A à E décrits dans le code) :
        *   **Nouveau tag / Tag différent avec playlist**: Démarre la playlist depuis le début (`_playlist_service.play_playlist_with_validation`). Active `_auto_pause_enabled`.
        *   **Même tag, playlist terminée**: Redémarre la playlist. Active `_auto_pause_enabled`.
        *   **Même tag, lecture en pause**: Reprend la lecture (`self._audio.resume()`). Active `_auto_pause_enabled`.
        *   **Même tag, lecture arrêtée**: Redémarre la playlist. Active `_auto_pause_enabled`.
        *   **Tag sans playlist associée**: Aucune action de lecture.
    *   `_playlist_service.play_playlist_with_validation` convertit les données de la playlist en modèle `Playlist`, valide les pistes, puis appelle `self._audio.set_playlist(playlist_model)` sur l'instance `AudioPlayer`.

5.  **Lecture Audio (Module AudioPlayer)**:
    *   `AudioPlayer.set_playlist(playlist_model)` délègue à l'implémentation matérielle (`AudioPlayerWM8960` ou `MockAudioPlayer`).
    *   `AudioPlayerWM8960` (via `BaseAudioPlayer`) charge la playlist, sélectionne la première piste, et appelle `self.play_track(track_number)`.
    *   `AudioPlayerWM8960.play_track()` utilise `PygameAudioBackend` pour charger (`_audio_backend.load()`) et jouer (`_audio_backend.play()`) le fichier audio.
    *   `PygameAudioBackend` interagit avec `pygame.mixer.music` pour la lecture effective. Il gère aussi l'événement `MUSIC_END` de Pygame pour notifier la fin d'une piste.
    *   Pendant la lecture, `AudioPlayerWM8960` (via `BaseAudioPlayer` et son thread de progression) émet des événements de progression et de statut via le `PlaybackSubject` du `NotificationService`.

6.  **Gestion de l'Absence de Tag**:
    *   Si `TagDetectionManager` émet un événement d'absence, `NFCService._on_tag_subject` le reçoit.
    *   Si le `PlaylistController` est lié, `NFCService` appelle `playlist_controller.handle_tag_absence()`.
    *   `PlaylistController.handle_tag_absence()`: Si `_auto_pause_enabled` est vrai et que la lecture est en cours, il appelle `self._audio.pause()`. `_auto_pause_enabled` est ensuite désactivé.

### 3.1.2. Scénario : Contrôle Manuel (ex: Bouton "Piste Suivante")

1.  **Détection Matérielle (Module Contrôles)**:
    *   Sur Raspberry Pi, `ControlesGPIO` utilise `gpiozero.Button` pour un bouton physique (ex: GPIO5 pour "piste suivante").
    *   Lorsqu'un appui est détecté (après debounce matériel), le callback enregistré par la classe `Button` (dans `input_devices`) est appelé.
    *   Ce callback est `Button._on_button_state_change(pressed=True)`.

2.  **Émission de l'Événement de Contrôle**:
    *   `Button._on_button_state_change` crée un `ControlesEvent` (ex: `event_type=ControlesEventType.NEXT_TRACK`).
    *   Cet événement est émis sur le `_event_subject` (RxPy Subject) du `ControlesManager`.

3.  **Réception et Action (Exemple : `app.main.py` ou `PlaylistController`)**:
    *   Dans `app.main.py`, lors de l'initialisation des routes et des contrôles physiques (via `playlist_routes._setup_controls_integration`), un abonnement est fait à l'`event_observable` du `ControlesManager`.
    *   Le callback de cet abonnement reçoit le `ControlesEvent`.
    *   En fonction de `event.event_type`:
        *   Si `NEXT_TRACK`: Appelle `playlist_controller.handle_manual_action('next')` (ou directement `audio_player.next_track()`).
        *   Si `VOLUME_UP`: Appelle `audio_player.set_volume()` avec une valeur augmentée.
    *   `PlaylistController.handle_manual_action()`:
        *   Enregistre `_last_manual_action_time` (pour la priorité sur les scans NFC).
        *   Désactive `_auto_pause_enabled`.
        *   Appelle la méthode correspondante sur `self._audio` (ex: `self._audio.next_track()`).

### 3.1.3. Scénario : Association d'un Tag NFC via API

1.  **Requête API**: Le frontend envoie une requête (ex: POST `/api/nfc/listen/{playlist_id}`) à FastAPI.
2.  **Route NFC (`NFCRoutes`)**:
    *   L'endpoint correspondant dans `NFCRoutes` est activé.
    *   Il appelle `self.nfc_service.start_listening(playlist_id, client_sid)` (où `client_sid` est l'ID de session Socket.IO du client demandeur).
3.  **Logique de `NFCService`**:
    *   `start_listening` active le mode association (`_association_mode = True`, `waiting_for_tag = True`), stocke `playlist_id` et `client_sid`.
    *   Il démarre le lecteur NFC si nécessaire et commence à envoyer des mises à jour `nfc_scanning` au client via Socket.IO.
4.  **Scan du Tag**: L'utilisateur présente un tag au lecteur.
    *   Le flux de détection (Matériel -> TagDetectionManager -> NFCHandler -> NFCService._on_tag_subject) se produit comme décrit en 3.1.1 (points 1-2).
    *   `NFCService._on_tag_subject` appelle `asyncio.create_task(self.handle_tag_detected(tag_id, tag_data))`.
5.  **Traitement en Mode Association (`NFCService.handle_tag_detected`)**:
    *   Puisque `_association_mode` est vrai, la logique d'association est exécutée.
    *   Le service vérifie si le tag est déjà associé à une autre playlist (en consultant `self._playlists`, une liste en mémoire).
    *   Si le tag est libre ou si `_allow_override` est vrai:
        *   Il utilise `PlaylistService` (crée une instance temporaire) pour appeler `playlist_service.associate_nfc_tag(self.current_playlist_id, tag_id)`.
        *   `PlaylistService.associate_nfc_tag` appelle `PlaylistRepository.associate_nfc_tag` pour mettre à jour la base de données.
        *   `NFCService` met à jour sa liste `_playlists` en mémoire.
        *   Il envoie un message de succès (`nfc_status` type `success`) au client via Socket.IO.
        *   Il désactive le mode association (`waiting_for_tag = False`, `_association_mode = False`).
        *   Il tente de forcer une re-détection du tag via `self._nfc_handler.tag_detection_manager.force_redetect(tag_id)` pour potentiellement démarrer la lecture immédiatement.
    *   Si le tag est déjà associé et l'override n'est pas permis, un message d'erreur (`already_associated`) est envoyé au client.

## 3.2. Gestion des Événements, État, et Communication

*   **RxPy Subjects pour les Événements Matériels**:
    *   `TagDetectionManager._tag_subject`: Émet des événements de présence/absence de tag NFC après traitement (debounce, cooldown). Consommé par `NFCService`.
    *   `NFCService._playback_subject`: Émet des événements de tag NFC spécifiquement destinés à déclencher/affecter la lecture. Consommé par `PlaylistController`.
    *   `ControlesManager._event_subject`: Émet des `ControlesEvent` (boutons, encodeur). Consommé par la logique de gestion des contrôles (ex: dans `app.main.py` ou `PlaylistController`).

*   **`NotificationService.PlaybackSubject`**:
    *   Utilisé par `BaseAudioPlayer` (et donc ses sous-classes `MockAudioPlayer`, `AudioPlayerWM8960`) pour diffuser l'état de la lecture audio (piste en cours, progression, statut play/pause/stop).
    *   Les `WebSocketHandlersAsync` s'abonnent à ce subject pour relayer ces informations au frontend via Socket.IO.

*   **Socket.IO**:
    *   Utilisé pour la communication bidirectionnelle en temps réel avec le frontend.
    *   **Backend -> Frontend**:
        *   Statut NFC (en attente de tag, tag détecté, association réussie/échouée) émis par `NFCService`.
        *   Statut de lecture (piste actuelle, progression, play/pause/stop) émis par `WebSocketHandlersAsync` en réponse aux événements de `PlaybackSubject`.
    *   **Frontend -> Backend**:
        *   Peu d'événements Socket.IO du frontend vers le backend sont explicitement visibles dans le code exploré, la plupart des interactions se faisant via l'API REST. Cependant, des actions de contrôle de lecture pourraient potentiellement être envoyées via Socket.IO.

*   **Gestion de l'État de Lecture**:
    *   L'état principal de la lecture (quelle playlist, quelle piste, position) est maintenu dans les instances de `AudioPlayer` (plus précisément dans `BaseAudioPlayer` et ses spécialisations).
    *   `PlaylistController` maintient l'état lié à l'interaction NFC (`_current_tag`, `_auto_pause_enabled`, `_last_manual_action_time`) pour prendre des décisions.
    *   La synchronisation de l'état entre ces composants et le frontend se fait via les mécanismes d'événements décrits ci-dessus.

*   **Gestion de l'État NFC**:
    *   `NFCService` gère l'état du mode d'association (`_association_mode`, `waiting_for_tag`, `current_playlist_id` pour l'association).
    *   `TagDetectionManager` gère l'état de bas niveau de la présence/absence de tag sur le lecteur.

## 3.3. Comportement du Système en Temps Réel

*   **Réactivité aux Tags NFC**: La chaîne de traitement (matériel -> TagDetectionManager -> NFCHandler -> NFCService -> PlaylistController -> AudioPlayer) est conçue pour être réactive. L'utilisation d'`asyncio` pour les opérations matérielles et la propagation des événements via RxPy visent à minimiser la latence.
*   **Réactivité aux Contrôles Physiques**: Les callbacks GPIO (gérés par `gpiozero` dans `ControlesGPIO`) sont généralement rapides. Les événements sont propagés via RxPy au `PlaylistController` ou à d'autres gestionnaires pour une action quasi immédiate.
*   **Mises à Jour de Statut au Frontend**:
    *   Les changements d'état de lecture (piste, progression, play/pause) sont notifiés par `AudioPlayerWM8960` (via `PlaybackSubject`) et relayés par `WebSocketHandlersAsync` au frontend. La fréquence des mises à jour de progression est gérée dans la boucle de `BaseAudioPlayer._progress_monitoring_thread`.
    *   Les changements d'état NFC (scan en cours, tag détecté pour association) sont envoyés par `NFCService` directement au client Socket.IO concerné.

Le système s'appuie fortement sur des mécanismes événementiels (RxPy, callbacks GPIO, événements Pygame) et la communication asynchrone (Socket.IO, `asyncio` pour certaines opérations) pour atteindre un comportement en temps réel.
