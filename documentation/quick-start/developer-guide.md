# Quick Start Guide - Developers

## Get Development Environment Running in 10 Minutes

This guide gets you from zero to running development environment quickly, so you can start contributing to The Open Music Box project.

## Prerequisites Check (2 minutes)

### Required Software
```bash
# Check Python version (3.9+ required)
python3 --version

# Check Node.js version (16+ required)
node --version

# Check Git
git --version

# Install missing tools
# macOS: brew install python3 node git
# Ubuntu: sudo apt-get install python3 python3-pip nodejs npm git
# Windows: Use chocolatey or download installers
```

### Hardware for Testing
- 💻 **Development machine**: macOS/Linux/Windows
- 🎵 **Audio output**: Speakers or headphones
- 📱 **Modern browser**: Chrome, Firefox, Safari, or Edge
- 🏷️ **NFC tags** (optional): For testing NFC features

## Step 1: Clone and Setup (3 minutes)

### Get the Code
```bash
# Clone repository
git clone https://github.com/theopenmusicbox/tomb-rpi.git
cd tomb-rpi

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# OR: venv\Scripts\activate  # Windows

# Install Python dependencies
pip install -r requirements-dev.txt
```

### Quick Environment Setup
```bash
# Copy development configuration
cp config/.env.example config/.env
```

## Step 2: Start Backend (2 minutes)

### Launch Development Server
```bash
# From project root directory
source venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 5004 --reload
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:5004 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Application startup complete
```

### Verify Backend
```bash
# Test API health (new terminal)
curl http://localhost:5004/api/health

# Expected: {"status": "ok", "timestamp": 1640995200}

# View API documentation
open http://localhost:5004/docs  # Swagger UI
```

## Step 3: Start Frontend (3 minutes)

### Install and Launch
```bash
# Open new terminal, navigate to frontend
cd front

# Install Node.js dependencies
npm install

# Start development server
npm run dev
```

**Expected Output:**
```
VITE v4.0.0  ready in 800ms

➜  Local:   http://localhost:3000/
➜  Network: http://192.168.1.100:3000/
➜  press h to show help
```

### Test Full Stack
1. **Open browser**: http://localhost:3000
2. **Should see**: Music Box interface with sample playlists
3. **Test playback**: Click play on any playlist
4. **Check real-time**: Open multiple browser tabs - changes sync automatically

## Development Workflow

### Code Structure Overview
```
tomb-rpi/
├── back/                   # Python backend
│   ├── app/
│   │   ├── main.py        # FastAPI application entry
│   │   ├── routes/        # HTTP API endpoints
│   │   ├── services/      # Business logic services
│   │   ├── models/        # Data models (Pydantic)
│   │   └── db/            # Database layer
│   └── tests/             # Backend tests
├── front/                  # Vue.js frontend
│   ├── src/
│   │   ├── components/    # Vue components
│   │   ├── services/      # API clients
│   │   ├── stores/        # Pinia state management
│   │   └── views/         # Page components
│   └── tests/             # Frontend tests
├── config/                 # Configuration files
├── scripts/               # Utility scripts
└── docs/                  # Documentation
```

### Making Your First Change

### Development Commands

#### Backend Development
```bash
# Run with hot reload

# Run tests

# Code formatting
```

#### Frontend Development
```bash
# Development server

# Code quality

# Testing

```

## Common Development Tasks

### Adding a New Feature

#### 1. Backend Service
```python
# app/services/my_feature_service.py

```

#### 2. API Route
```python
# app/routes/my_feature_routes.py

```

#### 3. Frontend Service
```typescript
// src/services/myFeatureService.ts

```

#### 4. Vue Component
```vue
<!-- src/components/MyFeature.vue -->

```

### Testing Your Changes

#### Backend Testing
```python

```

#### Frontend Testing
```typescript
// tests/components/MyFeature.test.ts

```

### WebSocket Event Development

#### Backend: Emit Events
```python
# In your service

```

#### Frontend: Listen to Events
```typescript
// In your Vue component

```

## Debugging Tips

### Backend Debugging
```python
# Add debug logging

```

### Frontend Debugging
```javascript
// Console logging

```

### Common Issues

#### Backend Won't Start
```bash
# Check Python version
python3 --version

# Verify virtual environment
which python  # Should be in venv/

# Check dependencies
pip list | grep fastapi

# Check port availability
netstat -tulnp | grep 5004
```

#### Frontend Won't Start
```bash
# Check Node version
node --version  # Should be 16+

# Clear node_modules if needed
rm -rf node_modules package-lock.json
npm install

# Check for port conflicts

```

#### API Calls Fail
```javascript
// Check CORS configuration
// Backend config/.env should have:
CORS_ALLOW_ORIGINS=["http://localhost:5004"]

// Check network tab in browser DevTools
// Look for 404, 500, CORS errors
```

## Ready to Contribute?

### Before Submitting Code
```bash
# Format and lint everything
black app/ tests/
isort app/ tests/
flake8 app/ tests/

cd front/
npm run lint:fix
npm run type-check

# Run all tests
pytest
npm run test

# Commit with good message
git add .
git commit -m "feat(api): add new feature endpoint

- Add MyFeatureService with data processing
- Add API route with validation
- Add frontend integration with real-time updates
- Include comprehensive tests"
```

### Submission Checklist
- [ ] **Code formatted** with black/prettier
- [ ] **Tests written** and passing
- [ ] **Type hints added** (Python) / **TypeScript types** (Frontend)
- [ ] **Documentation updated** if needed
- [ ] **Commit message** follows conventional format
- [ ] **No console.log** statements in production code
- [ ] **API documentation** updated if endpoints changed

You're now ready to contribute to The Open Music Box! 🎵

---

*Next: Check out our [Architecture Overview](../architecture/overview.md) to understand the system design, or browse [API Documentation](../api/http-endpoints.md) for detailed endpoint information.*