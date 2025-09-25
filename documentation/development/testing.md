# Testing Guide - The Open Music Box

## Overview

The Open Music Box uses comprehensive testing strategies across both backend (Python) and frontend (Vue.js/TypeScript) to ensure reliability, maintainability, and consistent behavior. This guide covers all testing approaches, tools, and best practices.

## Testing Philosophy

### Test-Driven Development (TDD)
- **Write tests first**: Tests define expected behavior before implementation
- **Red-Green-Refactor**: Fail → Pass → Improve cycle
- **Confidence in changes**: Tests enable safe refactoring and feature additions

### Test Pyramid Strategy
```
    /\
   /  \  E2E Tests (Few, Expensive, High-level)
  /____\
 /      \  Integration Tests (Some, Medium cost)
/________\  Unit Tests (Many, Fast, Isolated)
```

## Backend Testing (Python)

### Test Structure
```
tests/
├── unit/                    # Isolated component tests
│   ├── services/           # Service layer tests
│   ├── models/             # Data model tests
│   ├── routes/             # API endpoint tests
│   └── utils/              # Utility function tests
├── integration/            # Component interaction tests
│   ├── test_api_flows.py  # End-to-end API flows
│   ├── test_database.py   # Database integration
│   └── test_websocket.py  # WebSocket communication
├── fixtures/               # Test data and mocks
│   ├── sample_data.py     # Sample playlist/track data
│   ├── mock_hardware.py   # Hardware simulation
│   └── test_audio.py      # Audio file samples
└── conftest.py            # Pytest configuration
```

### Testing Tools

#### Core Testing Framework
```bash
# Install testing dependencies
pip install pytest pytest-asyncio pytest-cov pytest-mock

# Additional tools for advanced testing
pip install pytest-xdist pytest-benchmark pytest-clarity
```

#### Configuration (`pytest.ini`)
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --strict-markers
    --disable-warnings
    --tb=short
    -ra
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow-running tests
    hardware: Tests requiring hardware
```

### Unit Testing Examples

#### Service Layer Testing
```python
# tests/unit/services/test_playlist_service.py
import pytest
from unittest.mock import Mock, AsyncMock
from app.services.playlist_service import PlaylistService
from app.models.playlist import Playlist, PlaylistCreate

class TestPlaylistService:
    @pytest.fixture
    def mock_db_session(self):
        return Mock()

    @pytest.fixture
    def playlist_service(self, mock_db_session):
        return PlaylistService(mock_db_session)

    @pytest.mark.asyncio
    async def test_create_playlist_success(self, playlist_service, mock_db_session):
        # Arrange
        playlist_data = PlaylistCreate(title="Test Playlist", description="Test")
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        # Act
        result = await playlist_service.create_playlist(playlist_data)

        # Assert
        assert result.title == "Test Playlist"
        assert result.description == "Test"
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_playlist_duplicate_title(self, playlist_service, mock_db_session):
        # Arrange
        playlist_data = PlaylistCreate(title="Existing Playlist")
        mock_db_session.query().filter().first = AsyncMock(return_value=Mock())

        # Act & Assert
        with pytest.raises(DuplicatePlaylistError):
            await playlist_service.create_playlist(playlist_data)

    def test_playlist_validation(self):
        # Test data validation
        with pytest.raises(ValueError):
            PlaylistCreate(title="", description="Invalid empty title")

        with pytest.raises(ValueError):
            PlaylistCreate(title="A" * 256)  # Title too long
