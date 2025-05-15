# 4. Comportements Spécifiques à Auditer

Cette section se concentre sur les aspects de l'application qui méritent une attention particulière lors d'un audit de code, notamment en ce qui concerne la gestion du matériel et les modules critiques.

## 4.1. Gestion du Matériel et des Entrées Physiques

### 4.1.1. Module NFC (`app/src/module/nfc/`)

*   **`PN532I2CNFC`**:
    *   **Accès I2C et Verrouillage**: L'utilisation de `asyncio.Lock` (`self._lock`) pour protéger les accès au bus I2C (`busio.I2C` et `_pn532` object) est cruciale. Vérifier que toutes les interactions matérielles avec `self._pn532` sont bien encapsulées dans `async with self._lock:`.
    *   **Initialisation Matérielle (`_initialize_hardware`)**: La séquence d'initialisation (création `I2C`, instanciation `PN532_I2C`, lecture version firmware, `SAM_configuration`) doit être robuste. Les erreurs ici peuvent empêcher toute fonctionnalité NFC. La gestion des exceptions avec `ErrorHandler.create_app_error` est présente.
    *   **Gestion des Erreurs de Lecture (`read_nfc`)**: La gestion des `RuntimeError` et `OSError` (pouvant survenir lors de la communication I2C) comme une absence de tag est une stratégie. S'assurer que cela ne masque pas des problèmes persistants du bus I2C. La journalisation des erreurs autres que "No card" ou "timeout" est importante.
    *   **Boucle de Lecture (`_nfc_reader_loop`)**:
        *   La réinitialisation du matériel (`_initialize_hardware()`) après `_config.max_errors` est une bonne mesure de robustesse.
        *   Le délai `_config.retry_delay` entre les lectures impacte la réactivité et la charge CPU.
    *   **Nettoyage (`cleanup`)**: S'assurer que `stop_nfc_reader` est bien appelé et que `_pn532` est libéré.

*   **`TagDetectionManager`**:
    *   **Logique de Cooldown/Debounce**: La logique dans `process_tag_detection` et `process_tag_absence` (utilisation de `cooldown_period`, `removal_threshold`, `_last_read_time`, `_tag_present`) est centrale pour éviter les événements multiples non désirés. Un audit attentif de cette logique d'état est recommandé pour s'assurer qu'elle couvre tous les cas de figure et ne conduit pas à des états incohérents ou à des événements manqués/superflus.
    *   **`force_redetect`**: Cette méthode est utilisée par `NFCService` après l'association d'un tag. Il est important que la mise à jour de l'état interne (`_last_tag`, `_last_read_time`, `_tag_present`) soit correcte pour que le tag soit traité comme une nouvelle détection par le `PlaylistController`.

### 4.1.2. Module Audio (`app/src/module/audio_player/`)

