# 📊 Rapport des Changements Structurels - main vs refactor/fix-ddd-violations

## 🎯 Résumé Exécutif

La branche `refactor/fix-ddd-violations` contient une refactorisation majeure pour implémenter une architecture Domain-Driven Design (DDD) stricte. Cette refactorisation a introduit des changements structurels importants qui ont cassé le fonctionnement audio sur Raspberry Pi.

## 🔄 Changements Majeurs Identifiés

### 1. Migration des Protocols (❗ IMPACT CRITIQUE)

**Sur `main`:**
```
back/app/src/domain/audio/protocols/
├── audio_backend_protocol.py
├── audio_engine_protocol.py
├── event_bus_protocol.py
├── playlist_manager_protocol.py
└── state_manager_protocol.py
```

**Sur `refactor/fix-ddd-violations`:**
```
back/app/src/domain/protocols/ (niveau domain global)
├── audio_backend_protocol.py
├── audio_engine_protocol.py
├── event_bus_protocol.py
├── persistence_service_protocol.py (renommé de database_service_protocol.py)
└── (playlist_manager_protocol.py SUPPRIMÉ)
```

### 2. Suppression du PlaylistManager du Domain Layer

**Sur `main`:**
- `PlaylistManager` était dans le domain layer : `domain/audio/playlist/playlist_manager.py`
- `AudioEngine` avait une dépendance directe sur `PlaylistManagerProtocol`
- La factory créait un système complet avec PlaylistManager intégré

**Sur `refactor/fix-ddd-violations`:**
- `PlaylistManager` complètement supprimé du domain layer
- `AudioEngine` n'a plus de référence au PlaylistManager
- Gestion des playlists déléguée aux services d'application

### 3. Déplacement du UnifiedController

**Sur `main`:**
```
back/app/src/domain/controllers/unified_controller.py
```

**Sur `refactor/fix-ddd-violations`:**
```
back/app/src/application/controllers/unified_controller.py
```

### 4. Changements dans WM8960AudioBackend

#### Device Detection
**Sur `main`:**
```python
# Utilisation simple de plughw
device = f"plughw:{card_part},0"
```

**Sur `refactor/fix-ddd-violations` (avant fix):**
```python
# Tentative d'utiliser dmix pour partage
device = "default"  # ou "dmix:CARD=wm8960soundcard,DEV=0"
```

**Après notre fix d'aujourd'hui:**
```python
# Retour à l'accès hardware direct
device = "plughw:wm8960soundcard,0"
```

### 5. Architecture des Imports et Dépendances

**Sur `main`:**
- Imports directs depuis `domain/audio/protocols/`
- PlaybackSubject depuis `app.src.services.notification_service`
- Couplage fort entre domain et services

**Sur `refactor/fix-ddd-violations`:**
- Imports depuis `domain/protocols/` (niveau supérieur)
- PlaybackNotifierProtocol depuis `domain/protocols/notification_protocol`
- Découplage strict entre les couches

## 🔍 Analyse des Problèmes Audio

### Problème Principal Identifié

La refactorisation DDD a introduit plusieurs changements qui ont perturbé l'audio:

1. **Suppression du PlaylistManager** - L'AudioEngine ne peut plus gérer directement les playlists
2. **Migration des protocols** - Changement des chemins d'import et des interfaces
3. **Device Selection Strategy** - Tentative d'utiliser des devices partagés (dmix) au lieu de l'accès hardware direct

### État Actuel après Fixes

✅ **Fixed:** Device selection revenu à `plughw:wm8960soundcard,0`
✅ **Fixed:** AudioEngine avec fallback pour lecture directe sans PlaylistManager
✅ **Fixed:** Cleanup ALSA propre avec libération des variables SDL
❌ **Problème Restant:** Pygame s'initialise mais n'envoie pas d'audio réel au hardware

## 📝 Travail Effectué Aujourd'hui

### 1. Fix du Device Selection
- Modifié `_detect_wm8960_device()` pour utiliser `plughw:` au lieu de `dmix:`
- Supprimé les tentatives d'utiliser des devices partagés
- Retour à l'accès hardware direct comme sur `main`

### 2. Scripts de Test Créés
- `test_wm8960_pygame_fix.py` - Test complet de l'intégration pygame
- `test_wm8960_resource_release.py` - Test de libération des ressources ALSA
- `debug_pygame_wm8960.py` - Debug étape par étape
- `debug_wm8960_detailed.py` - Diagnostic détaillé

### 3. Tests Unitaires
- ✅ 99 tests passent
- ✅ Pas de régression introduite

## 🚨 Problème Racine Suspecté

Basé sur l'analyse, le problème semble être lié à:

1. **Changement d'Architecture AudioEngine**
   - Sur `main`: AudioEngine → PlaylistManager → Backend
   - Sur `refactor`: AudioEngine → Backend directement

2. **Initialisation pygame**
   - Le changement d'architecture pourrait affecter l'ordre d'initialisation
   - Les variables d'environnement SDL pourraient ne pas être configurées au bon moment

3. **Context de Thread/Async**
   - La refactorisation a changé certains appels async en sync
   - Possible problème de contexte thread avec pygame

## 🔧 Prochaines Étapes Recommandées

1. **Comparer l'initialisation complète** entre `main` et `refactor`
2. **Tracer l'ordre exact des appels** pygame.mixer.init()
3. **Vérifier les différences de configuration SDL**
4. **Tester avec l'architecture PlaylistManager restaurée temporairement**

## 📌 État Git Actuel

```bash
Branch: refactor/fix-ddd-violations
Commits depuis main: 21 commits
Fichiers modifiés: 100+ fichiers
```

## ⚠️ Note Importante

La branche `main` **FONCTIONNE** sur Raspberry Pi avec audio.
La branche `refactor/fix-ddd-violations` **NE FONCTIONNE PAS** malgré les fixes appliqués.

Le problème est structurel et lié à la refactorisation DDD, pas seulement à la configuration des devices ALSA.