```

#### API Route Testing
```python
# tests/unit/routes/test_playlist_routes.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_create_playlist_endpoint(test_client: TestClient):
    # Arrange
    playlist_data = {"title": "New Playlist", "description": "Description"}

    with patch('app.services.playlist_service.PlaylistService.create_playlist') as mock_create:
        mock_create.return_value = Mock(id="123", title="New Playlist")

        # Act
        response = test_client.post("/api/playlists/", json=playlist_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["playlist"]["title"] == "New Playlist"
        mock_create.assert_called_once()

@pytest.mark.asyncio
async def test_create_playlist_invalid_data(test_client: TestClient):
    # Test validation error handling
    response = test_client.post("/api/playlists/", json={})

    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"
    assert "validation_error" in data["error_type"]
```

#### WebSocket Event Testing
```python
# tests/unit/services/test_state_manager.py
import pytest
from unittest.mock import AsyncMock, Mock
from app.services.state_manager import StateManager

class TestStateManager:
    @pytest.fixture
    def mock_socketio(self):
        return Mock()

    @pytest.fixture
    def state_manager(self, mock_socketio):
        return StateManager(mock_socketio)

    @pytest.mark.asyncio
    async def test_broadcast_player_state(self, state_manager, mock_socketio):
        # Arrange
        player_state = {"is_playing": True, "track_id": "123"}
        mock_socketio.emit = AsyncMock()

        # Act
        await state_manager.broadcast_state_change("state:player", player_state)

        # Assert
        mock_socketio.emit.assert_called_once()
        call_args = mock_socketio.emit.call_args
        assert call_args[0][0] == "state:player"  # Event name
        assert call_args[1]["room"] == "playlists"  # Room name

    @pytest.mark.asyncio
    async def test_client_subscription(self, state_manager):
        # Test room subscription management
        client_id = "client-123"
        room = "playlists"

        await state_manager.subscribe_client(client_id, room)

        subscribed_clients = state_manager.subscriptions.get_subscribed_clients(room)
        assert client_id in subscribed_clients
```

### Integration Testing

#### Database Integration
```python
# tests/integration/test_database.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_async_db_session
from app.models.playlist import Playlist
from app.services.playlist_service import PlaylistService

@pytest.mark.integration
class TestDatabaseIntegration:
    @pytest.fixture
    async def db_session(self):
        async for session in get_async_db_session():
            yield session

    @pytest.mark.asyncio
    async def test_playlist_crud_operations(self, db_session: AsyncSession):
        # Create
        playlist_service = PlaylistService(db_session)
        playlist = await playlist_service.create_playlist({
            "title": "Integration Test Playlist",
            "description": "Test Description"
        })
        assert playlist.id is not None

        # Read
        retrieved = await playlist_service.get_playlist(playlist.id)
        assert retrieved.title == "Integration Test Playlist"

        # Update
        updated = await playlist_service.update_playlist(
            playlist.id, {"title": "Updated Title"}
        )
        assert updated.title == "Updated Title"

        # Delete
        await playlist_service.delete_playlist(playlist.id)
        deleted = await playlist_service.get_playlist(playlist.id)
        assert deleted is None
```

#### API Flow Integration
```python
# tests/integration/test_api_flows.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.mark.integration
class TestPlaylistAPIFlow:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_complete_playlist_workflow(self, client: TestClient):
        # 1. Create playlist
        create_response = client.post("/api/playlists/", json={
            "title": "API Test Playlist",
            "description": "End-to-end test"
        })
        assert create_response.status_code == 201
        playlist_id = create_response.json()["data"]["playlist"]["id"]

        # 2. Get playlist
        get_response = client.get(f"/api/playlists/{playlist_id}")
        assert get_response.status_code == 200
        assert get_response.json()["data"]["playlist"]["title"] == "API Test Playlist"

        # 3. Update playlist
        update_response = client.put(f"/api/playlists/{playlist_id}", json={
            "title": "Updated API Test Playlist"
        })
        assert update_response.status_code == 200

        # 4. Delete playlist
        delete_response = client.delete(f"/api/playlists/{playlist_id}")
        assert delete_response.status_code == 200

        # 5. Verify deletion
        get_deleted_response = client.get(f"/api/playlists/{playlist_id}")
        assert get_deleted_response.status_code == 404
```

### Hardware Mocking

#### Audio System Mocking
```python
# tests/fixtures/mock_hardware.py
from unittest.mock import Mock, AsyncMock
from app.hardware.audio import AudioController

class MockAudioController(AudioController):
    def __init__(self):
        self.is_playing = False
        self.position_ms = 0
        self.volume = 50
        self.current_track = None

    async def play(self, track_path: str) -> bool:
        self.is_playing = True
        self.current_track = track_path
        return True

    async def pause(self) -> bool:
        self.is_playing = False
        return True

    async def get_position_ms(self) -> int:
        return self.position_ms

    async def seek(self, position_ms: int) -> bool:
        self.position_ms = position_ms
        return True
```

#### NFC Reader Mocking
```python
# tests/fixtures/mock_nfc.py
from unittest.mock import Mock
from app.hardware.nfc import NFCReader

class MockNFCReader(NFCReader):
    def __init__(self):
        self.available = True
        self.mock_tags = {}

    def is_available(self) -> bool:
        return self.available

    def read_tag(self) -> str:
        # Simulate tag reading
        return "mock-tag-id-123"

    def set_mock_tag(self, tag_id: str):
        self.mock_tags[tag_id] = True
```

### Performance Testing

#### Benchmark Testing
```python
# tests/performance/test_benchmarks.py
import pytest
from app.services.playlist_service import PlaylistService

@pytest.mark.benchmark
def test_playlist_creation_performance(benchmark):
    """Benchmark playlist creation speed"""
    def create_playlist():
        return PlaylistService.create_playlist({
            "title": "Benchmark Playlist",
            "description": "Performance test"
        })

    result = benchmark(create_playlist)
    assert result is not None

@pytest.mark.benchmark
def test_track_search_performance(benchmark, large_playlist):
    """Benchmark track search in large playlist"""
    def search_tracks():
        return large_playlist.search_tracks("test query")

    results = benchmark(search_tracks)
    assert len(results) >= 0
```

## Frontend Testing (Vue.js/TypeScript)

### Testing Tools

#### Core Framework
```bash
# Install testing dependencies
npm install --save-dev vitest @vue/test-utils jsdom
npm install --save-dev @vitest/ui @vitest/coverage-c8

# Component testing
npm install --save-dev @testing-library/vue @testing-library/jest-dom
```

#### Configuration (`vitest.config.ts`)
```typescript
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts']
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, './src')
    }
  }
})
```

### Component Testing

#### Basic Component Test
```typescript
// tests/components/AudioPlayer.test.ts
import { mount } from '@vue/test-utils'
import { describe, it, expect, vi } from 'vitest'
import AudioPlayer from '@/components/AudioPlayer.vue'
import { createPinia } from 'pinia'

