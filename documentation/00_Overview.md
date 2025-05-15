# 0. Vue d’ensemble de l'application The Open Music Box (Backend)

## 0.1. Objectif principal de l’application

L'application "The Open Music Box" (partie backend) a pour objectif principal de permettre la lecture de playlists musicales déclenchée par la détection de tags NFC. Chaque tag NFC peut être associé à une playlist spécifique. Lorsqu'un tag est scanné, la playlist correspondante est chargée et jouée. L'application est conçue pour fonctionner sur un Raspberry Pi en environnement de production, utilisant du matériel réel (lecteur NFC, carte son WM8960, contrôles physiques GPIO), et sur des machines de développement (comme macOS) avec des simulations (mocks) de ce matériel.

Le backend expose une API REST pour la gestion des playlists, l'association des tags NFC, et le contrôle de la lecture, ainsi qu WebSocket (Socket.IO) pour des mises à jour d'état en temps réel vers une interface utilisateur frontend.

## 0.2. Fonctionnalités majeures

Le backend de The Open Music Box offre les fonctionnalités majeures suivantes :

1.  **Gestion des Playlists :**
    *   Création, suppression de playlists.
    *   Récupération de la liste des playlists et des détails d'une playlist spécifique.
    *   Synchronisation automatique des playlists stockées en base de données avec les fichiers audio présents dans un dossier d'upload (`uploads/`). Les nouvelles playlists (dossiers) sont ajoutées, et les pistes des playlists existantes sont mises à jour.
    *   Support de divers formats audio (MP3, OGG, WAV, M4A, FLAC, AAC).

2.  **Gestion des Tags NFC :**
    *   Association d'un tag NFC unique à une playlist.
    *   Dissociation d'un tag NFC d'une playlist.
    *   Détection de tags NFC via un lecteur matériel (PN532 via I2C en production) ou simulé.

3.  **Lecture Audio :**
    *   Lecture de playlists déclenchée par le scan du tag NFC associé.
    *   Contrôles de lecture basiques : play (implicite au scan), pause, reprise, arrêt, volume, piste suivante, piste précédente.
    *   Gestion de l'état de lecture (en cours, en pause, arrêté, terminé).
    *   Support matériel pour la carte son WM8960 sur Raspberry Pi, utilisant Pygame comme moteur audio principal, avec un fallback possible vers des commandes ALSA (`aplay`/`mpg123`).
    *   Simulation de la lecture audio pour les environnements de développement.

4.  **Contrôles Physiques (GPIO) :**
    *   Prise en charge de boutons physiques et d'encodeurs rotatifs connectés aux pins GPIO du Raspberry Pi.
    *   Actions typiques : piste suivante/précédente, volume haut/bas, play/pause.
    *   Simulation des contrôles pour les environnements de développement.

5.  **Communication en Temps Réel :**
    *   Utilisation de Socket.IO pour notifier une interface frontend des changements d'état (ex: statut NFC, état de la lecture, progression de la piste).

6.  **API REST :**
    *   Endpoints pour gérer les playlists (CRUD).
    *   Endpoints pour gérer les associations NFC (associer, observer).
    *   Endpoints pour contrôler la lecture à distance.
    *   Endpoints système (ex: état de santé, configuration).

7.  **Configuration Flexible :**
    *   Gestion des configurations via des fichiers `.env` et des classes de configuration spécifiques pour les environnements de production (`StandardConfig`), de développement (`DevConfig`), et de test (`TestConfig`).
    *   Utilisation de "factories" pour charger la configuration et les implémentations matérielles appropriées (réelles ou mocks) en fonction de l'environnement.

8.  **Téléchargement YouTube (Fonctionnalité Secondaire) :**
    *   Endpoints permettant de télécharger des vidéos/playlists YouTube et de les convertir en playlists audio locales.

L'architecture est conçue pour être modulaire, avec une séparation claire entre la logique métier (services), l'accès aux données (repository), la gestion du matériel (modules NFC, audio, contrôles), et l'interface web (routes FastAPI).
