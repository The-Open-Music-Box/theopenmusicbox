# Development Environment Setup

## Overview

This guide helps developers set up a local development environment for The Open Music Box, including backend Python services, frontend Vue.js application, and optional hardware simulation.

## Prerequisites

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | macOS 10.15+, Ubuntu 20.04+, Windows 10+ | Latest stable versions |
| **Python** | 3.9+ | 3.11+ |
| **Node.js** | 16+ | 18+ LTS |
| **RAM** | 8GB | 16GB+ |
| **Storage** | 5GB free space | 10GB+ |

### Required Tools

```bash
# macOS (using Homebrew)
brew install python3 node git sqlite3 ffmpeg

# Ubuntu/Debian
sudo apt-get install python3 python3-pip nodejs npm git sqlite3 ffmpeg

# Windows (using Chocolatey)
choco install python nodejs git sqlite ffmpeg
```

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/theopenmusicbox/tomb-rpi.git
cd tomb-rpi
```

### 2. Backend Setup

```bash
# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate     # Windows

# Install Python dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development tools
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd front

# Install Node.js dependencies
npm install

# Install development tools
npm install -g @vue/cli typescript
```

### 4. Environment Configuration

```bash
# Copy environment template
cp config/.env.example config/.env

# Edit configuration for development
nano config/.env  # or your preferred editor
```

**Development Configuration:**
```bash
# Development Environment
ENVIRONMENT=development
DEBUG=true

# Database
DATABASE_URL="sqlite:///data/music_dev.db"

# Network
HOST="127.0.0.1"
PORT=5004
FRONTEND_URL="http://localhost:3000"

# Audio Backend (for development)
AUDIO_BACKEND="dummy"  # Simulates audio without hardware

# Hardware Simulation
NFC_ENABLED=false      # Enable if you have NFC hardware
GPIO_ENABLED=false     # Enable if running on Raspberry Pi

# File Storage
UPLOAD_DIR="data/uploads"
MAX_UPLOAD_SIZE=100

# Development Features
HOT_RELOAD=true
CORS_ALLOW_ALL=true

# Logging
LOG_LEVEL="DEBUG"
LOG_TO_FILE=true
```

### 5. Database Setup

```bash
# Initialize development database
python -c "from app.db.database import init_db; init_db()"

# Run migrations (if any)
python -c "from app.db.migrations import run_migrations; run_migrations()"

# Optional: Load sample data
python scripts/load_sample_data.py
```

## Development Workflow

### Backend Development

#### Starting the Backend Server

```bash
# Activate virtual environment
source venv/bin/activate

# Start FastAPI development server with hot reload
python -m uvicorn app.main:app --host 127.0.0.1 --port 5004 --reload

# OR use the development script
python run_dev.py
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:5004
INFO:     Application startup complete
INFO:     StateManager initialized with 4 components
INFO:     TrackProgressService scheduled for background execution
```

#### API Documentation

- **Swagger UI**: http://localhost:5004/docs
- **ReDoc**: http://localhost:5004/redoc
- **OpenAPI JSON**: http://localhost:5004/openapi.json

#### Backend Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_player_service.py -v

# Run integration tests
pytest tests/integration/ -v

# Run tests with live reload
ptw -- tests/
```

### Frontend Development

#### Starting the Frontend Server

```bash
# Navigate to frontend directory
cd front

# Start development server with hot reload
npm run dev

# OR start with specific configuration
npm run dev -- --host 0.0.0.0 --port 3000
```

**Expected Output:**
```
VITE ready in 800ms

➜  Local:   http://localhost:3000/
➜  Network: http://192.168.1.100:3000/
```

#### Frontend Development Commands

```bash
# Development server
npm run dev              # Start dev server with hot reload
npm run build            # Production build
npm run preview          # Preview production build

# Code quality
npm run lint             # ESLint checking
npm run lint:fix         # Fix linting issues
npm run type-check       # TypeScript checking

# Testing
npm run test             # Run unit tests
npm run test:watch       # Run tests in watch mode
npm run test:coverage    # Run tests with coverage
```

#### Frontend Testing

```bash
# Unit tests with Vitest
npm run test

# Component testing
npm run test -- --ui

# E2E tests (if configured)
npm run test:e2e
```

## Development Tools

### Code Quality Tools

#### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

**Pre-commit Configuration** (`.pre-commit-config.yaml`):
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/isort
    rev: 5.10.1
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v2.6.2
    hooks:
      - id: prettier
        files: \.(js|ts|vue|css|md)$
```

#### Python Tools

```bash
# Code formatting
black app/ tests/

# Import sorting
isort app/ tests/

# Linting
flake8 app/ tests/

# Type checking
mypy app/

# Documentation checking
pydocstyle app/
```

#### TypeScript/Vue Tools

```bash
# Linting
npm run lint

# Type checking
npm run type-check

# Formatting
npm run format

# Vue component analysis
vue-tsc --noEmit
```

### Database Management

#### Development Database Operations

```bash
# Reset database
rm data/music_dev.db
python -c "from app.db.database import init_db; init_db()"