describe('AudioPlayer', () => {
  const createWrapper = (props = {}) => {
    const pinia = createPinia()
    return mount(AudioPlayer, {
      props: {
        playerState: {
          is_playing: false,
          position_ms: 0,
          duration_ms: 180000,
          active_track: {
            id: '1',
            title: 'Test Song',
            artist: 'Test Artist'
          },
          ...props.playerState
        },
        ...props
      },
      global: {
        plugins: [pinia]
      }
    })
  }

  it('renders correctly with default props', () => {
    const wrapper = createWrapper()

    expect(wrapper.find('.audio-player').exists()).toBe(true)
    expect(wrapper.find('.track-title').text()).toBe('Test Song')
    expect(wrapper.find('.play-button').exists()).toBe(true)
  })

  it('shows pause button when playing', () => {
    const wrapper = createWrapper({
      playerState: { is_playing: true }
    })

    expect(wrapper.find('.pause-button').exists()).toBe(true)
    expect(wrapper.find('.play-button').exists()).toBe(false)
  })

  it('emits toggle event when play/pause clicked', async () => {
    const wrapper = createWrapper()

    await wrapper.find('.play-button').trigger('click')

    expect(wrapper.emitted('toggle-play-pause')).toHaveLength(1)
  })

  it('updates progress bar based on position', () => {
    const wrapper = createWrapper({
      playerState: {
        position_ms: 90000,  // 1.5 minutes
        duration_ms: 180000  // 3 minutes
      }
    })

    const progressBar = wrapper.find('.progress-bar')
    expect(progressBar.attributes('style')).toContain('width: 50%')
  })
})
```

#### Store Testing
```typescript
// tests/stores/serverStateStore.test.ts
import { setActivePinia, createPinia } from 'pinia'
import { describe, it, expect, beforeEach } from 'vitest'
import { useServerStateStore } from '@/stores/serverStateStore'

