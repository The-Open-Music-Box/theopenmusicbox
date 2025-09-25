# The Open Music Box - Documentation

*NFC-enabled music player system designed for children*

## 🎵 What is The Open Music Box?

The Open Music Box is an open-source, NFC-enabled music player built on Raspberry Pi. It combines tactile interaction (NFC tags) with modern web interface capabilities, creating an intuitive music experience for children while providing comprehensive management tools for parents.

## 📚 Documentation Index

### 🚀 Getting Started
- **[Quick Start - Users](quick-start/user-guide.md)** - Get your music box running in 15 minutes
- **[Quick Start - Developers](quick-start/developer-guide.md)** - Set up development environment
- **[Hardware Purchase Guide](hardware/purchase-guide.md)** - Complete shopping list with pricing

### 🏗️ Architecture & Development
- **[Architecture Overview](architecture/overview.md)** - System architecture and design patterns
- **[Backend Services](architecture/backend-services.md)** - Domain-driven backend architecture
- **[Frontend Architecture](architecture/frontend-components.md)** - Vue.js reactive frontend
- **[Business Logic](architecture/business-logic.md)** - Core application workflows

### 🌐 API & Integration
- **[HTTP API Reference](api/http-endpoints.md)** - REST API endpoints and schemas
- **[WebSocket Events](api/websocket-events.md)** - Real-time communication patterns
- **[Error Handling](api/error-handling.md)** - Standardized error responses

### 🚀 Deployment & Hardware
- **[Raspberry Pi Deployment](deployment/raspberry-pi.md)** - Production deployment guide
- **[Development Setup](deployment/development.md)** - Local development environment
- **[Hardware Assembly](hardware/assembly-guide.md)** - Step-by-step hardware setup

### 🎨 Design & Development Standards
- **[UI/UX Design System](ui-design/theme-guide.md)** - Colors, typography, and components
- **[Code Style Guide](development/code-style.md)** - Python/TypeScript coding standards
- **[Testing Guide](development/testing.md)** - Test strategies and frameworks

## 🎯 Core Features

### 🎶 Music Playback
- **Multi-format support**: MP3, FLAC, WAV, and more
- **Playlist management**: Create, organize, and manage music collections
- **Real-time controls**: Play, pause, seek, volume control
- **Cross-device sync**: State synchronization across all connected clients

### 🔖 NFC Integration
- **Tag association**: Link NFC tags to specific playlists
- **Instant playback**: Scan tag to start music immediately
- **Conflict handling**: Override existing associations safely
- **Session management**: Secure association workflow

### 🌐 Web Interface
- **Responsive design**: Works on desktop, tablet, and mobile
- **Real-time updates**: Live synchronization via WebSocket
- **File management**: Drag-and-drop upload with progress tracking
- **Dual modes**: Normal playback and edit mode for content management

### 📱 Modern Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend** | FastAPI + Python | HTTP API and business logic |
| **Frontend** | Vue.js 3 + TypeScript | Reactive user interface |
| **Real-time** | Socket.IO | WebSocket communication |
| **Database** | SQLite | Local data persistence |
| **Hardware** | Raspberry Pi | Edge computing platform |
| **Audio** | WM8960 HAT | High-quality audio output |

## 🚧 System Requirements

### Hardware Requirements
- **Minimum**: Raspberry Pi Zero 2W, 8GB microSD, basic audio output
- **Recommended**: Raspberry Pi 4B, 32GB microSD, WM8960 Audio HAT
- **Optional**: NFC reader (RC522), physical buttons, LED indicators, battery pack

### Software Requirements
- **OS**: Raspberry Pi OS (64-bit recommended)
- **Python**: 3.9+ with pip
- **Node.js**: 16+ for frontend development
- **Storage**: 4GB+ available space

## 🎪 Architecture Highlights

### Server-Authoritative Pattern
- **Single source of truth**: Backend maintains all authoritative state
- **Real-time sync**: Changes broadcast immediately to all clients
- **Conflict resolution**: Server state always takes precedence
- **Event sequencing**: Ordered updates prevent race conditions

### Domain-Driven Design
- **Clean architecture**: Separation of concerns across layers
- **Business logic isolation**: Core domain rules independent of infrastructure
- **Dependency inversion**: Protocols define interfaces, not implementations
- **Testable design**: Pure domain models with injected dependencies

### Performance Features
- **Chunked uploads**: Large files uploaded efficiently
- **Smart caching**: Intelligent client-side caching with TTL
- **Position streaming**: 200ms position updates for smooth playback
- **Lazy loading**: On-demand content loading for optimal performance

## 📊 Project Status

### ✅ Completed Features
- [x] Complete NFC tag association system
- [x] Real-time playlist management
- [x] Chunked file upload with progress tracking
- [x] YouTube integration with download progress
- [x] Server-authoritative player state
- [x] Responsive web interface
- [x] Hardware audio integration (WM8960)

### 🔄 In Development
- [ ] Mobile application (React Native)
- [ ] Voice control integration
- [ ] Advanced audio effects
- [ ] Multi-room synchronization
- [ ] Cloud backup integration

### 🚀 Planned Features
- [ ] Spotify/Apple Music integration
- [ ] Parental controls and time limits
- [ ] Sleep timer and bedtime routines
- [ ] Activity analytics and usage tracking
- [ ] Custom theme builder

## 🤝 Contributing

We welcome contributions! Please see our [Development Guide](development/contributing.md) for:
- Setting up the development environment
- Code style and commit conventions
- Testing requirements
- Pull request process

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

## 🆘 Support

- **Documentation Issues**: [GitHub Issues](https://github.com/theopenmusicbox/tomb-rpi/issues)
- **Community Discussions**: [GitHub Discussions](https://github.com/theopenmusicbox/tomb-rpi/discussions)
- **Email Support**: support@theopenmusicbox.com

---

*Last updated: September 2025 • The Open Music Box v2.0*