# View database schema
sqlite3 data/music_dev.db ".schema"

# Query database
sqlite3 data/music_dev.db "SELECT * FROM playlists LIMIT 5;"

# Database migrations
python -m app.db.migrations.create_migration "add_new_field"
python -m app.db.migrations.run_migrations
```

#### Sample Data Loading

```bash
# Load development sample data
python scripts/load_sample_data.py

# Load specific test scenarios
python scripts/load_sample_data.py --scenario large_playlists
python scripts/load_sample_data.py --scenario nfc_associations
```

### Hardware Simulation

#### Audio Backend Simulation

The `dummy` audio backend simulates audio playback for development:

```python
# config/.env
AUDIO_BACKEND="dummy"  # No actual audio playback, logs only
```

#### NFC Simulation

```bash
# Enable NFC simulation
python scripts/simulate_nfc.py --tag-id "test-tag-001" --playlist-id "uuid-here"
```

#### GPIO Simulation

```bash
# Simulate button presses
python scripts/simulate_gpio.py --button play_pause
python scripts/simulate_gpio.py --encoder volume --value 75
```

## Development Debugging

### Backend Debugging

#### Using Python Debugger

```python
# Add to code for debugging
import pdb; pdb.set_trace()

# OR use ipdb for enhanced debugging
import ipdb; ipdb.set_trace()
```

#### VS Code Debug Configuration

`.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI Debug",
      "type": "python",
      "request": "launch",
      "program": "-m",
      "args": ["uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "5004", "--reload"],
      "console": "integratedTerminal",
      "envFile": "${workspaceFolder}/config/.env",
      "cwd": "${workspaceFolder}"
    }
  ]
}
```

#### Logging Configuration

```python
# Enhanced logging for development
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Component-specific logging
logger = logging.getLogger(__name__)
logger.debug("Detailed debug information")
```

### Frontend Debugging

#### Vue DevTools

```bash
# Install Vue DevTools browser extension
# Chrome: Vue.js devtools from Chrome Web Store
# Firefox: Vue.js devtools from Firefox Add-ons
```

#### Browser Developer Tools

```javascript
// Add to components for debugging
console.log('Component data:', this.$data);
console.log('Component props:', this.$props);

// Debug reactive refs
import { ref, watch } from 'vue';
const debugRef = ref(null);
watch(debugRef, (newVal) => console.log('Changed:', newVal), { deep: true });
```

#### Network Debugging

```javascript
// Log all API calls
import axios from 'axios';

axios.interceptors.request.use(request => {
  console.log('API Request:', request);
  return request;
});

axios.interceptors.response.use(
  response => {
    console.log('API Response:', response);
    return response;
  },
  error => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);
```

## Performance Development

### Backend Performance

#### Profiling

```bash
# Install profiling tools
pip install py-spy memory-profiler line-profiler

# Profile CPU usage
py-spy record -o profile.svg -- python -m uvicorn app.main:app --host 127.0.0.1 --port 5004

# Profile memory usage
python -m memory_profiler app/main.py
```

#### Database Query Analysis

```python
# Enable SQL query logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

### Frontend Performance

#### Bundle Analysis

```bash
# Analyze bundle size
npm run build -- --analyze

# Check bundle composition
npx vite-bundle-analyzer dist/
```

#### Performance Monitoring

```javascript
// Add performance marks
performance.mark('component-start');
// ... component code ...
performance.mark('component-end');
performance.measure('component-duration', 'component-start', 'component-end');
```

## Testing Strategies

### Backend Testing

#### Test Structure

```
tests/
├── unit/           # Unit tests for individual components
├── integration/    # Integration tests for service interactions
├── fixtures/       # Test data and mocks
└── conftest.py    # Pytest configuration
```

#### Test Examples

```python
# Unit test example
def test_playlist_creation(db_session):
    playlist = create_playlist(title="Test Playlist")
    assert playlist.title == "Test Playlist"
    assert playlist.track_count == 0

# Integration test example
@pytest.mark.asyncio
async def test_player_api_toggle(test_client):
    response = await test_client.post("/api/player/toggle")
    assert response.status_code == 200
    data = response.json()
    assert "is_playing" in data
```

### Frontend Testing

#### Component Tests

```javascript
// Component test example
import { mount } from '@vue/test-utils';
import AudioPlayer from '@/components/AudioPlayer.vue';

test('AudioPlayer renders correctly', () => {
  const wrapper = mount(AudioPlayer, {
    props: { playerState: mockPlayerState }
  });

  expect(wrapper.find('.play-button').exists()).toBe(true);
});
```

#### API Mocking

```javascript
// Mock API responses for testing
import { vi } from 'vitest';

vi.mock('@/services/apiService', () => ({
  playerApi: {
    togglePlayer: vi.fn().mockResolvedValue(mockPlayerState)
  }
}));
```

## Continuous Integration

### GitHub Actions Workflow

`.github/workflows/test.yml`:
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run tests
        run: pytest --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

This development environment setup provides a solid foundation for contributing to The Open Music Box project with proper testing, debugging, and development workflow tools.