describe('Server State Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('initializes with default state', () => {
    const store = useServerStateStore()

    expect(store.playerState).toBeNull()
    expect(store.playlists).toEqual([])
    expect(store.isConnected).toBe(false)
  })

  it('updates player state correctly', () => {
    const store = useServerStateStore()
    const newPlayerState = {
      is_playing: true,
      active_track: { id: '1', title: 'Test Song' }
    }

    store.updatePlayerState(newPlayerState)

    expect(store.playerState).toEqual(newPlayerState)
  })

  it('handles WebSocket events correctly', () => {
    const store = useServerStateStore()
    const eventData = {
      event_type: 'state:player',
      data: { is_playing: true },
      server_seq: 123
    }

    store.handleStateEvent(eventData)

    expect(store.playerState.is_playing).toBe(true)
    expect(store.lastServerSequence).toBe(123)
  })
})
```

#### API Service Testing
```typescript
// tests/services/apiService.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { apiService } from '@/services/apiService'
import axios from 'axios'

// Mock axios
vi.mock('axios')
const mockedAxios = vi.mocked(axios)

describe('API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('playerApi', () => {
    it('toggles player successfully', async () => {
      const mockResponse = {
        data: {
          status: 'success',
          data: { is_playing: true }
        }
      }
      mockedAxios.post.mockResolvedValue(mockResponse)

      const result = await apiService.playerApi.togglePlayer()

      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/player/toggle',
        expect.any(Object)
      )
      expect(result.is_playing).toBe(true)
    })

    it('handles API errors gracefully', async () => {
      const mockError = {
        response: {
          status: 500,
          data: { status: 'error', message: 'Server error' }
        }
      }
      mockedAxios.post.mockRejectedValue(mockError)

      await expect(apiService.playerApi.togglePlayer()).rejects.toThrow('Server error')
    })
  })
})
```

### Integration Testing (Frontend)

#### Component Integration
```typescript
// tests/integration/PlaylistManagement.test.ts
import { mount } from '@vue/test-utils'
import { describe, it, expect, vi } from 'vitest'
import PlaylistContainer from '@/components/PlaylistContainer.vue'
import { createPinia } from 'pinia'
import { useServerStateStore } from '@/stores/serverStateStore'

describe('Playlist Management Integration', () => {
  it('integrates playlist creation with store updates', async () => {
    const pinia = createPinia()
    const wrapper = mount(PlaylistContainer, {
      global: {
        plugins: [pinia]
      }
    })

    const store = useServerStateStore()

    // Mock API call
    vi.spyOn(store, 'createPlaylist').mockResolvedValue({
      id: '1',
      title: 'New Playlist',
      tracks: []
    })

    // Trigger playlist creation
    await wrapper.find('.create-playlist-button').trigger('click')
    await wrapper.find('.playlist-title-input').setValue('New Playlist')
    await wrapper.find('.confirm-create-button').trigger('click')

    // Verify integration
    expect(store.createPlaylist).toHaveBeenCalledWith({
      title: 'New Playlist'
    })
  })
})
```

## E2E Testing (Cypress)

### Setup and Configuration

#### Installation
```bash
# Install Cypress
npm install --save-dev cypress

# Install additional plugins
npm install --save-dev @cypress/vue @cypress/code-coverage
```

#### Configuration (`cypress.config.ts`)
```typescript
import { defineConfig } from 'cypress'