*   **`AudioPlayerWM8960` et `PygameAudioBackend`**:
    *   **Configuration SDL (Variables d'Environnement)**: La configuration correcte de `SDL_AUDIODRIVER='alsa'`, `SDL_AUDIODEV='hw:1'`, et `SDL_VIDEODRIVER='dummy'` dans `PygameAudioBackend.__init__` (et potentiellement lors des réinitialisations) est fondamentale pour le fonctionnement sur Raspberry Pi.
    *   **Initialisation Pygame (`PygameAudioBackend.initialize`)**: La séquence `pygame.mixer.init()` puis `pygame.init()` et la configuration de `MUSIC_END_EVENT` sont standards. La robustesse de cette initialisation, surtout après des erreurs, est clé.
    *   **Gestion des Erreurs Pygame (`@handle_pygame_error` et `_reinitialize_pygame` dans `PygameAudioBackend`)**: La capacité à détecter les erreurs "video system not initialized" et à tenter une réinitialisation de Pygame est une mesure de robustesse importante. Vérifier que les conditions de réinitialisation sont appropriées et que la réinitialisation elle-même est fiable.
    *   **Gestion de l'État de Lecture**: La synchronisation de l'état interne de `AudioPlayerWM8960` (ex: `_is_playing`, `_paused_position`) avec l'état réel de `pygame.mixer.music` (via `get_busy()`, `get_pos()`) est critique. Des désynchronisations peuvent mener à un comportement incorrect (ex: progression qui continue après arrêt). La méthode `_update_progress` dans `AudioPlayerWM8960` tente de gérer cela.
    *   **Fallback ALSA (`_fallback_to_alsa`)**: L'utilisation de `subprocess.Popen` pour `aplay`/`mpg123` est un bon filet de sécurité. S'assurer que les processus enfants sont correctement gérés (terminés lors d'un `stop` ou avant de jouer une nouvelle piste). La gestion de `self._alsa_process` doit être rigoureuse.
    *   **Gestion de la Fin de Piste**: Le callback `_handle_track_end` (de `BaseAudioPlayer`) est déclenché par `PygameAudioBackend.process_events` lorsque `MUSIC_END_EVENT` est reçu. La fiabilité de cette détection est essentielle pour l'enchaînement des pistes.
    *   **Accès Concurrents**: `_state_lock` (de `BaseAudioPlayer`) est utilisé pour protéger l'état. Vérifier son utilisation correcte dans toutes les méthodes modifiant ou lisant l'état partagé, surtout avec le thread de monitoring de progression.

### 4.1.3. Module Contrôles (`app/src/module/controles/`)

*   **`ControlesGPIO`**:
    *   **Utilisation de `gpiozero` et `LGPIOFactory`**: C'est une approche moderne pour les GPIO sur Raspberry Pi.
    *   **Callbacks et Threads**: `gpiozero` exécute ses callbacks (`when_pressed`, `when_released`, `when_activated`, `when_deactivated`) dans des threads séparés. La logique dans `_handle_rotary_state_change` utilise un `threading.Lock` (`self._lock`) pour protéger l'accès à `_rotary_states`, ce qui est correct.
    *   **Debounce**: `gpiozero.Button` a un `bounce_time` matériel. `_handle_rotary_state_change` implémente un debounce logiciel. Vérifier que ces valeurs de debounce sont appropriées pour éviter les rebonds ou les lectures manquées.
    *   **Logique de l'Encodeur Rotatif (`_handle_rotary_state_change`)**: L'algorithme de détection de direction basé sur les changements d'état de CLK et la valeur de DT est standard. S'assurer de sa robustesse face à des signaux bruités (le debounce aide ici).
    *   **Nettoyage (`cleanup`)**: La fermeture des dispositifs `gpiozero` (`device.close()`) est importante pour libérer les ressources GPIO.

## 4.2. Modules Critiques (Performance, Accès I/O, Traitement Temps Réel)

*   **`PlaylistController` (`app/src/core/playlist_controller.py`)**:
    *   **Gestion d'État Complexe**: Ce module gère de nombreux états (`_current_tag`, `_auto_pause_enabled`, `_last_manual_action_time`, etc.) et prend des décisions basées sur une combinaison de ces états et des événements entrants. La complexité de cette logique (Cas A-E) est un point d'audit majeur pour s'assurer qu'il n'y a pas de conditions de course, d'états imprévus ou de transitions incorrectes.
    *   **Interaction avec `NFCService` et `AudioPlayer`**: Les dépendances (parfois optionnelles à l'init) et les abonnements aux `Subject` RxPy doivent être gérés correctement.
    *   **Priorité des Actions Manuelles**: La logique utilisant `_last_manual_action_time` et `_manual_action_priority_window` pour ignorer les scans NFC après une action manuelle est importante pour l'UX.
    *   **Auto-Pause**: La gestion de `_auto_pause_enabled` et son interaction avec `handle_tag_absence` et le `_tag_monitor` (qui semble redondant ou un fallback) nécessite une vérification pour la cohérence.

*   **`NFCService` (`app/src/services/nfc_service.py`)**:
    *   **Modes d'Opération (Association vs Lecture)**: La distinction et la transition entre ces modes (`_association_mode`) sont critiques. La méthode `handle_tag_detected` contient la logique de branchement.
    *   **Communication Socket.IO**: L'émission d'événements vers le client (`self.socketio.emit`) doit être fiable et fournir des informations correctes. La gestion du `_sid` du client est importante.
    *   **Interaction avec `PlaylistService` pour Association**: La création d'une instance de `PlaylistService` à la volée dans `handle_tag_detected` pour persister l'association est un point à noter.
    *   **`force_redetect`**: L'appel à `_nfc_handler.tag_detection_manager.force_redetect()` après une association réussie est une astuce pour une transition fluide vers la lecture. Son timing et sa fiabilité sont importants.

*   **`PlaylistService` (`app/src/services/playlist_service.py`)**:
    *   **Synchronisation avec le Système de Fichiers (`sync_with_filesystem`)**:
        *   Cette opération peut être coûteuse en I/O, surtout avec de nombreuses playlists/pistes. L'utilisation de `threading.RLock` (`_sync_lock`) empêche les exécutions concurrentes.
        *   Les timeouts (`SYNC_TOTAL_TIMEOUT`, `SYNC_FOLDER_TIMEOUT`, `SYNC_OPERATION_TIMEOUT`) sont des mesures de sécurité importantes pour éviter que l'application ne se bloque.
        *   La logique de comparaison entre la base de données et le système de fichiers pour ajouter/mettre à jour les playlists et les pistes (`_update_existing_playlists`, `_add_new_playlists`, `update_playlist_tracks`) doit être correcte pour éviter la perte de données ou les incohérences.
    *   **Accès Concurrents**: Bien que `sync_with_filesystem` soit protégé par un verrou, d'autres opérations CRUD sur les playlists pourraient potentiellement interférer si elles ne sont pas également gérées avec soin au niveau des appels (ex: une API modifie une playlist pendant une synchro).

*   **Threads et `asyncio`**:
    *   L'application mélange `threading` (ex: `PlaylistService._sync_lock`, `ControlesGPIO._lock`, `BaseAudioPlayer._progress_monitoring_thread`) et `asyncio` (FastAPI, `ContainerAsync`, opérations NFC/Audio matérielles).
    *   La communication et la synchronisation entre ces deux mondes (si nécessaire) doivent être gérées avec précaution pour éviter les blocages ou les conditions de course. Par exemple, les callbacks RxPy ou GPIO (qui peuvent s'exécuter dans des threads) interagissant avec des objets gérés par `asyncio` nécessitent une attention particulière (ex: `asyncio.create_task` pour appeler des coroutines depuis un contexte synchrone). `NFCService._on_tag_subject` utilise `asyncio.create_task` correctement.

*   **Gestion des Ressources Matérielles**:
    *   Le nettoyage correct des ressources (fichiers, connexions GPIO, I2C, instances Pygame) dans les méthodes `cleanup` des différentes classes matérielles et gestionnaires est essentiel pour éviter les fuites de ressources ou les états instables après redémarrage.