export default defineConfig({
  e2e: {
    baseUrl: 'http://localhost:3000',
    supportFile: 'tests/e2e/support/e2e.ts',
    specPattern: 'tests/e2e/specs/**/*.cy.ts',
    video: true,
    screenshot: true
  },
  component: {
    devServer: {
      framework: 'vue',
      bundler: 'vite',
    },
    specPattern: 'tests/e2e/components/**/*.cy.ts'
  }
})
```

### E2E Test Examples

#### User Journey Testing
```typescript
// tests/e2e/specs/music-playback.cy.ts
describe('Music Playback Journey', () => {
  beforeEach(() => {
    cy.visit('/')
    cy.wait(1000) // Wait for app initialization
  })

  it('plays music from start to finish', () => {
    // 1. User sees playlists
    cy.get('[data-testid="playlist-container"]').should('be.visible')
    cy.get('[data-testid="playlist-item"]').should('have.length.greaterThan', 0)

    // 2. User clicks play on first playlist
    cy.get('[data-testid="playlist-item"]').first().within(() => {
      cy.get('[data-testid="play-button"]').click()
    })

    // 3. Player should appear and start playing
    cy.get('[data-testid="audio-player"]').should('be.visible')
    cy.get('[data-testid="pause-button"]').should('be.visible')
    cy.get('[data-testid="track-title"]').should('not.be.empty')

    // 4. User can control playback
    cy.get('[data-testid="pause-button"]').click()
    cy.get('[data-testid="play-button"]').should('be.visible')

    // 5. User can navigate tracks
    cy.get('[data-testid="next-button"]').click()
    cy.get('[data-testid="track-title"]').should('contain', 'Track 2')
  })

  it('handles WebSocket real-time updates', () => {
    // Open two browser tabs to test real-time sync
    cy.window().then((win) => {
      win.open('/', '_blank')
    })

    // Play music in first tab
    cy.get('[data-testid="play-button"]').first().click()

    // Verify both tabs show playing state
    cy.get('[data-testid="audio-player"]').should('be.visible')

    // Switch to second tab and verify sync
    cy.visit('/')
    cy.get('[data-testid="audio-player"]').should('be.visible')
    cy.get('[data-testid="pause-button"]').should('be.visible')
  })
})
```

#### File Upload Testing
```typescript
// tests/e2e/specs/file-upload.cy.ts
describe('File Upload Flow', () => {
  it('uploads music files successfully', () => {
    cy.visit('/')

    // Enable edit mode
    cy.get('[data-testid="edit-mode-toggle"]').click()

    // Create new playlist
    cy.get('[data-testid="create-playlist-button"]').click()
    cy.get('[data-testid="playlist-title-input"]').type('Cypress Test Playlist')
    cy.get('[data-testid="confirm-create-button"]').click()

    // Upload file to playlist
    const fileName = 'test-audio.mp3'
    cy.get('[data-testid="file-upload-zone"]').selectFile(`tests/fixtures/${fileName}`, {
      action: 'drag-drop'
    })

    // Verify upload progress
    cy.get('[data-testid="upload-progress"]').should('be.visible')

    // Wait for upload completion
    cy.get('[data-testid="track-item"]', { timeout: 30000 }).should('be.visible')
    cy.get('[data-testid="track-title"]').should('contain', 'test-audio')
  })
})
```

## Test Data Management

### Fixtures and Sample Data

#### Backend Test Data
```python
# tests/fixtures/sample_data.py
import uuid
from app.models.playlist import Playlist
from app.models.track import Track

def create_sample_playlist():
    return Playlist(
        id=str(uuid.uuid4()),
        title="Test Playlist",
        description="Sample playlist for testing",
        tracks=[
            create_sample_track("Track 1", 180000),
            create_sample_track("Track 2", 240000),
            create_sample_track("Track 3", 200000),
        ]
    )

def create_sample_track(title: str, duration_ms: int):
    return Track(
        id=str(uuid.uuid4()),
        title=title,
        filename=f"{title.lower().replace(' ', '_')}.mp3",
        duration_ms=duration_ms,
        file_path=f"/test/audio/{title.lower().replace(' ', '_')}.mp3"
    )

# Large dataset for performance testing
def create_large_playlist(track_count: int = 1000):
    tracks = [
        create_sample_track(f"Track {i}", 180000 + (i * 1000))
        for i in range(track_count)
    ]

    return Playlist(
        id=str(uuid.uuid4()),
        title=f"Large Playlist ({track_count} tracks)",
        description=f"Performance test playlist with {track_count} tracks",
        tracks=tracks
    )
```

#### Frontend Test Data
```typescript
// tests/fixtures/mockData.ts
export const mockPlayerState = {
  is_playing: false,
  state: 'stopped' as const,
  active_playlist_id: null,
  active_playlist_title: null,
  active_track_id: null,
  active_track: null,
  position_ms: 0,
  duration_ms: 0,
  track_index: 0,
  track_count: 0,
  can_prev: false,
  can_next: false,
  volume: 50,
  muted: false,
  server_seq: 1
}

export const mockPlaylist = {
  id: '1',
  title: 'Test Playlist',
  description: 'Mock playlist for testing',
  nfc_tag_id: null,
  tracks: [
    {
      id: '1',
      title: 'Test Song 1',
      filename: 'test1.mp3',
      duration_ms: 180000,
      file_path: '/test/test1.mp3',
      artist: 'Test Artist',
      play_count: 0,
      created_at: '2025-01-01T00:00:00Z',
      server_seq: 1
    },
    {
      id: '2',
      title: 'Test Song 2',
      filename: 'test2.mp3',
      duration_ms: 240000,
      file_path: '/test/test2.mp3',
      artist: 'Test Artist',
      play_count: 0,
      created_at: '2025-01-01T00:00:00Z',
      server_seq: 2
    }
  ],
  track_count: 2,
  created_at: '2025-01-01T00:00:00Z',
  server_seq: 1,
  playlist_seq: 1
}
```

## Test Automation and CI/CD

### GitHub Actions Workflow
```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.11]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run unit tests
      run: pytest tests/unit/ -v --cov=app --cov-report=xml

    - name: Run integration tests
      run: pytest tests/integration/ -v

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  frontend-tests:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: front/package-lock.json

    - name: Install dependencies
      run: |
        cd front
        npm ci

    - name: Run unit tests
      run: |
        cd front
        npm run test -- --coverage

    - name: Run type checking
      run: |
        cd front
        npm run type-check

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [backend-tests, frontend-tests]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Start backend
      run: |
        pip install -r requirements.txt
        python -m uvicorn app.main:app --host 127.0.0.1 --port 5004 &

    - name: Start frontend
      run: |
        cd front
        npm ci
        npm run build
        npm run preview -- --port 3000 &

    - name: Wait for services
      run: |
        npx wait-on http://localhost:5004/api/health
        npx wait-on http://localhost:3000

    - name: Run E2E tests
      run: |
        cd front
        npx cypress run

    - name: Upload E2E artifacts
      uses: actions/upload-artifact@v3
      if: failure()
      with:
        name: cypress-screenshots
        path: front/cypress/screenshots
```

## Testing Best Practices

### Test Organization
- **One assertion per test**: Clear test failure diagnosis
- **Descriptive test names**: `test_create_playlist_with_duplicate_title_fails`
- **AAA pattern**: Arrange, Act, Assert
- **Test independence**: Each test can run in isolation

### Mock Strategy
- **Mock external dependencies**: Database, network calls, hardware
- **Don't mock what you own**: Test real business logic
- **Use dependency injection**: Makes mocking easier
- **Mock at the boundary**: Mock at service layer, not deep internals

### Performance Testing
- **Benchmark critical paths**: Playlist loading, audio processing
- **Load testing**: Simulate multiple concurrent users
- **Memory profiling**: Check for leaks in long-running operations
- **Database performance**: Query optimization and indexing

### Security Testing
- **Input validation**: Test malformed data handling
- **Authentication testing**: Verify access control
- **SQL injection prevention**: Test database query safety
- **File upload security**: Verify file type validation

This comprehensive testing guide ensures robust, reliable software with confidence in changes and new feature development.